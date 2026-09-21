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


CIO_AI_VERSION = "2.3.5"
CIO_AI_BUILD = "2.3.5-INTEGRATION-TO-CONCLUSION"
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
- Não crie compra, venda, entrada, saída, espera, rebalanceamento, aumento ou redução de exposição.
- Não crie plano de ação.
- Não formule aconselhamento, orientação, recomendação de monitoramento ou linguagem normativa; descreva apenas o estado observado.
- Não use governança para determinar a conclusão de cenário.
- Não acrescente relações que não estejam no contrato.
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
        "contract_version": "2.3.5",
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
        return {"RISK": _clone(layers.get("RISK", []))}
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
            "Descreva a condição de risco da carteira representada pela camada RISK. "
            "Risco não é ordem operacional."
        ),
        "micro_us": (
            "Produza uma leitura conjunta da camada MICRO_US. Os sistemas não são votos. "
            "Compare diretamente apenas dimensões realmente comuns. "
            "Ao falar em alinhamento, convergência ou confirmação de sinal entre sistemas, "
            "use EXCLUSIVAMENTE comparison_evidence.literal_signal_matches. "
            "Se o ticker estiver em literal_signal_divergences, descreva sinais diferentes, nunca alinhamento."
        ),
        "micro_br": (
            "Produza uma leitura conjunta da camada MICRO_BR. B3 e FII são classes diferentes; "
            "trate a relação como contexto regional quando não houver dimensão diretamente comparável."
        ),
        "cross_layer_integration": (
            "Integre as quatro camadas usando SOMENTE authorized_relations. "
            "Explique coexistências, tensões, heterogeneidade ou seletividade sustentadas pelos fatos. "
            "Não transforme a integração em recomendação."
        ),
        "integrated_cio_conclusion": (
            "Responda diretamente à pergunta de conclusion_contract em nível de síntese executiva. "
            "Use como BASE ANALÍTICA a seção cross_layer_integration já produzida e grounded nas quatro camadas. "
            "Extraia dela a característica dominante do cenário conjunto e as tensões que qualificam essa leitura. "
            "NÃO reenumere robôs, tickers, rankings, scores, pesos, contagens ou listas de sinais. "
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
- Não crie compra, venda, entrada, saída, espera, rebalanceamento ou plano de ação.
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
                temperature=1.0,
                top_p=0.95,
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
    V2.3.5:
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
        call_trace.append({"field": field, "status": "PASS"})

    # Depois: integração real das quatro camadas, apoiada pelas sínteses anteriores,
    # mas sempre com os payloads completos e authorized_relations disponíveis.
    integration_prior = {
        key: analysis[key]
        for key in ("scenario", "risk", "micro_us", "micro_br")
    }
    analysis["cross_layer_integration"] = _request_final_section(
        client,
        contract,
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
    "build_integration_contract",
    "build_ai_prompt",
    "validate_report_structure",
    "run_cio_ai",
    "analyze_cio_context",
]
