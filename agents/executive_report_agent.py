# ============================================================
# INVESTMENT CIO AGENT
# agents/executive_report_agent.py
# ============================================================
#
# EXECUTIVE REPORT AGENT V1
#
# Responsabilidade:
# Transformar a saída validada do Decision Agent em uma
# estrutura executiva única, rastreável e legível.
#
# Esta camada NÃO:
# - recalcula indicadores;
# - altera sinais dos motores;
# - altera decisões dos motores;
# - cria score de investimento;
# - cria recomendação automática;
# - reordena oportunidades;
# - transforma scanners em votos macro;
# - executa ordens;
# - substitui decisão humana.
#
# Fluxo:
#
#   7 motores quantitativos
#           ↓
#   Synthesis Agent V2
#           ↓
#   Risk Agent V1
#           ↓
#   Decision Agent V1
#           ↓
#   Executive Report Agent V1
#           ↓
#   Relatório executivo estruturado
#
# ============================================================

from copy import deepcopy
from datetime import datetime, timezone


EXECUTIVE_REPORT_AGENT_VERSION = "1.0"


# ============================================================
# EXCEÇÕES
# ============================================================


class ExecutiveReportAgentError(Exception):
    """Erro geral do Executive Report Agent."""


class InvalidExecutiveReportInputError(
    ExecutiveReportAgentError
):
    """Entrada inválida para geração do relatório."""


# ============================================================
# AUXILIARES
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
# VALIDAÇÃO
# ============================================================


def _validate_decision(decision):

    if not isinstance(decision, dict):
        raise InvalidExecutiveReportInputError(
            "Decision deve ser um dicionário."
        )

    required = (
        "decision_agent_version",
        "status",
        "macro_context",
        "risk_context",
        "operational_context",
        "conflicts",
        "executive_alerts",
        "layers",
        "source_signals",
        "summary",
        "policy",
    )

    missing = [
        field
        for field in required
        if field not in decision
    ]

    if missing:
        raise InvalidExecutiveReportInputError(
            "Decision incompleto. Campos ausentes: "
            + ", ".join(missing)
        )

    if not isinstance(
        decision.get("macro_context"),
        dict,
    ):
        raise InvalidExecutiveReportInputError(
            "Campo 'macro_context' deve ser "
            "um dicionário."
        )

    if not isinstance(
        decision.get("risk_context"),
        dict,
    ):
        raise InvalidExecutiveReportInputError(
            "Campo 'risk_context' deve ser "
            "um dicionário."
        )

    if not isinstance(
        decision.get("operational_context"),
        dict,
    ):
        raise InvalidExecutiveReportInputError(
            "Campo 'operational_context' deve ser "
            "um dicionário."
        )

    if not isinstance(
        decision.get("layers"),
        dict,
    ):
        raise InvalidExecutiveReportInputError(
            "Campo 'layers' deve ser "
            "um dicionário."
        )

    if not isinstance(
        decision.get("policy"),
        dict,
    ):
        raise InvalidExecutiveReportInputError(
            "Campo 'policy' deve ser "
            "um dicionário."
        )

    return True


# ============================================================
# CABEÇALHO
# ============================================================


def _build_header(decision):

    return {
        "title": (
            "INVESTMENT CIO AI — "
            "RELATÓRIO EXECUTIVO"
        ),

        "report_type": (
            "CONSOLIDATED_DECISION_SUPPORT"
        ),

        "decision_agent_version": (
            decision.get(
                "decision_agent_version"
            )
        ),

        "status": decision.get("status"),

        "human_decision_required": (
            _safe_dict(
                decision.get("policy")
            ).get(
                "human_decision_required"
            )
        ),
    }


# ============================================================
# VISÃO EXECUTIVA
# ============================================================


