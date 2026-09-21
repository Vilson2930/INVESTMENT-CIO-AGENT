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


CIO_AI_VERSION = "2.2.1"
CIO_AI_BUILD = "2.2.1-COMPACT-STRUCTURED-INTEGRATION"
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
- Toda afirmação factual específica deve ser recuperável literalmente do payload de um dos sete sistemas.
- Ao citar ticker, contagem, status, decisão, ranking, score ou peso, confira o campo correspondente antes de redigir.
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
        "contract_version": "2.2.1",
        "architecture": "COMPACT_CONTRACT_FIRST_FUNCTIONAL_INTEGRATION",
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
    }


STRUCTURED_OUTPUT_FIELDS = (
    "scenario",
    "risk",
    "micro_us",
    "micro_br",
    "cross_layer_integration",
    "integrated_cio_conclusion",
    "governance",
)


def build_ai_prompt(context: Dict[str, Any]) -> str:
    """
    Compatibilidade pública.
    Na V2.2 a saída da NVIDIA é um objeto JSON analítico estruturado.
    """
    return _build_structured_prompt(context)


def _build_structured_prompt(contract: Dict[str, Any]) -> str:
    contract_json = json.dumps(contract, ensure_ascii=False, indent=2, default=str)
    schema_example = {
        "scenario": "texto factual do cenário/regime",
        "risk": "texto factual do risco da carteira",
        "micro_us": "texto integrado dos sistemas micro dos EUA",
        "micro_br": "texto integrado dos sistemas micro do Brasil",
        "cross_layer_integration": "integração entre as camadas usando apenas authorized_relations",
        "integrated_cio_conclusion": "uma única leitura CIO integrada e descritiva",
        "governance": "governança e rastreabilidade, separadas da conclusão",
    }
    schema_json = json.dumps(schema_example, ensure_ascii=False, indent=2)

    return f"""
CONTRATO DE INTEGRAÇÃO CIO
==========================
{contract_json}

TAREFA
======
Analise conjuntamente os sete sistemas conforme suas quatro camadas funcionais e
as relações explicitamente autorizadas no contrato.

Sua resposta NÃO é um rascunho, plano, raciocínio intermediário ou Markdown.
Retorne SOMENTE um objeto JSON válido, sem texto antes ou depois e sem bloco ```.

Use EXATAMENTE estas sete chaves:
{schema_json}

REGRAS
======
- Os sete sistemas não são votos equivalentes.
- Preserve os papéis SCENARIO, RISK, MICRO_US e MICRO_BR.
- Não acrescente fatos ausentes.
- Toda afirmação factual específica deve ser sustentada pelo payload correspondente.
- Antes de mencionar ticker, contagem, status, decisão, ranking, score ou peso, confira o campo de origem.
- Não misture opportunities/ranking com positions/carteira.
- Não acrescente relações além de authorized_relations.
- cross_layer_integration deve efetivamente relacionar as camadas; não apenas resumir cada sistema isoladamente.
- integrated_cio_conclusion deve responder diretamente à conclusion_contract.question e sintetizar as quatro camadas em UMA leitura.
- integrated_cio_conclusion é descritiva, não prescritiva.
- Não crie recomendação, plano de ação, compra, venda, rebalanceamento ou autorização operacional.
- governance deve permanecer separada da conclusão analítica.
- Cada valor deve ser uma string não vazia.
- scenario, risk, micro_us e micro_br: no máximo 90 palavras cada.
- cross_layer_integration: no máximo 120 palavras.
- integrated_cio_conclusion: no máximo 120 palavras.
- governance: no máximo 60 palavras.
- O conjunto dos sete valores deve ficar preferencialmente abaixo de 650 palavras.
- Priorize síntese integrada; não liste todos os detalhes disponíveis.
- Não exponha raciocínio interno, planejamento da resposta ou autocorreções.
""".strip()


def _extract_json_object(text: str) -> Dict[str, Any]:
    """Extrai somente o objeto JSON final; não interpreta conteúdo analítico."""
    if not isinstance(text, str) or not text.strip():
        raise CIOAIResponseError("A NVIDIA NIM retornou resposta vazia.")

    candidate = text.strip()

    # Tolerância apenas de transporte: remove cerca Markdown se o provedor a inserir.
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()
        if candidate.lower().startswith("json"):
            candidate = candidate[4:].lstrip()

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise CIOAIResponseError(
            f"Saída estruturada inválida: JSON não pôde ser interpretado ({exc})."
        ) from exc

    if not isinstance(parsed, dict):
        raise CIOAIResponseError("Saída estruturada inválida: a raiz deve ser um objeto JSON.")

    return parsed


