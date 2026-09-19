# ============================================================
# INVESTMENT CIO AGENT
# agents/orchestrator.py
# ============================================================
#
# ORCHESTRATOR V1
#
# Responsabilidade:
# Coordenar a execução das camadas centrais do Investment CIO:
#
#   outputs padronizados dos motores
#               ↓
#   Synthesis Agent V2
#               ↓
#   Risk Agent V1
#               ↓
#   Decision Agent V1
#               ↓
#   Executive Report Agent V1
#               ↓
#   resultado consolidado
#
# Esta camada NÃO:
# - recalcula indicadores dos motores;
# - altera sinais;
# - altera decisões;
# - cria score quantitativo;
# - cria recomendação automática;
# - executa ordens;
# - acessa corretora;
# - substitui decisão humana.
#
# ============================================================

from copy import deepcopy
from datetime import datetime, timezone

from agents.synthesis_agent import synthesize_outputs
from agents.risk_agent import assess_risk
from agents.decision_agent import build_decision
from agents.executive_report_agent import build_executive_report


ORCHESTRATOR_VERSION = "1.0"


# ============================================================
# EXCEÇÕES
# ============================================================


class OrchestratorError(Exception):
    """Erro geral do Investment CIO Orchestrator."""


class InvalidOrchestratorInputError(OrchestratorError):
    """Entrada inválida para o Orchestrator."""


class OrchestratorStageError(OrchestratorError):
    """Falha em uma das etapas internas do pipeline."""

    def __init__(self, stage, original_error):
        self.stage = stage
        self.original_error = original_error

        super().__init__(
            f"Falha na etapa '{stage}': {original_error}"
        )


# ============================================================
# CONSTANTES
# ============================================================


PIPELINE_STAGES = (
    "synthesis",
    "risk",
    "decision",
    "executive_report",
)


# ============================================================
# AUXILIARES
# ============================================================


def _utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def _safe_dict(value):
    if isinstance(value, dict):
        return value

    return {}


def _safe_list(value):
    if isinstance(value, list):
        return value

    return []


def _unique(values):
    result = []

    for value in values:
        if value is None:
            continue

        if value not in result:
            result.append(value)

    return result


# ============================================================
# VALIDAÇÃO DA ENTRADA
# ============================================================


def _validate_outputs(outputs):

    if not isinstance(outputs, list):
        raise InvalidOrchestratorInputError(
            "A entrada do Orchestrator deve ser uma lista "
            "de outputs padronizados."
        )

    if not outputs:
        raise InvalidOrchestratorInputError(
            "A lista de outputs não pode estar vazia."
        )

    for index, output in enumerate(outputs):

        if not isinstance(output, dict):
            raise InvalidOrchestratorInputError(
                "Todos os outputs devem ser dicionários. "
                f"Item inválido no índice {index}."
            )

        if not output.get("system_id"):
            raise InvalidOrchestratorInputError(
                "Todo output deve possuir 'system_id'. "
                f"Campo ausente no índice {index}."
            )

    return True


# ============================================================
# INVENTÁRIO DOS INPUTS
# ============================================================


def _build_input_inventory(outputs):

    systems = []

    for output in outputs:

        systems.append({
            "system_id": output.get("system_id"),
            "system_name": output.get("system_name"),
            "status": output.get("status"),
            "generated_at": output.get("generated_at"),
        })

    system_ids = [
        item.get("system_id")
        for item in systems
        if item.get("system_id")
    ]

    return {
        "input_count": len(outputs),
        "systems": systems,
        "system_ids": system_ids,
        "unique_system_ids": _unique(system_ids),
        "unique_system_count": len(
            _unique(system_ids)
        ),
    }


# ============================================================
# EXECUÇÃO PROTEGIDA DE ETAPA
# ============================================================


def _run_stage(
    stage_name,
    function,
    *args,
):

    try:
        return function(*args)

    except Exception as exc:
        raise OrchestratorStageError(
            stage_name,
            exc,
        ) from exc


# ============================================================
# STATUS DO PIPELINE
# ============================================================


