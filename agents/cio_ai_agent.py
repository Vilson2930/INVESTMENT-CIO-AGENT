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


CIO_AI_VERSION = "2.1"
CIO_AI_BUILD = "2.1-CONTRACT-FIRST-INTEGRATION"
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
- Não use governança para determinar a conclusão de cenário.
- Não acrescente relações que não estejam no contrato.
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
        "contract_version": "2.1",
        "architecture": "CONTRACT_FIRST_FUNCTIONAL_INTEGRATION",
        "layers": {
            "SCENARIO": scenario,
            "RISK": risk,
            "MICRO_US": micro_us,
            "MICRO_BR": micro_br,
        },
        "authorized_relations": authorized_relations,
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
        "source_data": _clone(systems),
    }


def build_ai_prompt(context: Dict[str, Any]) -> str:
    """
    Compatibilidade pública: recebe o contexto funcional e o transforma no prompt.
    Para a execução V2.1, run_cio_ai usa diretamente build_integration_contract().
    """
    context_json = json.dumps(context, ensure_ascii=False, indent=2, default=str)
    sections = "\n".join(REPORT_SECTIONS)
    return f"""
Redija o relatório a partir do contrato abaixo.

CONTRATO
========
{context_json}

FORMATO OBRIGATÓRIO
===================
{sections}

A seção 5 deve explicar somente relações autorizadas pelo contrato.
A seção 6 deve responder à pergunta central de forma DESCRITIVA, não prescritiva.
A seção 7 deve apenas registrar governança e rastreabilidade.

Não produza recomendações nem plano de ação.
Entregue somente o relatório final.
""".strip()


def _build_contract_prompt(contract: Dict[str, Any]) -> str:
    contract_json = json.dumps(contract, ensure_ascii=False, indent=2, default=str)
    sections = "\n".join(REPORT_SECTIONS)
    return f"""
CONTRATO DE INTEGRAÇÃO CIO
==========================
{contract_json}

TAREFA
======
Transforme exclusivamente este contrato em um relatório analítico legível.

Use exatamente estas seções e nesta ordem:
{sections}

REGRAS DE SAÍDA
===============
- Não faça uma votação entre sistemas.
- Não acrescente fatos ausentes.
- Não acrescente relações além de authorized_relations.
- A seção 5 descreve o padrão conjunto observado.
- A seção 6 responde à conclusion_contract.question.
- A seção 6 é uma LEITURA DO CENÁRIO, não uma decisão de investimento.
- Não diga o que o investidor deve fazer.
- Não crie recomendação, plano de ação ou autorização operacional.
- A seção 7 apenas relata governance.
- Entregue somente o relatório final.
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
            raise CIOAIStructuralValidationError(
                f"Seção obrigatória ausente: {section}"
            )
        positions.append(pos)

    if positions != sorted(positions):
        raise CIOAIStructuralValidationError(
            "As seções do relatório estão fora da ordem exigida."
        )

    for index, section in enumerate(REPORT_SECTIONS):
        start = positions[index] + len(section)
        end = positions[index + 1] if index + 1 < len(positions) else len(report)
        if not report[start:end].strip():
            raise CIOAIStructuralValidationError(
                f"Seção obrigatória vazia: {section}"
            )

    return {
        "status": "PASS",
        "sections_found": len(REPORT_SECTIONS),
        "integrated_conclusion_present": True,
    }


def _build_structural_reconstruction_prompt(
    contract: Dict[str, Any],
    structural_error: Exception,
) -> str:
    """
    Única recuperação permitida: reconstrução por erro de FORMATO.
    Não cria regras semânticas por palavra/frase.
    """
    contract_json = json.dumps(contract, ensure_ascii=False, indent=2, default=str)
    sections = "\n".join(REPORT_SECTIONS)

    return f"""
A resposta anterior falhou somente no CONTRATO DE FORMATO:
{type(structural_error).__name__}: {structural_error}

Reconstrua o relatório do zero usando exclusivamente o mesmo contrato:

{contract_json}

Use exatamente estas sete seções, nesta ordem, todas com conteúdo:
{sections}

Não explique a correção.
Não crie recomendação, plano de ação, novo sinal, novo score ou causalidade.
Entregue somente o relatório completo.
""".strip()


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
                temperature=0.10,
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
    """
    V2.1:
    1) Python preserva e organiza os sete sistemas em contrato;
    2) NVIDIA redige a leitura do contrato;
    3) Python valida somente o contrato estrutural do relatório.
    """
    selected_model = model or DEFAULT_MODEL

    # Mantido para rastreabilidade/compatibilidade.
    context = build_functional_context(raw_input)

    # Esta é a fronteira principal da V2.1.
    contract = build_integration_contract(raw_input)
    prompt = _build_contract_prompt(contract)
    client = _build_nvidia_client(api_key=api_key)
    report = _request_nvidia_analysis(client, prompt, selected_model)

    structural_retry_used = False
    first_structural_rejection = None

    try:
        structural_validation = validate_report_structure(report)
    except CIOAIStructuralValidationError as exc:
        structural_retry_used = True
        first_structural_rejection = str(exc)

        report = _request_nvidia_analysis(
            client,
            _build_structural_reconstruction_prompt(contract, exc),
            selected_model,
        )
        structural_validation = validate_report_structure(report)

    structural_validation = {
        **structural_validation,
        "retry_used": structural_retry_used,
        "retry_count": 1 if structural_retry_used else 0,
        "max_structural_retries": 1,
        "first_rejection": first_structural_rejection,
    }

    return {
        "status": "OK",
        "cio_ai_version": CIO_AI_VERSION,
        "cio_ai_build": CIO_AI_BUILD,
        "architecture": "CONTRACT_FIRST_FUNCTIONAL_INTEGRATION",
        "model": selected_model,
        "generated_at": _utc_now(),
        "systems_count": len(OFFICIAL_SYSTEMS),
        "layers": _clone(context["layers"]),
        "relation_map": _clone(RELATION_MAP),
        "integration_contract": contract,
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
    "build_integration_contract",
    "build_ai_prompt",
    "validate_report_structure",
    "run_cio_ai",
    "analyze_cio_context",
]