def validate_structured_analysis(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Valida contrato de saída sem julgar palavras, tickers ou conclusões."""
    if not isinstance(analysis, dict):
        raise CIOAIResponseError("Análise estruturada deve ser um dicionário.")

    expected = list(STRUCTURED_OUTPUT_FIELDS)
    missing = [field for field in expected if field not in analysis]
    extra = [field for field in analysis if field not in STRUCTURED_OUTPUT_FIELDS]

    if missing:
        raise CIOAIResponseError(
            "Saída estruturada incompleta. Campos ausentes: " + ", ".join(missing)
        )
    if extra:
        raise CIOAIResponseError(
            "Saída estruturada contém campos não autorizados: " + ", ".join(extra)
        )

    empty = [
        field for field in expected
        if not isinstance(analysis.get(field), str) or not analysis[field].strip()
    ]
    if empty:
        raise CIOAIResponseError(
            "Saída estruturada contém campos vazios/inválidos: " + ", ".join(empty)
        )

    return {
        "status": "PASS",
        "fields_found": len(expected),
        "integrated_conclusion_present": bool(
            analysis["integrated_cio_conclusion"].strip()
        ),
        "validation_mode": "STRUCTURED_OUTPUT_CONTRACT",
    }


def _render_report(analysis: Dict[str, str]) -> str:
    """Python monta deterministicamente o relatório; a IA fornece apenas o conteúdo."""
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
    """
    Compatibilidade: na V2.2 o relatório é renderizado deterministicamente pelo Python.
    A validação verifica apenas que os sete títulos produzidos pelo próprio renderer existem.
    """
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
        "validation_mode": "PYTHON_RENDERED_REPORT",
    }


def _build_structured_retry_prompt(
    contract: Dict[str, Any],
    first_error: Exception,
) -> str:
    """
    Uma única recuperação de CONTRATO DE SAÍDA.
    Não adiciona regras semânticas específicas nem altera os fatos.
    """
    base = _build_structured_prompt(contract)
    return f"""
{base}

A tentativa anterior não respeitou o contrato técnico de saída:
{type(first_error).__name__}: {first_error}

Gere novamente SOMENTE o objeto JSON válido com as sete chaves exigidas.
Use no máximo 70 palavras em cada campo e no máximo 450 palavras no total.
Não explique o erro, não produza Markdown e não exponha raciocínio intermediário.
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
                max_tokens=3000,
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
    V2.2.1:
    1) Python preserva e organiza os sete sistemas em contrato;
    2) NVIDIA devolve sete campos analíticos estruturados;
    3) Python valida os campos e monta deterministicamente o relatório;
    4) ausência de conclusão integrada é erro, não WARN.
    """
    selected_model = model or DEFAULT_MODEL

    context = build_functional_context(raw_input)
    contract = build_integration_contract(raw_input)
    prompt = _build_structured_prompt(contract)
    client = _build_nvidia_client(api_key=api_key)

    raw_response = _request_nvidia_analysis(client, prompt, selected_model)

    retry_used = False
    first_rejection = None

    try:
        structured_analysis = _extract_json_object(raw_response)
        structured_validation = validate_structured_analysis(structured_analysis)
    except CIOAIResponseError as exc:
        retry_used = True
        first_rejection = str(exc)

        retry_response = _request_nvidia_analysis(
            client,
            _build_structured_retry_prompt(contract, exc),
            selected_model,
        )
        structured_analysis = _extract_json_object(retry_response)
        structured_validation = validate_structured_analysis(structured_analysis)

    # A conclusão integrada é parte obrigatória do contrato.
    if not structured_validation.get("integrated_conclusion_present"):
        raise CIOAIResponseError(
            "Saída inválida: integrated_cio_conclusion ausente ou vazia."
        )

    report = _render_report(structured_analysis)
    structural_validation = validate_report_structure(report)

    structured_validation = {
        **structured_validation,
        "retry_used": retry_used,
        "retry_count": 1 if retry_used else 0,
        "max_output_contract_retries": 1,
        "first_rejection": first_rejection,
    }

    return {
        "status": "OK",
        "cio_ai_version": CIO_AI_VERSION,
        "cio_ai_build": CIO_AI_BUILD,
        "architecture": "COMPACT_STRUCTURED_CONTRACT_FIRST_FUNCTIONAL_INTEGRATION",
        "model": selected_model,
        "generated_at": _utc_now(),
        "systems_count": len(OFFICIAL_SYSTEMS),
        "layers": _clone(context["layers"]),
        "relation_map": _clone(RELATION_MAP),
        "integration_contract": contract,
        "structured_analysis": _clone(structured_analysis),
        "structured_validation": structured_validation,
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
    "STRUCTURED_OUTPUT_FIELDS",
    "CIOAIError",
    "CIOAIConfigurationError",
    "CIOAIInputError",
    "CIOAIResponseError",
    "CIOAIStructuralValidationError",
    "normalize_system_outputs",
    "build_functional_context",
    "build_evidence_manifest",
    "build_integration_contract",
    "build_ai_prompt",
    "validate_structured_analysis",
    "validate_report_structure",
    "run_cio_ai",
    "analyze_cio_context",
]