def _build_executive_overview(decision):

    macro = _safe_dict(
        decision.get("macro_context")
    )

    operational = _safe_dict(
        decision.get(
            "operational_context"
        )
    )

    risk_context = _safe_dict(
        decision.get("risk_context")
    )

    global_risk = _safe_dict(
        risk_context.get("global_risk")
    )

    summary = _safe_dict(
        decision.get("summary")
    )

    return {
        "sp500_stance": (
            macro.get("sp500_stance")
        ),

        "global_stance": (
            macro.get("global_stance")
        ),

        "macro_risk_relationship": (
            macro.get("relationship")
        ),

        "global_risk_level": (
            global_risk.get(
                "global_risk_level"
            )
        ),

        "global_survival_status": (
            global_risk.get(
                "global_survival_status"
            )
        ),

        "global_kill_switch": (
            global_risk.get(
                "global_kill_switch"
            )
        ),

        "operational_state": (
            operational.get("state")
        ),

        "governance_state": (
            operational.get("governance")
        ),

        "operational_explanation": (
            operational.get("explanation")
        ),

        "conflict_count": (
            summary.get("conflict_count")
        ),

        "alert_count": (
            summary.get("alert_count")
        ),

        "asset_selection_systems": (
            summary.get(
                "asset_selection_systems"
            )
        ),

        "opportunity_scanners": (
            summary.get(
                "opportunity_scanners"
            )
        ),
    }


# ============================================================
# RESTRIÇÕES
# ============================================================


def _build_restrictions(decision):

    risk_context = _safe_dict(
        decision.get("risk_context")
    )

    restrictions = deepcopy(
        _safe_list(
            risk_context.get(
                "restrictions"
            )
        )
    )

    return restrictions


# ============================================================
# CONFLITOS
# ============================================================


def _build_conflicts(decision):

    return deepcopy(
        _safe_list(
            decision.get("conflicts")
        )
    )


# ============================================================
# ALERTAS
# ============================================================


def _build_alerts(decision):

    return deepcopy(
        _safe_list(
            decision.get(
                "executive_alerts"
            )
        )
    )


# ============================================================
# CAMADAS
# ============================================================


def _build_system_layers(decision):

    layers = _safe_dict(
        decision.get("layers")
    )

    return {
        "regime": deepcopy(
            _safe_list(
                layers.get("regime")
            )
        ),

        "global_risk": deepcopy(
            _safe_list(
                layers.get("global_risk")
            )
        ),

        "asset_selection": deepcopy(
            _safe_list(
                layers.get(
                    "asset_selection"
                )
            )
        ),

        "opportunity_scanners": deepcopy(
            _safe_list(
                layers.get(
                    "opportunity_scanners"
                )
            )
        ),
    }


# ============================================================
# SINAIS ORIGINAIS
# ============================================================


def _build_source_signals(decision):

    return deepcopy(
        _safe_list(
            decision.get(
                "source_signals"
            )
        )
    )


# ============================================================
# AGRUPAMENTO DOS SINAIS
# ============================================================


def _group_signals_by_system(
    source_signals,
):

    grouped = {}

    for item in source_signals:

        if not isinstance(item, dict):
            continue

        system_id = item.get(
            "system_id"
        )

        if system_id is None:
            system_id = "unknown"

        if system_id not in grouped:
            grouped[system_id] = []

        grouped[system_id].append(
            deepcopy(item)
        )

    return grouped


# ============================================================
# DESTAQUES DE RISCO
# ============================================================


def _build_risk_highlights(
    executive_overview,
    restrictions,
):

    highlights = []

    if (
        executive_overview.get(
            "global_kill_switch"
        )
        is True
    ):
        highlights.append({
            "code": "GLOBAL_KILL_SWITCH_ACTIVE",
            "severity": "CRITICAL",
            "message": (
                "Survival Kill Switch global "
                "permanece ativo."
            ),
        })

    risk_level = _normalize_text(
        executive_overview.get(
            "global_risk_level"
        )
    )

    if risk_level in {
        "CRITICO",
        "CRÍTICO",
        "CRITICAL",
    }:
        highlights.append({
            "code": "GLOBAL_RISK_CRITICAL",
            "severity": "CRITICAL",
            "message": (
                "O sistema global reporta "
                "nível crítico de risco."
            ),
        })

    relationship = _normalize_text(
        executive_overview.get(
            "macro_risk_relationship"
        )
    )

    if relationship == "DIVERGENCE":
        highlights.append({
            "code": "MACRO_RISK_DIVERGENCE",
            "severity": "WARNING",
            "message": (
                "Existe divergência entre "
                "regime e postura global de risco."
            ),
        })

    existing_codes = {
        item.get("code")
        for item in highlights
    }

    for restriction in restrictions:

        if not isinstance(
            restriction,
            dict,
        ):
            continue

        code = restriction.get("code")

        if (
            code
            and code not in existing_codes
        ):
            highlights.append(
                deepcopy(restriction)
            )

            existing_codes.add(code)

    return highlights