def _build_stage_status(
    synthesis,
    risk,
    decision,
    report,
):

    return {
        "synthesis": {
            "completed": True,
            "version": synthesis.get(
                "synthesis_version"
            ),
            "status": synthesis.get(
                "status"
            ),
        },

        "risk": {
            "completed": True,
            "version": risk.get(
                "risk_agent_version"
            ),
            "status": risk.get(
                "status"
            ),
        },

        "decision": {
            "completed": True,
            "version": decision.get(
                "decision_agent_version"
            ),
            "status": decision.get(
                "status"
            ),
        },

        "executive_report": {
            "completed": True,
            "version": report.get(
                "executive_report_agent_version"
            ),
            "status": report.get(
                "status"
            ),
        },
    }


# ============================================================
# DETERMINAÇÃO DO STATUS FINAL
# ============================================================


def _determine_pipeline_status(
    synthesis,
    risk,
    decision,
    report,
):

    statuses = [
        synthesis.get("status"),
        risk.get("status"),
        decision.get("status"),
        report.get("status"),
    ]

    normalized = {
        str(status).strip().upper()
        for status in statuses
        if status is not None
    }

    if "ERROR" in normalized:
        return "ERROR"

    if "DATA_INSUFFICIENT" in normalized:
        return "DATA_INSUFFICIENT"

    if "WARNING" in normalized:
        return "WARNING"

    return "OK"


# ============================================================
# GOVERNANÇA
# ============================================================


def _build_governance(
    synthesis,
    risk,
    decision,
    report,
):

    synthesis_policy = _safe_dict(
        synthesis.get("policy")
    )

    risk_policy = _safe_dict(
        risk.get("policy")
    )

    decision_policy = _safe_dict(
        decision.get("policy")
    )

    report_policy = _safe_dict(
        report.get("policy")
    )

    return {
        "source_signals_preserved": (
            synthesis_policy.get(
                "source_signals_preserved",
                True,
            )
            is not False
            and risk_policy.get(
                "source_signals_preserved",
                True,
            )
            is not False
            and decision_policy.get(
                "source_signals_preserved",
                True,
            )
            is not False
            and report_policy.get(
                "source_signals_preserved",
                True,
            )
            is not False
        ),

        "source_order_preserved": (
            synthesis_policy.get(
                "source_order_preserved",
                True,
            )
            is not False
            and decision_policy.get(
                "source_order_preserved",
                True,
            )
            is not False
            and report_policy.get(
                "source_order_preserved",
                True,
            )
            is not False
        ),

        "source_decisions_overridden": False,

        "source_risk_recalculated": False,

        "new_quantitative_score_created": False,

        "automatic_trade_decision_created": False,

        "broker_execution_allowed": False,

        "human_decision_required": True,

        "pipeline_only_coordinates_layers": True,
    }


# ============================================================
# RESUMO DO PIPELINE
# ============================================================


def _build_pipeline_summary(
    inventory,
    synthesis,
    risk,
    decision,
    report,
    final_status,
):

    synthesis_comparison = _safe_dict(
        synthesis.get("comparison")
    )

    risk_global = _safe_dict(
        risk.get("global_constraint")
    )

    decision_macro = _safe_dict(
        decision.get("macro_context")
    )

    decision_operational = _safe_dict(
        decision.get("operational_context")
    )

    report_summary = _safe_dict(
        report.get("report_summary")
    )

    return {
        "status": final_status,

        "input_system_count": (
            inventory.get(
                "unique_system_count"
            )
        ),

        "macro_relationship": (
            decision_macro.get(
                "relationship"
            )
            or synthesis_comparison.get(
                "relationship"
            )
        ),

        "global_constraint_state": (
            risk_global.get("state")
        ),

        "hard_block": (
            risk_global.get(
                "hard_block"
            )
        ),

        "operational_state": (
            decision_operational.get(
                "state"
            )
        ),

        "governance_state": (
            decision_operational.get(
                "governance"
            )
        ),

        "global_kill_switch": (
            report_summary.get(
                "global_kill_switch"
            )
        ),

        "restriction_count": (
            report_summary.get(
                "restriction_count"
            )
        ),

        "conflict_count": (
            report_summary.get(
                "conflict_count"
            )
        ),

        "alert_count": (
            report_summary.get(
                "alert_count"
            )
        ),

        "source_signal_count": (
            report_summary.get(
                "source_signal_count"
            )
        ),

        "human_decision_required": True,

        "broker_execution_allowed": False,
    }


