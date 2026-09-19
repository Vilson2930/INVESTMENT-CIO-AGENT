# ============================================================
# INVESTMENT CIO AGENT
# agents/decision_agent.py
# ============================================================
#
# DECISION AGENT V1
#
# Função:
# Transformar Synthesis Agent + Risk Agent em uma visão
# executiva consolidada para apoio à decisão.
#
# IMPORTANTE:
# - NÃO recalcula indicadores dos motores.
# - NÃO cria score de investimento.
# - NÃO altera sinais originais.
# - NÃO transforma seleção de ativos em voto macro.
# - NÃO transforma scanners em voto macro.
# - NÃO executa ordens.
# - NÃO substitui decisão humana.
#
# O Decision Agent organiza:
#
#   REGIME
#      +
#   RISCO GLOBAL
#      +
#   SELEÇÃO DE ATIVOS
#      +
#   OPORTUNIDADES
#      ↓
#   CONTEXTO EXECUTIVO CONSOLIDADO
#
# ============================================================

from datetime import datetime, timezone
from copy import deepcopy


DECISION_AGENT_VERSION = "1.0"


# ============================================================
# EXCEÇÕES
# ============================================================


class DecisionAgentError(Exception):
    """Erro geral do Decision Agent."""


class InvalidDecisionInputError(DecisionAgentError):
    """Entrada inválida para o Decision Agent."""


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================


def _safe_dict(value):
    if isinstance(value, dict):
        return value
    return {}


def _safe_list(value):
    if isinstance(value, list):
        return value
    return []


def _normalize_text(value):
    if value is None:
        return None

    return str(value).strip().upper()


def _unique(values):
    result = []

    for value in values:
        if value is None:
            continue

        if value not in result:
            result.append(value)

    return result


# ============================================================
# VALIDAÇÃO DAS ENTRADAS
# ============================================================


def _validate_inputs(synthesis, risk_assessment):

    if not isinstance(synthesis, dict):
        raise InvalidDecisionInputError(
            "Synthesis deve ser um dicionário."
        )

    if not isinstance(risk_assessment, dict):
        raise InvalidDecisionInputError(
            "Risk assessment deve ser um dicionário."
        )

    synthesis_required = (
        "synthesis_version",
        "status",
        "comparison",
        "risk",
        "policy",
    )

    missing_synthesis = [
        field
        for field in synthesis_required
        if field not in synthesis
    ]

    if missing_synthesis:
        raise InvalidDecisionInputError(
            "Synthesis incompleto. Campos ausentes: "
            + ", ".join(missing_synthesis)
        )

    risk_required = (
        "risk_agent_version",
        "status",
        "global_risk",
        "restrictions",
        "risk_opportunity_context",
        "policy",
    )

    missing_risk = [
        field
        for field in risk_required
        if field not in risk_assessment
    ]

    if missing_risk:
        raise InvalidDecisionInputError(
            "Risk assessment incompleto. Campos ausentes: "
            + ", ".join(missing_risk)
        )

    return True


# ============================================================
# CONTEXTO MACRO
# ============================================================


def _build_macro_context(synthesis):

    comparison = _safe_dict(
        synthesis.get("comparison")
    )

    return {
        "sp500_stance": comparison.get(
            "sp500_stance"
        ),

        "global_stance": comparison.get(
            "global_stance"
        ),

        "relationship": comparison.get(
            "relationship"
        ),
    }


# ============================================================
# CONTEXTO DE RISCO
# ============================================================


def _build_risk_context(risk_assessment):

    global_risk = deepcopy(
        _safe_dict(
            risk_assessment.get(
                "global_risk"
            )
        )
    )

    restrictions = deepcopy(
        _safe_list(
            risk_assessment.get(
                "restrictions"
            )
        )
    )

    opportunity_context = deepcopy(
        _safe_dict(
            risk_assessment.get(
                "risk_opportunity_context"
            )
        )
    )

    return {
        "global_risk": global_risk,
        "restrictions": restrictions,
        "risk_opportunity_context": (
            opportunity_context
        ),
    }


# ============================================================
# CAMADAS DOS SISTEMAS
# ============================================================


def _extract_layers(synthesis):

    layers = _safe_dict(
        synthesis.get("layers")
    )

    regime = deepcopy(
        _safe_list(
            layers.get("REGIME")
        )
    )

    global_risk = deepcopy(
        _safe_list(
            layers.get("GLOBAL_RISK")
        )
    )

    asset_selection = deepcopy(
        _safe_list(
            layers.get("ASSET_SELECTION")
        )
    )

    opportunity_scanners = deepcopy(
        _safe_list(
            layers.get(
                "OPPORTUNITY_SCANNER"
            )
        )
    )

    return {
        "regime": regime,
        "global_risk": global_risk,
        "asset_selection": asset_selection,
        "opportunity_scanners": (
            opportunity_scanners
        ),
    }


# ============================================================
# SINAIS PRESERVADOS
# ============================================================