# ============================================================
# DESTAQUES DE OPORTUNIDADE
# ============================================================


def _build_opportunity_highlights(
    decision,
):

    operational = _safe_dict(
        decision.get(
            "operational_context"
        )
    )

    risk_context = _safe_dict(
        decision.get("risk_context")
    )

    risk_opportunity = _safe_dict(
        risk_context.get(
            "risk_opportunity_context"
        )
    )

    has_positive_entry = (
        operational.get(
            "has_positive_entry_evidence"
        )
        is True
    )

    has_global_restrictions = (
        risk_opportunity.get(
            "has_global_restrictions"
        )
        is True
    )

    highlights = []

    if has_positive_entry:

        highlights.append({
            "code": (
                "POSITIVE_ENTRY_EVIDENCE_PRESENT"
            ),

            "message": (
                "Existem sinais positivos de "
                "entrada produzidos por motores "
                "específicos."
            ),

            "changes_source_signals": False,
        })

    if (
        has_positive_entry
        and has_global_restrictions
    ):

        highlights.append({
            "code": (
                "OPPORTUNITY_UNDER_GLOBAL_RISK"
            ),

            "message": (
                "Existem oportunidades específicas "
                "simultaneamente a restrições "
                "globais de risco."
            ),

            "changes_source_signals": False,
        })

    return highlights


# ============================================================
# RASTREABILIDADE
# ============================================================


def _build_traceability(
    decision,
    layers,
):

    source_versions = deepcopy(
        _safe_dict(
            decision.get(
                "source_versions"
            )
        )
    )

    systems = []

    for layer_name in (
        "regime",
        "global_risk",
        "asset_selection",
        "opportunity_scanners",
    ):

        for system in _safe_list(
            layers.get(layer_name)
        ):

            if not isinstance(
                system,
                dict,
            ):
                continue

            system_id = system.get(
                "system_id"
            )

            if system_id:
                systems.append(
                    system_id
                )

    return {
        "source_versions": (
            source_versions
        ),

        "systems_present": (
            _unique(systems)
        ),

        "system_count": len(
            _unique(systems)
        ),

        "decision_status": (
            decision.get("status")
        ),
    }


# ============================================================
# RESUMO DE GOVERNANÇA
# ============================================================


def _build_governance_summary(
    decision,
):

    policy = _safe_dict(
        decision.get("policy")
    )

    return {
        "source_signals_preserved": (
            policy.get(
                "source_signals_preserved"
            )
        ),

        "source_order_preserved": (
            policy.get(
                "source_order_preserved"
            )
        ),

        "source_decisions_preserved": (
            policy.get(
                "source_decisions_preserved"
            )
        ),

        "source_risk_preserved": (
            policy.get(
                "source_risk_preserved"
            )
        ),

        "indicators_recalculated": (
            policy.get(
                "indicators_recalculated"
            )
        ),

        "source_risk_recalculated": (
            policy.get(
                "source_risk_recalculated"
            )
        ),

        "new_quantitative_score_created": (
            policy.get(
                "new_quantitative_score_created"
            )
        ),

        "source_decisions_overridden": (
            policy.get(
                "source_decisions_overridden"
            )
        ),

        "automatic_trade_decision_created": (
            policy.get(
                "automatic_trade_decision_created"
            )
        ),

        "broker_execution_allowed": (
            policy.get(
                "broker_execution_allowed"
            )
        ),

        "human_decision_required": (
            policy.get(
                "human_decision_required"
            )
        ),
    }


# ============================================================
# TEXTO EXECUTIVO DETERMINÍSTICO
# ============================================================


def _build_executive_text(
    overview,
):

    operational_state = (
        overview.get(
            "operational_state"
        )
        or "N/D"
    )

    governance_state = (
        overview.get(
            "governance_state"
        )
        or "N/D"
    )

    sp500_stance = (
        overview.get(
            "sp500_stance"
        )
        or "N/D"
    )

    global_stance = (
        overview.get(
            "global_stance"
        )
        or "N/D"
    )

    relationship = (
        overview.get(
            "macro_risk_relationship"
        )
        or "N/D"
    )

    global_risk = (
        overview.get(
            "global_risk_level"
        )
        or "N/D"
    )

    kill_switch = (
        "ATIVO"
        if overview.get(
            "global_kill_switch"
        )
        is True
        else "INATIVO"
    )

    return (
        "Estado operacional: "
        f"{operational_state}. "
        "Governança: "
        f"{governance_state}. "
        "SP500 Cycle Atlas: "
        f"{sp500_stance}. "
        "Postura global: "
        f"{global_stance}. "
        "Relação macro/risco: "
        f"{relationship}. "
        "Nível global de risco: "
        f"{global_risk}. "
        "Survival Kill Switch: "
        f"{kill_switch}. "
        "Os sinais dos sistemas de origem "
        "permanecem preservados e a decisão "
        "final permanece humana."
    )


