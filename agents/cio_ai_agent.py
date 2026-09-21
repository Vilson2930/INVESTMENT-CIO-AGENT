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


CIO_AI_VERSION = "2.0"
CIO_AI_BUILD = "2.0-FUNCTIONAL-INTEGRATION"
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
Você é o CIO Integration Engine, uma camada de inteligência que integra sete sistemas
quantitativos especialistas.

PRINCÍPIO CENTRAL
Os sete sistemas NÃO são sete votos equivalentes. Cada um responde a uma pergunta
diferente. Sua tarefa é integrar DIMENSÕES FUNCIONAIS, não buscar maioria ou consenso.

CAMADAS
1. SCENARIO — SP500_CYCLE_ATLAS: pano de fundo/regime de mercado.
2. RISK — COPIAULTIMOROB: condição de risco da carteira.
3. MICRO_US — Ações Americanas + AI Infrastructure + Growth: seleção e oportunidades.
4. MICRO_BR — B3 + FII: seleção e oportunidades no mercado brasileiro, respeitando
   que ações e FIIs são classes diferentes.

MÉTODO OBRIGATÓRIO
A) Leia primeiro SCENARIO.
B) Relacione SCENARIO com RISK sem afirmar que um causou o outro.
C) Analise MICRO_US e procure comparação direta somente quando existir dimensão comum
   comprovável, especialmente o mesmo ticker.
D) Analise MICRO_BR como contexto regional; não trate ações e FIIs como sinais equivalentes.
E) Relacione SCENARIO/RISK com MICRO_US/MICRO_BR por coexistência e contexto.
F) Produza uma inferência CIO sobre o PADRÃO CONJUNTO que emerge dessas camadas.
G) Somente depois apresente governança, separada da conclusão de cenário.

PERMITIDO
- inferir o significado conjunto de fatos preservados;
- caracterizar alinhamento, tensão, heterogeneidade, seletividade ou coexistência quando
  essas características decorrerem dos fatos apresentados;
- explicar que camadas diferentes apresentam leituras diferentes;
- comparar o mesmo ticker quando ele estiver explicitamente presente nos sistemas comparados.

PROIBIDO
- alterar sinal, ticker, score, ranking, indicador ou status de origem;
- recalcular indicadores;
- contar sistemas positivos/negativos como votação;
- transformar seleção micro em voto macro;
- transformar risco em ordem de reduzir exposição;
- transformar oportunidade em autorização para operar;
- inventar causa de um sinal;
- transformar coexistência em causalidade;
- afirmar que Kill Switch, Hard Block ou restrições causaram bloqueio operacional sem
  relação causal explicitamente fornecida;
- criar recomendação própria de compra, venda, entrada, saída ou rebalanceamento;
- criar novo score ou novo sinal CIO.

A CONCLUSÃO CIO deve responder:
"Considerando conjuntamente as quatro camadas funcionais formadas pelos sete sistemas,
qual é a leitura integrada do cenário de investimento?"

A conclusão deve ser uma interpretação do conjunto, e não uma enumeração dos sete robôs.
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


def build_ai_prompt(context: Dict[str, Any]) -> str:
    context_json = json.dumps(context, ensure_ascii=False, indent=2, default=str)
    sections = "\n".join(REPORT_SECTIONS)
    return f"""
Analise exclusivamente o contexto funcional abaixo.

=========================
CONTEXTO FUNCIONAL
=========================
{context_json}

=========================
TAREFA
=========================

Produza UM relatório CIO integrado.

Não resuma os sete robôs em sequência. Trabalhe por CAMADAS e use o relation_map para
saber quais relações são estruturalmente válidas.

Na seção 5, explique o padrão que emerge da combinação entre regime, risco e evidências
micro. Diferencie relação estrutural, contexto, coexistência e convergência comprovada.

Na seção 6, responda diretamente à pergunta central:
"Considerando conjuntamente as quatro camadas funcionais formadas pelos sete sistemas,
qual é a leitura integrada do cenário de investimento?"

A seção 6 deve conter uma conclusão analítica real, mas não pode criar recomendação,
novo sinal, novo score ou causalidade não fornecida.

A governança deve aparecer somente na seção 7. Não use governança para fabricar a
conclusão de cenário.

Use exatamente estas seções e nesta ordem:
{sections}
""".strip()


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
    try:
        content = completion.choices[0].message.content
    except Exception as exc:
        raise CIOAIResponseError("Formato inesperado de resposta da NVIDIA NIM.") from exc

    if not isinstance(content, str) or not content.strip():
        raise CIOAIResponseError("A NVIDIA NIM retornou resposta textual vazia ou inválida.")
    return content.strip()


def validate_report_structure(report: str) -> Dict[str, Any]:
    if not isinstance(report, str) or not report.strip():
        raise CIOAIStructuralValidationError("Relatório CIO vazio.")

    positions = []
    for section in REPORT_SECTIONS:
        pos = report.find(section)
        if pos < 0:
            raise CIOAIStructuralValidationError(f"Seção obrigatória ausente: {section}")
        positions.append(pos)

    if positions != sorted(positions):
        raise CIOAIStructuralValidationError("As seções do relatório estão fora da ordem exigida.")

    conclusion_start = positions[5] + len(REPORT_SECTIONS[5])
    conclusion_end = positions[6]
    conclusion = report[conclusion_start:conclusion_end].strip()
    if not conclusion:
        raise CIOAIStructuralValidationError("CONCLUSÃO CIO INTEGRADA vazia.")

    return {
        "status": "PASS",
        "sections_found": len(REPORT_SECTIONS),
        "integrated_conclusion_present": True,
    }


def _is_transient_503(exc: Exception) -> bool:
    text = str(exc).lower()
    return "503" in text or "service unavailable" in text or "temporarily unavailable" in text


def _request_nvidia_analysis(
    client: Any,
    prompt: str,
    model: str,
    max_503_retries: int = 2,
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
                temperature=0.15,
                top_p=0.9,
                max_tokens=5000,
            )
            return _extract_response_text(completion)
        except Exception as exc:
            last_exc = exc
            if not _is_transient_503(exc) or attempt >= max_503_retries:
                raise CIOAIResponseError(f"Falha na NVIDIA NIM: {exc}") from exc
            time.sleep(2 ** attempt)

    raise CIOAIResponseError(f"Falha na NVIDIA NIM: {last_exc}")


def run_cio_ai(
    raw_input: Dict[str, Any],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Executa a nova integração funcional dos sete sistemas."""
    selected_model = model or DEFAULT_MODEL
    context = build_functional_context(raw_input)
    prompt = build_ai_prompt(context)
    client = _build_nvidia_client(api_key=api_key)
    report = _request_nvidia_analysis(client, prompt, selected_model)
    structural_validation = validate_report_structure(report)

    return {
        "status": "OK",
        "cio_ai_version": CIO_AI_VERSION,
        "cio_ai_build": CIO_AI_BUILD,
        "architecture": "FUNCTIONAL_INTEGRATION",
        "model": selected_model,
        "generated_at": _utc_now(),
        "systems_count": len(OFFICIAL_SYSTEMS),
        "layers": _clone(context["layers"]),
        "relation_map": _clone(RELATION_MAP),
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
    "CIOAIError",
    "CIOAIConfigurationError",
    "CIOAIInputError",
    "CIOAIResponseError",
    "CIOAIStructuralValidationError",
    "normalize_system_outputs",
    "build_functional_context",
    "build_ai_prompt",
    "validate_report_structure",
    "run_cio_ai",
    "analyze_cio_context",
]