def _extract_source_signals(
    risk_assessment,
):

    source_signals = deepcopy(
        _safe_list(
            risk_assessment.get(
                "source_signals"
            )
        )
    )

    return source_signals


# ============================================================
# CLASSIFICAÇÃO OPERACIONAL DO CONTEXTO
# ============================================================


def _has_restriction(
    risk_assessment,
    code,
):

    codes = _safe_list(
        risk_assessment.get(
            "restriction_codes"
        )
    )

    return code in codes


def _derive_operational_context(
    synthesis,
    risk_assessment,
):

    """
    Esta classificação NÃO substitui os motores.

    Ela descreve somente o estado de governança
    resultante da combinação entre regime e risco.
    """

    kill_switch = _has_restriction(
        risk_assessment,
        "GLOBAL_KILL_SWITCH_ACTIVE",
    )

    critical_risk = _has_restriction(
        risk_assessment,
        "GLOBAL_RISK_CRITICAL",
    )

    defensive = _has_restriction(
        risk_assessment,
        "GLOBAL_DEFENSIVE_STANCE",
    )

    divergence = _has_restriction(
        risk_assessment,
        "MACRO_RISK_DIVERGENCE",
    )

    opportunity_context = _safe_dict(
        risk_assessment.get(
            "risk_opportunity_context"
        )
    )

    has_opportunity = (
        opportunity_context.get(
            "has_positive_entry_evidence"
        )
        is True
    )

    if kill_switch:

        state = "GLOBAL_RISK_RESTRICTION"

        governance = "HARD_RESTRICTION_PRESENT"

        explanation = (
            "Existe Survival Kill Switch global ativo. "
            "Sinais específicos de seleção e oportunidade "
            "continuam preservados, mas a restrição global "
            "de risco deve permanecer explicitamente "
            "visível na decisão humana."
        )

    elif critical_risk:

        state = "ELEVATED_GLOBAL_RISK"

        governance = "STRONG_RISK_CONSTRAINT"

        explanation = (
            "O sistema global reporta risco crítico. "
            "As oportunidades dos demais motores são "
            "preservadas sem substituir a restrição "
            "de risco registrada na origem."
        )

    elif defensive and divergence:

        state = "MACRO_RISK_CONFLICT"

        governance = "CONFLICT_REQUIRES_REVIEW"

        explanation = (
            "Existe divergência entre o contexto de "
            "regime e a postura global de risco. "
            "Nenhum dos sinais originais é alterado."
        )

    elif defensive:

        state = "DEFENSIVE_GLOBAL_CONTEXT"

        governance = "RISK_CONSTRAINT_PRESENT"

        explanation = (
            "A postura global permanece defensiva. "
            "Seleções e oportunidades específicas "
            "continuam disponíveis como evidência."
        )

    elif divergence:

        state = "DIVERGENT_CONTEXT"

        governance = "REVIEW_DIVERGENCE"

        explanation = (
            "Os motores macro e de risco apresentam "
            "divergência que deve permanecer visível."
        )

    elif has_opportunity:

        state = "OPPORTUNITIES_PRESENT"

        governance = "NO_GLOBAL_HARD_RESTRICTION"

        explanation = (
            "Existem sinais positivos de entrada "
            "produzidos pelos motores específicos e "
            "nenhuma restrição global dura foi "
            "identificada pelo Risk Agent."
        )

    else:

        state = "NEUTRAL_EXECUTIVE_CONTEXT"

        governance = "NO_GLOBAL_HARD_RESTRICTION"

        explanation = (
            "Não foi identificada restrição global "
            "dura nem evidência explícita de entrada "
            "nesta consolidação."
        )

    return {
        "state": state,
        "governance": governance,
        "has_positive_entry_evidence": (
            has_opportunity
        ),
        "explanation": explanation,
    }


# ============================================================
# CONFLITOS
# ============================================================


def _build_conflicts(
    synthesis,
    risk_assessment,
):

    conflicts = []

    comparison = _safe_dict(
        synthesis.get("comparison")
    )

    relationship = _normalize_text(
        comparison.get("relationship")
    )

    if relationship == "DIVERGENCE":

        conflicts.append({
            "code": "REGIME_GLOBAL_RISK_DIVERGENCE",

            "type": "MACRO_RISK",

            "message": (
                "O SP500 Cycle Atlas e o sistema "
                "global de risco apresentam "
                "posturas divergentes."
            ),

            "source_systems": [
                "SP500_CYCLE_ATLAS",
                "COPIAULTIMOROB",
            ],
        })

    risk_opportunity = _safe_dict(
        risk_assessment.get(
            "risk_opportunity_context"
        )
    )

    if (
        risk_opportunity.get(
            "has_global_restrictions"
        )
        is True
        and
        risk_opportunity.get(
            "has_positive_entry_evidence"
        )
        is True
    ):

        conflicts.append({
            "code": "OPPORTUNITY_VS_GLOBAL_RISK",

            "type": "RISK_OPPORTUNITY",

            "message": (
                "Existem sinais específicos de entrada "
                "simultaneamente a restrições globais "
                "de risco."
            ),

            "source_systems": [
                "RISK_AGENT",
                "ASSET_SELECTION",
                "OPPORTUNITY_SCANNERS",
            ],
        })

    return conflicts