# ============================================================
# STATUS
# ============================================================


def _determine_report_status(
    decision,
):

    status = _normalize_text(
        decision.get("status")
    )

    if status == "ERROR":
        return "ERROR"

    if status == "DATA_INSUFFICIENT":
        return "DATA_INSUFFICIENT"

    if status == "WARNING":
        return "WARNING"

    return "OK"


# ============================================================
# INTERFACE PRINCIPAL
# ============================================================


def build_executive_report(
    decision,
):

    """
    Gera relatório executivo estruturado a partir
    da saída validada do Decision Agent.

    A função é determinística e não utiliza LLM.
    """

    _validate_decision(
        decision
    )

    header = _build_header(
        decision
    )

    overview = (
        _build_executive_overview(
            decision
        )
    )

    restrictions = (
        _build_restrictions(
            decision
        )
    )

    conflicts = (
        _build_conflicts(
            decision
        )
    )

    alerts = (
        _build_alerts(
            decision
        )
    )

    layers = (
        _build_system_layers(
            decision
        )
    )

    source_signals = (
        _build_source_signals(
            decision
        )
    )

    signals_by_system = (
        _group_signals_by_system(
            source_signals
        )
    )

    risk_highlights = (
        _build_risk_highlights(
            overview,
            restrictions,
        )
    )

    opportunity_highlights = (
        _build_opportunity_highlights(
            decision
        )
    )

    traceability = (
        _build_traceability(
            decision,
            layers,
        )
    )

    governance = (
        _build_governance_summary(
            decision
        )
    )

    executive_text = (
        _build_executive_text(
            overview
        )
    )

    status = (
        _determine_report_status(
            decision
        )
    )

    return {
        "executive_report_agent_version": (
            EXECUTIVE_REPORT_AGENT_VERSION
        ),

        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),

        "status": status,

        "header": header,

        "executive_overview": (
            overview
        ),

        "executive_text": (
            executive_text
        ),

        "risk_highlights": (
            risk_highlights
        ),

        "opportunity_highlights": (
            opportunity_highlights
        ),

        "restrictions": (
            restrictions
        ),

        "conflicts": conflicts,

        "alerts": alerts,

        "system_layers": (
            layers
        ),

        "source_signals": (
            source_signals
        ),

        "signals_by_system": (
            signals_by_system
        ),

        "traceability": (
            traceability
        ),

        "governance": (
            governance
        ),

        "report_summary": {
            "status": status,

            "operational_state": (
                overview.get(
                    "operational_state"
                )
            ),

            "governance_state": (
                overview.get(
                    "governance_state"
                )
            ),

            "global_kill_switch": (
                overview.get(
                    "global_kill_switch"
                )
            ),

            "restriction_count": len(
                restrictions
            ),

            "conflict_count": len(
                conflicts
            ),

            "alert_count": len(
                alerts
            ),

            "risk_highlight_count": len(
                risk_highlights
            ),

            "opportunity_highlight_count": len(
                opportunity_highlights
            ),

            "source_signal_count": len(
                source_signals
            ),

            "system_count": (
                traceability.get(
                    "system_count"
                )
            ),
        },

        "policy": {
            "presentation_layer_only": True,

            "source_signals_preserved": True,

            "source_order_preserved": True,

            "source_decisions_preserved": True,

            "source_risk_preserved": True,

            "indicators_recalculated": False,

            "source_risk_recalculated": False,

            "new_quantitative_score_created": False,

            "source_decisions_overridden": False,

            "recommendation_created": False,

            "automatic_trade_decision_created": False,

            "broker_execution_allowed": False,

            "human_decision_required": True,
        },
    }


# ============================================================
# INTERFACE GENÉRICA
# ============================================================


def run_executive_report_agent(
    decision,
):

    return build_executive_report(
        decision
    )
