from __future__ import annotations

"""
CIO INTEGRATION ENGINE — proposta funcional limpa.

Objetivo:
- integrar sete sistemas especialistas sem tratá-los como sete votos equivalentes;
- preservar integralmente os fatos de origem;
- organizar a análise por função: REGIME, RISCO, MICRO EUA e MICRO BRASIL;
- permitir inferência analítica entre camadas, sem inventar fatos, causalidade ou recomendação;
- separar a conclusão de cenário dos estados de governança.

Este módulo NÃO recalcula indicadores, NÃO altera sinais, NÃO cria scores e NÃO executa ordens.
"""

import json
import os
import time
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


CIO_AI_VERSION = "2.4.5"
CIO_AI_BUILD = "2.4.5-DETERMINISTIC-ALLOCATION-REPORT"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = os.getenv("CIO_AI_MODEL", "nvidia/nemotron-3-super-120b-a12b")


# A função de cada sistema é definida por código, não descoberta pela IA.
OFFICIAL_SYSTEMS: Dict[str, Dict[str, str]] = {
    "sp500_cycle": {
        "name": "SP500_CYCLE_ATLAS",
        "role": "REGIME",
        "region": "GLOBAL_US",
        "layer": "SCENARIO",
    },
    "global_portfolio": {
        "name": "COPIAULTIMOROB",
        "role": "PORTFOLIO_RISK",
        "region": "GLOBAL",
        "layer": "RISK",
    },
    "us_equities": {
        "name": "portfolio-acoes-americana-teste",
        "role": "ASSET_SELECTION",
        "region": "US",
        "layer": "MICRO_US",
    },
    "ai_infrastructure": {
        "name": "AI_INFRASTRUCTURE_SCANNER",
        "role": "OPPORTUNITY_SCANNER",
        "region": "US_GLOBAL",
        "layer": "MICRO_US",
    },
    "growth": {
        "name": "GROWTH-OPPORTUNITY-ENGINE",
        "role": "OPPORTUNITY_SCANNER",
        "region": "US_GLOBAL",
        "layer": "MICRO_US",
    },
    "b3_equities": {
        "name": "Portfolio-B3-Operational",
        "role": "ASSET_SELECTION",
        "region": "BR",
        "layer": "MICRO_BR",
    },
    "fii": {
        "name": "FII-Scanner",
        "role": "ASSET_SELECTION",
        "region": "BR",
        "layer": "MICRO_BR",
    },
}


# Relações autorizadas pela arquitetura. Elas definem COMO comparar, não QUAL conclusão obter.
RELATION_MAP: Dict[str, Dict[str, Any]] = {
    "regime_x_risk": {
        "systems": ["sp500_cycle", "global_portfolio"],
        "type": "STRUCTURAL",
        "question": "Como o regime de mercado e a condição de risco da carteira coexistem?",
        "causality_allowed": False,
    },
    "us_micro": {
        "systems": ["us_equities", "ai_infrastructure", "growth"],
        "type": "COMPARABLE_WHEN_COMMON_DIMENSION_EXISTS",
        "question": "Que evidências micro aparecem nos sistemas de ações e oportunidades ligados aos EUA?",
        "causality_allowed": False,
    },
    "brazil_micro": {
        "systems": ["b3_equities", "fii"],
        "type": "REGIONAL_CONTEXT",
        "question": "Que evidências micro aparecem nas classes de ativos brasileiras?",
        "causality_allowed": False,
    },
    "scenario_x_micro": {
        "systems": [
            "sp500_cycle", "us_equities", "ai_infrastructure", "growth",
            "b3_equities", "fii",
        ],
        "type": "VERTICAL_CONTEXT",
        "question": "O que os sistemas micro mostram dentro do pano de fundo de mercado?",
        "causality_allowed": False,
    },
    "risk_x_micro": {
        "systems": [
            "global_portfolio", "us_equities", "ai_infrastructure", "growth",
            "b3_equities", "fii",
        ],
        "type": "COEXISTENCE",
        "question": "Como a condição de risco da carteira coexiste com sinais micro específicos?",
        "causality_allowed": False,
    },
}


class CIOAIError(RuntimeError):
    pass


class CIOAIConfigurationError(CIOAIError):
    pass


class CIOAIInputError(CIOAIError):
    pass


class CIOAIResponseError(CIOAIError):
    pass