# ============================================================
# ALERTAS EXECUTIVOS
# ============================================================


def _build_executive_alerts(
    synthesis,
    risk_assessment,
):

    alerts = []

    synthesis_risk = _safe_dict(
        synthesis.get("risk")
    )

    for alert in _safe_list(
        synthesis_risk.get("alerts")
    ):

        alerts.append({
            "source": "SYNTHESIS_AGENT",
            "message": alert,
        })

    for restriction in _safe_list(
        risk_assessment.get(
            "restrictions"
        )
    ):

        alerts.append({
            "source": restriction.get(
                "source"
            ),
            "code": restriction.get(
                "code"
            ),
            "severity": restriction.get(
                "severity"
            ),
            "message": restriction.get(
                "message"
            ),
        })

    unique_alerts = []
    seen = set()

    for alert in alerts:

        key = (
            alert.get("source"),
            alert.get("code"),
            alert.get("message"),
        )

        if key not in seen:
            seen.add(key)
            unique_alerts.append(alert)

    return unique_alerts


# ============================================================
# STATUS DO DECISION AGENT
# ============================================================


def _determine_status(
    synthesis,
    risk_assessment,
):

    synthesis_status = _normalize_text(
        synthesis.get("status")
    )

    risk_status = _normalize_text(
        risk_assessment.get("status")
    )

    if (
        synthesis_status == "ERROR"
        or risk_status == "ERROR"
    ):
        return "ERROR"

    if (
        synthesis_status == "DATA_INSUFFICIENT"
        or risk_status == "DATA_INSUFFICIENT"
    ):
        return "DATA_INSUFFICIENT"

    if (
        synthesis_status == "WARNING"
        or risk_status == "WARNING"
    ):
        return "WARNING"

    return "OK"


# ============================================================
# DECISION AGENT
# ============================================================


def build_decision(
    synthesis,
    risk_assessment,
):

    """
    Constrói a consolidação executiva do CIO.

    Não constitui execução automática nem substitui
    os sinais produzidos pelos motores.
    """

    _validate_inputs(
        synthesis,
        risk_assessment,
    )

    macro_context = (
        _build_macro_context(
            synthesis
        )
    )

    risk_context = (
        _build_risk_context(
            risk_assessment
        )
    )

    layers = _extract_layers(
        synthesis
    )

    source_signals = (
        _extract_source_signals(
            risk_assessment
        )
    )

    operational_context = (
        _derive_operational_context(
            synthesis,
            risk_assessment,
        )
    )

    conflicts = _build_conflicts(
        synthesis,
        risk_assessment,
    )

    alerts = _build_executive_alerts(
        synthesis,
        risk_assessment,
    )

    status = _determine_status(
        synthesis,
        risk_assessment,
    )

    return {

        "decision_agent_version": (
            DECISION_AGENT_VERSION
        ),

        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),

        "status": status,

        "source_versions": {
            "synthesis_agent": (
                synthesis.get(
                    "synthesis_version"
                )
            ),

            "risk_agent": (
                risk_assessment.get(
                    "risk_agent_version"
                )
            ),
        },

        "macro_context": (
            macro_context
        ),

        "risk_context": (
            risk_context
        ),

        "operational_context": (
            operational_context
        ),

        "conflicts": conflicts,

        "executive_alerts": alerts,

        "layers": layers,

        "source_signals": (
            source_signals
        ),

        "summary": {

            "operational_state": (
                operational_context.get(
                    "state"
                )
            ),

            "governance_state": (
                operational_context.get(
                    "governance"
                )
            ),

            "conflict_count": len(
                conflicts
            ),

            "alert_count": len(
                alerts
            ),

            "asset_selection_systems": len(
                layers.get(
                    "asset_selection",
                    []
                )
            ),

            "opportunity_scanners": len(
                layers.get(
                    "opportunity_scanners",
                    []
                )
            ),
        },

        "policy": {

            "source_signals_preserved": True,

            "source_order_preserved": True,

            "source_decisions_preserved": True,

            "source_risk_preserved": True,

            "indicators_recalculated": False,

            "source_risk_recalculated": False,

            "new_quantitative_score_created": False,

            "source_decisions_overridden": False,

            "selection_systems_used_as_macro_votes": False,

            "opportunity_systems_used_as_macro_votes": False,

            "automatic_trade_decision_created": False,

            "broker_execution_allowed": False,

            "human_decision_required": True,
        },
    }


# ============================================================
# INTERFACE GENÉRICA
# ============================================================


def run_decision_agent(
    synthesis,
    risk_assessment,
):

    return build_decision(
        synthesis,
        risk_assessment,
    )