# ============================================================
# AUDITORIA DE IMUTABILIDADE
# ============================================================


def _assert_inputs_unchanged(
    before,
    after,
):

    if before != after:
        raise OrchestratorError(
            "Os outputs de origem foram alterados "
            "durante a execução do pipeline."
        )

    return True


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================


def run_pipeline(outputs):

    """
    Executa o pipeline central do Investment CIO Agent.

    Entrada:
        Lista de outputs já padronizados pelos adapters.

    Fluxo:
        Synthesis
            ↓
        Risk
            ↓
        Decision
            ↓
        Executive Report

    Saída:
        Estrutura única contendo todas as etapas,
        rastreabilidade, governança e relatório final.

    Nenhuma ordem de corretora é executada.
    """

    _validate_outputs(
        outputs
    )

    original_outputs = deepcopy(
        outputs
    )

    working_outputs = deepcopy(
        outputs
    )

    started_at = _utc_now()

    inventory = _build_input_inventory(
        working_outputs
    )

    # --------------------------------------------------------
    # 1 — SYNTHESIS
    # --------------------------------------------------------

    synthesis = _run_stage(
        "synthesis",
        synthesize_outputs,
        working_outputs,
    )

    # --------------------------------------------------------
    # 2 — RISK
    # --------------------------------------------------------

    risk = _run_stage(
        "risk",
        assess_risk,
        synthesis,
    )

    # --------------------------------------------------------
    # 3 — DECISION
    # --------------------------------------------------------

    decision = _run_stage(
        "decision",
        build_decision,
        synthesis,
        risk,
    )

    # --------------------------------------------------------
    # 4 — EXECUTIVE REPORT
    # --------------------------------------------------------

    report = _run_stage(
        "executive_report",
        build_executive_report,
        decision,
    )

    # --------------------------------------------------------
    # IMUTABILIDADE DOS INPUTS
    # --------------------------------------------------------

    _assert_inputs_unchanged(
        original_outputs,
        outputs,
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    final_status = (
        _determine_pipeline_status(
            synthesis,
            risk,
            decision,
            report,
        )
    )

    stage_status = (
        _build_stage_status(
            synthesis,
            risk,
            decision,
            report,
        )
    )

    governance = (
        _build_governance(
            synthesis,
            risk,
            decision,
            report,
        )
    )

    summary = (
        _build_pipeline_summary(
            inventory,
            synthesis,
            risk,
            decision,
            report,
            final_status,
        )
    )

    finished_at = _utc_now()

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    return {
        "orchestrator_version": (
            ORCHESTRATOR_VERSION
        ),

        "pipeline_name": (
            "INVESTMENT_CIO_CORE_PIPELINE"
        ),

        "status": final_status,

        "started_at": started_at,

        "finished_at": finished_at,

        "stages": list(
            PIPELINE_STAGES
        ),

        "stage_status": (
            stage_status
        ),

        "input_inventory": (
            inventory
        ),

        "synthesis": (
            synthesis
        ),

        "risk": (
            risk
        ),

        "decision": (
            decision
        ),

        "executive_report": (
            report
        ),

        "summary": (
            summary
        ),

        "governance": (
            governance
        ),

        "policy": {
            "orchestration_only": True,

            "source_outputs_preserved": True,

            "source_signals_preserved": True,

            "source_order_preserved": True,

            "source_decisions_overridden": False,

            "source_risk_recalculated": False,

            "new_quantitative_score_created": False,

            "recommendation_created": False,

            "automatic_trade_decision_created": False,

            "broker_execution_allowed": False,

            "human_decision_required": True,
        },
    }


# ============================================================
# INTERFACE ALTERNATIVA
# ============================================================


def orchestrate(outputs):

    """
    Alias simples para run_pipeline().
    """

    return run_pipeline(
        outputs
    )


# ============================================================
# INTERFACE GENÉRICA
# ============================================================


def run_orchestrator(outputs):

    """
    Interface genérica do Orchestrator V1.
    """

    return run_pipeline(
        outputs
    )