class CIOAIStructuralValidationError(CIOAIResponseError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clone(value: Any) -> Any:
    return deepcopy(value)


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _contains_system_id(value: Any, system_id: str) -> bool:
    for node in _walk(value):
        if isinstance(node, dict) and node.get("system_id") == system_id:
            return True
    return False


def _find_system_payload(value: Any, system_id: str) -> Optional[Dict[str, Any]]:
    """Localiza o primeiro payload explicitamente identificado pelo system_id."""
    for node in _walk(value):
        if isinstance(node, dict) and node.get("system_id") == system_id:
            return _clone(node)
    return None


def normalize_system_outputs(raw_input: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Converte a entrada em um contrato simples {system_id: payload}.

    Aceita preferencialmente o novo contrato:
        {"systems": {"sp500_cycle": {...}, ...}}

    Durante a migração, também aceita:
        {"sp500_cycle": {...}, ...}
    ou um payload legado que contenha objetos com system_id.

    Não interpreta nem altera o conteúdo dos sistemas.
    """
    if not isinstance(raw_input, dict) or not raw_input:
        raise CIOAIInputError("A entrada do CIO Integration Engine deve ser um dicionário não vazio.")

    candidate = raw_input.get("systems")
    if isinstance(candidate, dict):
        source = candidate
    else:
        source = raw_input

    normalized: Dict[str, Dict[str, Any]] = {}
    for system_id in OFFICIAL_SYSTEMS:
        direct = source.get(system_id) if isinstance(source, dict) else None
        if isinstance(direct, dict):
            normalized[system_id] = _clone(direct)
            continue

        found = _find_system_payload(raw_input, system_id)
        if found is not None:
            normalized[system_id] = found

    missing = [system_id for system_id in OFFICIAL_SYSTEMS if system_id not in normalized]
    if missing:
        raise CIOAIInputError(
            "Entrada incompleta. Sistemas ausentes: " + ", ".join(missing)
        )

    return normalized


def build_functional_context(raw_input: Dict[str, Any]) -> Dict[str, Any]:
    """Monta o contexto funcional sem recalcular qualquer resultado dos robôs."""
    systems = normalize_system_outputs(raw_input)

    layers = {
        "SCENARIO": ["sp500_cycle"],
        "RISK": ["global_portfolio"],
        "MICRO_US": ["us_equities", "ai_infrastructure", "growth"],
        "MICRO_BR": ["b3_equities", "fii"],
    }

    return {
        "context_version": CIO_AI_VERSION,
        "generated_at": _utc_now(),
        "architecture": "FUNCTIONAL_INTEGRATION",
        "systems_catalog": _clone(OFFICIAL_SYSTEMS),
        "layers": _clone(layers),
        "relation_map": _clone(RELATION_MAP),
        "source_data": _clone(systems),
        "governance": _clone(_safe_dict(raw_input.get("governance"))),
        "rules": {
            "source_facts_are_immutable": True,
            "systems_are_not_equal_votes": True,
            "different_roles_must_not_be_forced_into_consensus": True,
            "same_ticker_comparison_requires_same_ticker": True,
            "coexistence_is_not_convergence": True,
            "coexistence_is_not_causality": True,
            "cross_layer_inference_is_allowed": True,
            "new_quantitative_signal_is_forbidden": True,
            "new_score_is_forbidden": True,
            "investment_recommendation_is_forbidden": True,
            "broker_execution_is_forbidden": True,
            "governance_is_reported_after_scenario_conclusion": True,
            "human_decision_required": True,
        },
    }


SYSTEM_PROMPT = """
Você é o redator analítico do CIO Integration Engine.

Você NÃO decide investimentos. Você recebe um CONTRATO DE INTEGRAÇÃO já construído
deterministicamente pelo Python a partir dos sete sistemas especialistas.

Sua função é somente:
1. explicar os fatos preservados;
2. explicar as relações explicitamente autorizadas pelo contrato;
3. redigir uma leitura integrada descritiva do cenário;
4. manter governança separada da conclusão analítica.

REGRAS INVIOLÁVEIS
- Não altere fatos de origem.
- Não crie sinal, score, ranking, ticker, indicador ou status.
- Não transforme sete sistemas em votação.
- Não invente causalidade.
- Não transforme risco em ordem de reduzir exposição.
- Não transforme oportunidade em autorização para operar.
- Não crie compra, venda, entrada, saída, espera, rebalanceamento, aumento ou redução de exposição. Decisões operacionais já publicadas por um sistema de origem podem ser relatadas literalmente, com atribuição explícita à fonte.
- Não crie plano de ação.
- Não formule aconselhamento, orientação, recomendação de monitoramento ou linguagem normativa; descreva apenas o estado observado.
- Não use governança para determinar a conclusão de cenário.
- Não acrescente relações que não estejam no contrato.
- Relações factuais computáveis — contagens, ticker/sinal, interseções, sobreposições,
  presença/ausência de ticker e convergência/divergência literal — pertencem ao Python.
- Você pode interpretar o SIGNIFICADO dessas relações, inclusive o significado analítico
  de sobreposição entre especialistas, mas não deve recontá-las, recalculá-las,
  negá-las ou formular uma nova versão factual delas.
- Toda afirmação factual específica deve ser recuperável literalmente do payload de um dos sete sistemas.
- Ao citar ticker, contagem, status, decisão, ranking, score ou peso, confira o campo correspondente antes de redigir.
- Alinhamento/convergência entre sistemas exige o mesmo ticker e o mesmo signal literal no comparison_evidence; sinais diferentes nunca são alinhamento.
- Não faça autocorreções especulativas no texto; se um fato não puder ser sustentado pelo contrato, omita-o.
""".strip()


REPORT_SECTIONS = (
    "1. CENÁRIO E REGIME",
    "2. RISCO DA CARTEIRA",
    "3. MICRO EUA",
    "4. MICRO BRASIL",
    "5. INTEGRAÇÃO ENTRE CAMADAS",
    "6. CONCLUSÃO CIO INTEGRADA",
    "7. GOVERNANÇA E RASTREABILIDADE",
)


def _system_fact(system_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Envelope determinístico: preserva o payload e acrescenta somente metadados fixos."""
    catalog = OFFICIAL_SYSTEMS[system_id]
    return {
        "system_id": system_id,
        "system_name": catalog["name"],
        "role": catalog["role"],
        "region": catalog["region"],
        "layer": catalog["layer"],
        "payload": _clone(payload),
    }


def build_evidence_manifest(raw_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Índice determinístico de evidências por sistema.

    Não resume, não recalcula e não interpreta. Apenas expõe, por system_id,
    os blocos universais que o redator deve usar como fonte factual.
    """
    systems = normalize_system_outputs(raw_input)
    manifest: Dict[str, Any] = {}
    for system_id, payload in systems.items():
        manifest[system_id] = {
            "system_id": system_id,
            "status": _clone(payload.get("status")),
            "decision": _clone(payload.get("decision")),
            "metrics": _clone(payload.get("metrics")),
            "risk": _clone(payload.get("risk")),
            "data_quality": _clone(payload.get("data_quality")),
            "positions": _clone(payload.get("positions")),
            "opportunities": _clone(payload.get("opportunities")),
            "audit": _clone(payload.get("audit")),
            "metadata": _clone(payload.get("metadata")),
        }
    return manifest



def _literal_ticker_signals(payload: Dict[str, Any]) -> Dict[str, list]:
    """
    Indexa SOMENTE pares literais ticker/signal existentes nos blocos universais
    positions e opportunities. Não normaliza sinal, não cria equivalência e não recalcula nada.
    """
    out: Dict[str, list] = {}
    for block_name in ("positions", "opportunities"):
        rows = payload.get(block_name)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            ticker = row.get("ticker")
            signal = row.get("signal")
            if isinstance(ticker, str) and ticker.strip() and isinstance(signal, str) and signal.strip():
                t = ticker.strip().upper()
                pair = {"block": block_name, "signal": signal}
                if pair not in out.setdefault(t, []):
                    out[t].append(pair)
    return out


def build_comparison_evidence(systems: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evidência determinística para comparações entre sistemas.
    'literal_signal_matches' só existe quando o MESMO ticker aparece em pelo menos
    dois sistemas e o texto do signal é literalmente idêntico.
    Divergências também são preservadas, sem interpretação semântica.
    """
    by_system = {
        system_id: _literal_ticker_signals(payload)
        for system_id, payload in systems.items()
    }

    ticker_systems: Dict[str, Dict[str, list]] = {}
    for system_id, ticker_map in by_system.items():
        for ticker, observations in ticker_map.items():
            ticker_systems.setdefault(ticker, {})[system_id] = _clone(observations)

    common = {}
    literal_matches = {}
    divergences = {}

    for ticker, system_map in ticker_systems.items():
        if len(system_map) < 2:
            continue
        common[ticker] = _clone(system_map)

        signal_sets = {
            system_id: {obs["signal"] for obs in observations}
            for system_id, observations in system_map.items()
        }
        systems_list = list(signal_sets)
        shared = set(signal_sets[systems_list[0]])
        for system_id in systems_list[1:]:
            shared &= signal_sets[system_id]

        if shared:
            literal_matches[ticker] = {
                "systems": systems_list,
                "shared_literal_signals": sorted(shared),
            }
        else:
            divergences[ticker] = {
                system_id: sorted(signals)
                for system_id, signals in signal_sets.items()
            }

    system_ids = list(by_system)
    pairwise_overlaps: Dict[str, Any] = {}
    for i, left in enumerate(system_ids):
        left_tickers = set(by_system[left])
        for right in system_ids[i + 1:]:
            overlap = sorted(left_tickers & set(by_system[right]))
            pairwise_overlaps[f"{left}__x__{right}"] = {
                "systems": [left, right],
                "overlap_count": len(overlap),
                "overlap_tickers": overlap,
            }

    return {
        "rule": (
            "Alinhamento/convergência de sinal só pode ser afirmado para tickers "
            "presentes em literal_signal_matches. Mesmo ticker com sinais diferentes "
            "é divergência, não alinhamento."
        ),
        "by_system": by_system,
        "common_tickers": common,
        "literal_signal_matches": literal_matches,
        "literal_signal_divergences": divergences,
        "pairwise_ticker_overlaps": pairwise_overlaps,
    }


def build_integration_contract(raw_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constrói em Python o contrato que limita o espaço de inferência da IA.

    Nenhum fato quantitativo é recalculado e nenhuma conclusão operacional é criada.
    """
    systems = normalize_system_outputs(raw_input)

    scenario = [_system_fact("sp500_cycle", systems["sp500_cycle"])]
    risk = [_system_fact("global_portfolio", systems["global_portfolio"])]
    micro_us = [
        _system_fact("us_equities", systems["us_equities"]),
        _system_fact("ai_infrastructure", systems["ai_infrastructure"]),
        _system_fact("growth", systems["growth"]),
    ]
    micro_br = [
        _system_fact("b3_equities", systems["b3_equities"]),
        _system_fact("fii", systems["fii"]),
    ]

    authorized_relations = []
    for relation_id, relation in RELATION_MAP.items():
        authorized_relations.append({
            "relation_id": relation_id,
            "systems": list(relation["systems"]),
            "type": relation["type"],
            "question": relation["question"],
            "causality_allowed": bool(relation["causality_allowed"]),
        })

    return {
        "contract_version": "2.4.5",
        "architecture": "PYTHON_ORCHESTRATED_INTEGRATION_TO_CONCLUSION",
        "layers": {
            "SCENARIO": scenario,
            "RISK": risk,
            "MICRO_US": micro_us,
            "MICRO_BR": micro_br,
        },
        "authorized_relations": authorized_relations,
        "comparison_evidence": build_comparison_evidence(systems),
        "conclusion_contract": {
            "question": (
                "Considerando conjuntamente as quatro camadas funcionais formadas "
                "pelos sete sistemas, qual é a leitura integrada do cenário de investimento?"
            ),
            "allowed": [
                "descrever o padrão conjunto sustentado pelos fatos",
                "descrever coexistência, tensão, heterogeneidade ou seletividade quando sustentadas",
                "comparar diretamente somente dimensões realmente comuns",
            ],
            "forbidden": [
                "criar recomendação",
                "criar plano de ação",
                "criar novo sinal",
                "criar novo score",
                "inventar causalidade",
                "transformar risco em ordem operacional",
                "transformar oportunidade em autorização para operar",
            ],
        },
        "governance": _clone(_safe_dict(raw_input.get("governance"))),
    }


ANALYTICAL_SECTION_FIELDS = (
    "scenario",
    "risk",
    "micro_us",
    "micro_br",
    "cross_layer_integration",
    "integrated_cio_conclusion",
    "governance",
)


def _compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)





def build_deterministic_risk_diagnosis(contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expõe deterministicamente os fatos que sustentam o estado atual da camada RISK.

    Não inventa causalidade e não recalcula risco. Apenas separa os campos já
    publicados pelo sistema global_portfolio para impedir que o LLM trate
    "risco integrado CRÍTICO" como sinônimo de "BTC alto" ou de qualquer
    componente isolado.
    """
    layers = _safe_dict(contract.get("layers"))
    risk_items = layers.get("RISK", [])
    if not isinstance(risk_items, list) or not risk_items:
        return {}

    envelope = risk_items[0] if isinstance(risk_items[0], dict) else {}
    payload = _safe_dict(envelope.get("payload"))
    metrics = _safe_dict(payload.get("metrics"))
    risk = _safe_dict(payload.get("risk"))
    decision = _safe_dict(payload.get("decision"))

    # Adapter COPIAULTIMOROB V1.6 publica em positions as decisões literais
    # do Allocation Advisor. O CIO apenas as preserva; não recalcula nem
    # transforma essas decisões em recomendação própria.
    allocation_positions = []
    raw_positions = payload.get("positions")
    if isinstance(raw_positions, list):
        for row in raw_positions:
            if not isinstance(row, dict):
                continue
            allocation_positions.append({
                "ticker": _clone(row.get("ticker")),
                "current_weight_pct": _clone(row.get("current_weight_pct")),
                "target_weight_pct": _clone(row.get("target_weight_pct")),
                "drift_pct": _clone(row.get("drift_pct")),
                "model_action": _clone(row.get("model_action")),
                "model_priority": _clone(row.get("model_priority")),
                "source_data": _clone(row.get("source_data")),
            })

    keys = (
        "portfolio_total_value",
        "survival_status",
        "ruin_risk",
        "survival_kill_switch",
        "kill_switch",
        "runway_months",
        "survival_score",
        "kill_reasons",
        "required_evidence",
        "critical_flags",
        "stress_level",
        "forced_selling",
        "risk_budget_level",
        "risk_budget_score",
        "top_risk_asset",
        "max_risk_contribution_pct",
        "liquidity_level",
        "liquidity_score",
        "counterparty_level",
        "counterparty_score",
        "integrated_risk_level",
        "committee_action",
        "final_verdict",
    )

    observed = {}
    for key in keys:
        if key in metrics and metrics[key] is not None:
            observed[key] = _clone(metrics[key])
        elif key in risk and risk[key] is not None:
            observed[key] = _clone(risk[key])
        elif key in decision and decision[key] is not None:
            observed[key] = _clone(decision[key])

    # Fallback estrutural para o adapter COPIAULTIMOROB V1.5.
    # Apenas copia evidências já publicadas; não cria causalidade.
    survival_detail = _safe_dict(risk.get("survival"))
    integrated_detail = _safe_dict(risk.get("integrated"))

    nested_aliases = {
        "survival_status": survival_detail.get("status"),
        "survival_score": survival_detail.get("score"),
        "ruin_risk": survival_detail.get("ruin_risk"),
        "survival_kill_switch": survival_detail.get("kill_switch"),
        "runway_months": survival_detail.get("runway_months"),
        "kill_reasons": survival_detail.get("kill_reasons"),
        "required_evidence": survival_detail.get("required_evidence"),
        "integrated_risk_level": integrated_detail.get("level"),
        "critical_flags": integrated_detail.get("critical_flags"),
        "committee_action": integrated_detail.get("committee_action"),
        "final_verdict": integrated_detail.get("final_verdict"),
    }

    for key, value in nested_aliases.items():
        if key not in observed and value is not None:
            observed[key] = _clone(value)

    return {
        "system_id": envelope.get("system_id", "global_portfolio"),
        "rule": (
            "Cada campo abaixo é um fato independente publicado pela camada RISK. "
            "O estado integrado não deve ser atribuído a BTC, liquidez, orçamento "
            "de risco ou qualquer outro componente isolado sem relação causal "
            "explicitamente fornecida pela fonte."
        ),
        "observed_risk_facts": observed,
        "allocation_advisor_positions": allocation_positions,
        "allocation_rule": (
            "As posições acima são decisões literais do Allocation Advisor do COPIAULTIMOROB. "
            "Devem ser atribuídas ao sistema de origem e não podem ser apresentadas como "
            "recomendação criada pelo CIO."
        ),
    }



def render_deterministic_allocation_advisor(contract: Dict[str, Any]) -> str:
    """
    Renderiza literalmente as posições publicadas pelo Allocation Advisor do
    COPIAULTIMOROB. Não recalcula pesos, desvios, ações ou prioridades.
    """
    diagnosis = build_deterministic_risk_diagnosis(contract)
    positions = diagnosis.get("allocation_advisor_positions", [])
    if not isinstance(positions, list) or not positions:
        return ""

    def _fmt(value: Any) -> str:
        if value is None:
            return "N/D"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return f"{value:.2f}".replace(".", ",")
        return str(value)

    lines = ["ALOCAÇÃO DETERMINÍSTICA — COPIAULTIMOROB / ALLOCATION ADVISOR"]
    for row in positions:
        if not isinstance(row, dict):
            continue
        ticker = row.get("ticker") or "N/D"
        current = _fmt(row.get("current_weight_pct"))
        target = _fmt(row.get("target_weight_pct"))
        drift = _fmt(row.get("drift_pct"))
        action = row.get("model_action") or "N/D"
        priority = row.get("model_priority") or "N/D"
        lines.append(
            f"- {ticker}: peso atual {current}% | peso-alvo {target}% | "
            f"desvio {drift}% | ação {action} | prioridade {priority}."
        )

    return "\n".join(lines) if len(lines) > 1 else ""



def build_deterministic_fact_layer(contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Camada factual computada exclusivamente pelo Python.

    O LLM não conta, não intersecta conjuntos, não associa ticker a signal
    e não reconstrói relações literais entre sistemas.
    """
    evidence = _safe_dict(contract.get("comparison_evidence"))
    layers = _safe_dict(contract.get("layers"))

    return {
        "systems_count": len(OFFICIAL_SYSTEMS),
        "layer_system_counts": {
            layer: len(items) if isinstance(items, list) else 0
            for layer, items in layers.items()
        },
        "literal_signal_match_count": len(
            _safe_dict(evidence.get("literal_signal_matches"))
        ),
        "literal_signal_divergence_count": len(
            _safe_dict(evidence.get("literal_signal_divergences"))
        ),
        "literal_signal_matches": _clone(
            _safe_dict(evidence.get("literal_signal_matches"))
        ),
        "literal_signal_divergences": _clone(
            _safe_dict(evidence.get("literal_signal_divergences"))
        ),
        "pairwise_ticker_overlaps": _clone(
            _safe_dict(evidence.get("pairwise_ticker_overlaps"))
        ),
        "comparison_rule": evidence.get("rule"),
    }


def render_deterministic_fact_layer(contract: Dict[str, Any]) -> str:
    facts = build_deterministic_fact_layer(contract)
    lines = [
        f"Sistemas oficiais: {facts['systems_count']}.",
        "Sistemas por camada: "
        + ", ".join(
            f"{layer}={count}"
            for layer, count in facts["layer_system_counts"].items()
        )
        + ".",
        f"Convergências literais de sinal: {facts['literal_signal_match_count']}.",
        f"Divergências literais de sinal: {facts['literal_signal_divergence_count']}.",
    ]

    matches = facts["literal_signal_matches"]
    for ticker in sorted(matches):
        item = matches[ticker]
        systems = ", ".join(item.get("systems", []))
        signals = " | ".join(item.get("shared_literal_signals", []))
        lines.append(f"- CONVERGÊNCIA {ticker}: {signals} [{systems}]")

    divergences = facts["literal_signal_divergences"]
    for ticker in sorted(divergences):
        system_map = divergences[ticker]
        parts = [
            f"{system_id}=" + " | ".join(signals)
            for system_id, signals in system_map.items()
        ]
        lines.append(f"- DIVERGÊNCIA {ticker}: " + "; ".join(parts))

    micro_us = {"us_equities", "ai_infrastructure", "growth"}
    micro_br = {"b3_equities", "fii"}
    for pair_key in sorted(facts["pairwise_ticker_overlaps"]):
        item = facts["pairwise_ticker_overlaps"][pair_key]
        systems = item.get("systems", [])
        if len(systems) != 2:
            continue
        pair = set(systems)
        if not (pair.issubset(micro_us) or pair.issubset(micro_br)):
            continue
        tickers = item.get("overlap_tickers", [])
        ticker_text = ", ".join(tickers) if tickers else "nenhuma"
        lines.append(
            f"- SOBREPOSIÇÃO {systems[0]} x {systems[1]}: "
            f"{item.get('overlap_count', 0)} ticker(s): {ticker_text}."
        )

    return "\n".join(lines)


def build_ai_synthesis_source(contract: Dict[str, Any], factual_sections: Dict[str, str]) -> Dict[str, Any]:
    """
    Fonte reduzida para a IA: fatos já consolidados + relações autorizadas.
    A IA recebe o significado factual pronto e executa somente síntese.
    """
    return {
        "deterministic_facts": build_deterministic_fact_layer(contract),
        "authorized_relations": _clone(contract.get("authorized_relations", [])),
        "conclusion_contract": _clone(_safe_dict(contract.get("conclusion_contract"))),
        "factual_sections": _clone(factual_sections),
    }


def _section_source(contract: Dict[str, Any], field: str) -> Dict[str, Any]:
    """
    Seleciona deterministicamente somente o contexto necessário para cada etapa.
    Não resume nem recalcula fatos.
    """
    layers = _safe_dict(contract.get("layers"))
    relations = contract.get("authorized_relations", [])
    conclusion_contract = _safe_dict(contract.get("conclusion_contract"))
    comparison_evidence = _safe_dict(contract.get("comparison_evidence"))
    governance = _safe_dict(contract.get("governance"))

    if field == "scenario":
        return {"SCENARIO": _clone(layers.get("SCENARIO", []))}
    if field == "risk":
        return {
            "RISK": _clone(layers.get("RISK", [])),
            "risk_diagnosis": build_deterministic_risk_diagnosis(contract),
        }
    if field == "micro_us":
        return {
            "MICRO_US": _clone(layers.get("MICRO_US", [])),
            "comparison_evidence": _clone(comparison_evidence),
        }
    if field == "micro_br":
        return {"MICRO_BR": _clone(layers.get("MICRO_BR", []))}
    if field == "cross_layer_integration":
        return {
            "SCENARIO": _clone(layers.get("SCENARIO", [])),
            "RISK": _clone(layers.get("RISK", [])),
            "MICRO_US": _clone(layers.get("MICRO_US", [])),
            "MICRO_BR": _clone(layers.get("MICRO_BR", [])),
            "authorized_relations": _clone(relations),
            "comparison_evidence": _clone(comparison_evidence),
        }
    if field == "integrated_cio_conclusion":
        return {
            "authorized_relations": _clone(relations),
            "conclusion_contract": _clone(conclusion_contract),
        }
    if field == "governance":
        return {"governance": _clone(governance)}
    raise CIOAIInputError(f"Campo analítico desconhecido: {field}")


def _build_section_prompt(
    contract: Dict[str, Any],
    field: str,
    prior_sections: Optional[Dict[str, str]] = None,
) -> str:
    """
    Cada chamada pede somente UMA peça textual.
    Integração e conclusão recebem conjuntamente as quatro camadas.
    """
    source = _section_source(contract, field)
    prior_sections = prior_sections or {}

    tasks = {
        "scenario": (
            "Descreva o cenário e o regime representados pela camada SCENARIO. "
            "Preserve literalmente os fatos relevantes e não faça recomendação."
        ),
        "risk": (
            "Diagnostique a condição atual da carteira usando a camada RISK e risk_diagnosis. "
            "Separe explicitamente o estado integrado dos componentes que o sustentam ou coexistem com ele. "
            "Se orçamento de risco, liquidez ou outro componente estiver aceitável enquanto Survival, Stress, "
            "risco de ruína, Kill Switch ou o risco integrado permanecerem críticos/reprovados, deixe essa "
            "distinção clara. NÃO atribua causalidade a BTC ou a qualquer componente isolado sem campo causal "
            "explícito na fonte. Quando kill_reasons, runway_months ou required_evidence estiverem presentes, "
            "use-os como explicação factual do estado de Survival, sem criar relação adicional. "
            "Não diga que a causa de Survival não está explicitada se esses campos a explicitarem. "
            "Para Stress, somente explique a causa se houver campo causal explícito na fonte; caso contrário, "
            "limite-se ao estado, score e forced selling observados. "
            "Quando allocation_advisor_positions trouxer ticker, peso atual, peso-alvo, desvio, model_action "
            "e model_priority, descreva esses fatos literalmente e atribua a decisão ao Allocation Advisor do "
            "COPIAULTIMOROB. Uma ação como REDUZIR já publicada pela fonte pode ser relatada, mas NÃO deve ser "
            "transformada em recomendação própria do CIO. Risco, por si só, não é ordem operacional."
        ),
        "micro_us": (
            "Produza uma leitura conjunta da camada MICRO_US. Os sistemas não são votos. "
            "Interprete somente o padrão agregado. NÃO escreva pares ticker/signal, NÃO conte, "
            "NÃO intersecte conjuntos e NÃO reconstrua listas ou relações factuais. "
            "NÃO afirme presença, ausência ou quantidade de sobreposição entre sistemas; "
            "a sobreposição factual será apresentada pelo Python. "
            "Você pode interpretar apenas o significado analítico de leituras distintas ou coincidentes "
            "entre especialistas do mercado americano. Esses fatos pertencem exclusivamente "
            "à camada determinística do Python."
        ),
        "micro_br": (
            "Produza uma leitura conjunta da camada MICRO_BR. B3 e FII são classes diferentes; "
            "trate a relação como contexto regional quando não houver dimensão diretamente comparável."
        ),
        "cross_layer_integration": (
            "Integre as quatro camadas usando SOMENTE authorized_relations e as sínteses factuais já fornecidas. "
            "NÃO calcule contagens, NÃO intersecte conjuntos, NÃO reconstrua ticker/signal e NÃO crie nova relação factual. "
            "NÃO faça afirmações próprias sobre presença/ausência ou quantidade de sobreposição de tickers. "
            "Se a camada factual mostrar sobreposição, convergência ou divergência, interprete somente o significado disso. "
            "Explique o significado conjunto dos fatos já consolidados: coexistências, tensões, heterogeneidade ou seletividade. "
            "Não transforme a integração em recomendação."
        ),
        "integrated_cio_conclusion": (
            "Responda diretamente à pergunta de conclusion_contract em nível de síntese executiva. "
            "Use como BASE ANALÍTICA a seção cross_layer_integration já produzida e grounded nas quatro camadas. "
            "Extraia dela a característica dominante do cenário conjunto e as tensões que qualificam essa leitura. "
            "NÃO reenumere robôs, tickers, rankings, scores, pesos, contagens ou listas de sinais. "
            "NÃO faça afirmações próprias sobre presença/ausência ou quantidade de sobreposição de tickers. "
            "NÃO reabra os payloads individuais nem reconstrua a análise das quatro camadas. "
            "Não force consenso e não crie recomendação. A conclusão deve ser descritiva, não prescritiva."
        ),
        "governance": (
            "Relate somente a governança fornecida. Não use governança para modificar a conclusão analítica."
        ),
    }

    limits = {
        "scenario": 120,
        "risk": 120,
        "micro_us": 140,
        "micro_br": 140,
        "cross_layer_integration": 180,
        "integrated_cio_conclusion": 110,
        "governance": 80,
    }

    # Resumos já produzidos servem apenas como apoio de coerência nas etapas integrativas.
    prior_block = ""
    if field == "cross_layer_integration" and prior_sections:
        prior_block = (
            "\n\nSÍNTESES ANTERIORES PARA COERÊNCIA\n"
            + _compact_json(prior_sections)
        )
    elif field == "integrated_cio_conclusion" and prior_sections:
        integration_text = prior_sections.get("cross_layer_integration", "")
        prior_block = (
            "\n\nBASE ANALÍTICA JÁ INTEGRADA\n"
            + _compact_json({"cross_layer_integration": integration_text})
        )

    conclusion_rules = ""
    if field == "integrated_cio_conclusion":
        conclusion_rules = (
            "\n- Esta seção é uma SÍNTESE de nível superior, não uma repetição da seção de integração."
            "\n- Priorize a característica dominante do conjunto e as tensões que qualificam essa leitura."
            "\n- Não faça inventário de tickers, sinais, contagens ou resultados individuais já descritos nas seções anteriores."
            "\n- A seção 5 é a evidência analítica imediata desta conclusão; sintetize-a, não a reproduza."
            "\n- Não transforme ausência de convergência micro em conclusão de ausência de cenário."
        )

    return f"""
TAREFA ÚNICA
============
{tasks[field]}

FONTE AUTORIZADA
================
{_compact_json(source)}
{prior_block}

REGRAS
======
- Retorne SOMENTE o parágrafo final pronto para publicação, sem título, JSON, Markdown, prefácio, notas, análise do pedido ou raciocínio intermediário.\n- Comece diretamente pela afirmação analítica; não use frases como "preciso", "devemos", "vou", "a tarefa", "o usuário pediu", "analisando" ou equivalentes metadiscursivos.\n- Termine o parágrafo de forma completa; não deixe frase, enumeração ou raciocínio em aberto.
- Não altere fatos de origem.
- Não crie ticker, sinal, score, ranking, indicador ou status.
- Não invente causalidade.
- Não transforme risco em ordem de reduzir exposição.
- Não transforme oportunidade em autorização para operar.
- Não crie compra, venda, entrada, saída, espera, rebalanceamento ou plano de ação. Decisões operacionais já presentes na FONTE AUTORIZADA podem ser relatadas literalmente e atribuídas ao sistema de origem.
- Não formule recomendação, orientação, aconselhamento, necessidade de monitoramento ou linguagem normativa; descreva somente o estado observado.
- Toda afirmação factual específica deve ser sustentada pela FONTE AUTORIZADA.{conclusion_rules}
- Máximo de {limits[field]} palavras.
""".strip()


def build_ai_prompt(context: Dict[str, Any]) -> str:
    """
    Compatibilidade pública.
    Retorna o prompt da conclusão integrada, que é a pergunta central da V2.3.
    """
    return _build_section_prompt(context, "integrated_cio_conclusion")


def _clean_section_text(text: str, field: str) -> str:
    """
    Valida somente o contrato técnico mínimo da peça textual.
    Não tenta interpretar nem corrigir semanticamente a resposta.
    """
    if not isinstance(text, str) or not text.strip():
        raise CIOAIResponseError(f"Resposta vazia na etapa {field}.")

    cleaned = text.strip()

    # Não aceitamos serialização/rascunho como peça final.
    lowered = cleaned.lstrip().lower()
    if lowered.startswith("```") or lowered.startswith("{") or lowered.startswith("["):
        raise CIOAIResponseError(
            f"Formato inválido na etapa {field}: era esperado texto analítico final."
        )

    # Sinal técnico simples de truncamento: a resposta final deve terminar como prosa completa.
    if cleaned[-1] not in ".!?)]}":
        raise CIOAIResponseError(
            f"Resposta possivelmente truncada na etapa {field}: término incompleto."
        )

    return cleaned


def _render_report(analysis: Dict[str, str]) -> str:
    mapping = (
        ("1. CENÁRIO E REGIME", "scenario"),
        ("2. RISCO DA CARTEIRA", "risk"),
        ("3. MICRO EUA", "micro_us"),
        ("4. MICRO BRASIL", "micro_br"),
        ("5. INTEGRAÇÃO ENTRE CAMADAS", "cross_layer_integration"),
        ("6. CONCLUSÃO CIO INTEGRADA", "integrated_cio_conclusion"),
        ("7. GOVERNANÇA E RASTREABILIDADE", "governance"),
    )
    return "\n\n".join(
        f"{title}\n{analysis[field].strip()}"
        for title, field in mapping
    )


def validate_report_structure(report: str) -> Dict[str, Any]:
    """O Python controla os sete títulos; a NVIDIA fornece apenas o conteúdo."""
    if not isinstance(report, str) or not report.strip():
        raise CIOAIStructuralValidationError("Relatório CIO vazio.")

    positions = []
    for title in REPORT_SECTIONS:
        pos = report.find(title)
        if pos < 0:
            raise CIOAIStructuralValidationError(f"Seção ausente: {title}")
        positions.append(pos)

    if positions != sorted(positions):
        raise CIOAIStructuralValidationError("Seções fora da ordem determinística.")

    return {
        "status": "PASS",
        "sections_found": 7,
        "integrated_conclusion_present": True,
        "validation_mode": "PYTHON_ORCHESTRATED_SECTIONS",
    }


def _build_nvidia_client(api_key: Optional[str] = None):
    if OpenAI is None:
        raise CIOAIConfigurationError(
            "Pacote 'openai' não instalado. Adicione 'openai' ao requirements.txt."
        )

    key = api_key or os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_API_KEY_CIO")
    if not key:
        raise CIOAIConfigurationError(
            "Chave NVIDIA não configurada. Configure NVIDIA_API_KEY nos GitHub Secrets."
        )

    return OpenAI(base_url=NVIDIA_BASE_URL, api_key=key)


def _extract_response_text(completion: Any) -> str:
    """
    Extrai somente a resposta final destinada ao usuário.
    Campos de reasoning, quando presentes no provider, nunca entram no relatório.
    """
    try:
        message = completion.choices[0].message
        content = message.content
    except Exception as exc:
        raise CIOAIResponseError("Formato inesperado de resposta da NVIDIA NIM.") from exc

    if not isinstance(content, str) or not content.strip():
        raise CIOAIResponseError("A NVIDIA NIM retornou resposta final vazia ou inválida.")

    return content.strip()


def _is_transient_503(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        "503" in text
        or "service unavailable" in text
        or "temporarily unavailable" in text
    )


def _request_nvidia_analysis(
    client: Any,
    prompt: str,
    model: str,
    max_503_retries: int = 2,
    max_tokens: int = 900,
) -> str:
    last_exc: Optional[Exception] = None

    for attempt in range(max_503_retries + 1):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                top_p=1.0,
                max_tokens=max_tokens,
                extra_body={
                    "chat_template_kwargs": {
                        "enable_thinking": False
                    }
                },
            )
            return _extract_response_text(completion)
        except Exception as exc:
            last_exc = exc
            if not _is_transient_503(exc) or attempt >= max_503_retries:
                raise CIOAIResponseError(f"Falha na NVIDIA NIM: {exc}") from exc
            time.sleep(2 ** attempt)

    raise CIOAIResponseError(f"Falha na NVIDIA NIM: {last_exc}")



def _request_final_section(
    client: Any,
    contract: Dict[str, Any],
    field: str,
    model: str,
    prior_sections: Optional[Dict[str, str]] = None,
) -> str:
    """
    Solicita uma peça final curta. Uma segunda tentativa é permitida somente
    quando a resposta não satisfaz o contrato técnico de apresentação.
    """
    prompt = _build_section_prompt(contract, field, prior_sections=prior_sections)
    raw = _request_nvidia_analysis(client, prompt, model, max_tokens=900)

    try:
        return _clean_section_text(raw, field)
    except CIOAIResponseError as first_error:
        retry_prompt = (
            prompt
            + "\n\nCORREÇÃO DE APRESENTAÇÃO\n"
            + "A resposta anterior não era um parágrafo final publicável. "
              "Reescreva do zero e entregue somente o parágrafo final completo. "
              "Não descreva seu raciocínio nem a tarefa. "
            + f"Erro técnico: {first_error}"
        )
        retry_raw = _request_nvidia_analysis(
            client, retry_prompt, model, max_tokens=900
        )
        return _clean_section_text(retry_raw, field)


def run_cio_ai(
    raw_input: Dict[str, Any],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    V2.4.0:
    1) Python preserva os sete sistemas e as quatro camadas;
    2) Python orquestra sete peças analíticas curtas, sem JSON de saída;
    3) a integração recebe as quatro camadas completas;
    4) a conclusão recebe a integração já grounded, sem reabrir payloads brutos;
    5) Python monta deterministicamente um único relatório CIO.
    """
    selected_model = model or DEFAULT_MODEL
    context = build_functional_context(raw_input)
    contract = build_integration_contract(raw_input)
    client = _build_nvidia_client(api_key=api_key)

    analysis: Dict[str, str] = {}
    call_trace = []

    # Primeiro: leituras funcionais locais.
    for field in ("scenario", "risk", "micro_us", "micro_br"):
        analysis[field] = _request_final_section(
            client, contract, field, selected_model
        )
        if field == "risk":
            allocation_text = render_deterministic_allocation_advisor(contract)
            if allocation_text:
                analysis[field] = (
                    analysis[field].rstrip()
                    + "\n\n"
                    + allocation_text
                )
        call_trace.append({"field": field, "status": "PASS"})

    # Camada factual determinística: números, relações, ticker/signal e interseções.
    deterministic_facts_text = render_deterministic_fact_layer(contract)
    analysis["micro_us"] = (
        analysis["micro_us"].rstrip()
        + "\n\nFATOS DETERMINÍSTICOS — FONTE DE VERDADE\n"
        + deterministic_facts_text
    )

    # Depois: integração real das quatro camadas, apoiada pelas sínteses anteriores,
    # mas sempre com os payloads completos e authorized_relations disponíveis.
    integration_prior = {
        key: analysis[key]
        for key in ("scenario", "risk", "micro_us", "micro_br")
    }
    # O diagnóstico factual de risco acompanha a integração para que a síntese
    # preserve a distinção entre risco integrado e seus componentes.
    integration_prior["risk_diagnosis"] = build_deterministic_risk_diagnosis(contract)
    synthesis_source = build_ai_synthesis_source(contract, integration_prior)
    synthesis_contract = _clone(contract)
    synthesis_contract["layers"] = {}
    synthesis_contract["comparison_evidence"] = synthesis_source["deterministic_facts"]
    analysis["cross_layer_integration"] = _request_final_section(
        client,
        synthesis_contract,
        "cross_layer_integration",
        selected_model,
        prior_sections=integration_prior,
    )
    call_trace.append({"field": "cross_layer_integration", "status": "PASS"})

    # A conclusão é uma chamada própria de nível superior.
    # Recebe a integração já grounded da seção 5 + contrato/relações, sem reabrir payloads brutos.
    conclusion_prior = {
        "cross_layer_integration": analysis["cross_layer_integration"],
    }
    analysis["integrated_cio_conclusion"] = _request_final_section(
        client,
        contract,
        "integrated_cio_conclusion",
        selected_model,
        prior_sections=conclusion_prior,
    )
    call_trace.append({"field": "integrated_cio_conclusion", "status": "PASS"})

    # Governança fica deliberadamente depois da conclusão.
    analysis["governance"] = _request_final_section(
        client, contract, "governance", selected_model
    )
    call_trace.append({"field": "governance", "status": "PASS"})

    if not analysis["integrated_cio_conclusion"].strip():
        raise CIOAIResponseError("Conclusão CIO integrada ausente ou vazia.")

    report = _render_report(analysis)
    structural_validation = validate_report_structure(report)

    return {
        "status": "OK",
        "cio_ai_version": CIO_AI_VERSION,
        "cio_ai_build": CIO_AI_BUILD,
        "architecture": "PYTHON_ORCHESTRATED_INTEGRATION_TO_CONCLUSION",
        "model": selected_model,
        "generated_at": _utc_now(),
        "systems_count": len(OFFICIAL_SYSTEMS),
        "layers": _clone(context["layers"]),
        "relation_map": _clone(RELATION_MAP),
        "integration_contract": contract,
        "analytical_sections": _clone(analysis),
        "analytical_call_trace": call_trace,
        "structural_validation": structural_validation,
        "source_data_changed": False,
        "fact_grounding": {
            "strategy": "DETERMINISTIC_FACTS_AI_SYNTHESIS",
            "systems_count": "DETERMINISTIC_PYTHON",
            "ticker_signal_relations": "DETERMINISTIC_PYTHON",
            "counts": "DETERMINISTIC_PYTHON",
            "set_intersections": "DETERMINISTIC_PYTHON",
            "pairwise_ticker_overlaps": "DETERMINISTIC_PYTHON",
            "llm_role": "INTERPRETATION_AND_SYNTHESIS_ONLY",
            "llm_may_restate_computable_relations": False,
            "overlap_interpretation_allowed": True,
            "overlap_fact_assertion_owner": "DETERMINISTIC_PYTHON",
            "sampling_temperature": 0.0,
            "sampling_top_p": 1.0,
        },
        "report": report,
    }


def analyze_cio_context(
    raw_input: Dict[str, Any],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    return run_cio_ai(raw_input=raw_input, api_key=api_key, model=model)


__all__ = [
    "CIO_AI_VERSION",
    "CIO_AI_BUILD",
    "OFFICIAL_SYSTEMS",
    "RELATION_MAP",
    "SYSTEM_PROMPT",
    "REPORT_SECTIONS",
    "ANALYTICAL_SECTION_FIELDS",
    "CIOAIError",
    "CIOAIConfigurationError",
    "CIOAIInputError",
    "CIOAIResponseError",
    "CIOAIStructuralValidationError",
    "normalize_system_outputs",
    "build_functional_context",
    "build_evidence_manifest",
    "build_comparison_evidence",
    "build_deterministic_risk_diagnosis",
    "render_deterministic_allocation_advisor",
    "build_integration_contract",
    "build_ai_prompt",
    "validate_report_structure",
    "run_cio_ai",
    "analyze_cio_context",
]
