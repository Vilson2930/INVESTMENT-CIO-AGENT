# ============================================================
# INVESTMENT CIO AGENT
# adapters/sp500_cycle_adapter.py
# ============================================================
#
# Adaptador oficial:
# SP500_CYCLE_ATLAS -> INVESTMENT CIO AGENT
#
# O adaptador NÃO recalcula indicadores.
# Apenas traduz a saída do Atlas para o contrato universal.
#
# ============================================================

from datetime import datetime, timezone


SYSTEM_ID = "sp500_cycle"
SYSTEM_NAME = "SP500_CYCLE_ATLAS"
SCHEMA_VERSION = "1.0"


def _safe_float(value):

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_confidence(value):

    value = _safe_float(value)

    if value is None:
        return None

    # Permite que o Atlas forneça 0-1 ou 0-100.
    if value > 1:
        value = value / 100

    return max(0.0, min(1.0, value))


def build_sp500_agent_output(state):

    if not isinstance(state, dict):
        raise TypeError(
            "A saída do SP500 Cycle Atlas deve ser um dicionário."
        )

    # ========================================================
    # DECISÃO ORIGINAL DO ATLAS
    # ========================================================

    existing_position = state.get(
        "existing_position"
    )

    equity_allocation = _safe_float(
        state.get("new_contribution_equity")
    )

    reserve_allocation = _safe_float(
        state.get("new_contribution_reserve")
    )

    confidence = _normalize_confidence(
        state.get("confidence")
    )

    signal = (
        existing_position
        or state.get("operational_regime")
        or "UNDEFINED"
    )

    # ========================================================
    # QUALIDADE DOS DADOS
    # ========================================================

    warnings = []

    critical_fields = [
        "sp500",
        "drawdown",
        "cape",
        "operational_regime"
    ]

    missing_fields = [
        field
        for field in critical_fields
        if state.get(field) is None
    ]

    if missing_fields:
        warnings.append(
            "Campos críticos ausentes na saída do Atlas."
        )

    status = (
        "WARNING"
        if missing_fields
        else "OK"
    )

    # ========================================================
    # CONTRATO UNIVERSAL
    # ========================================================

    output = {

        "schema_version": SCHEMA_VERSION,

        "system_id": SYSTEM_ID,

        "system_name": SYSTEM_NAME,

        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "status": status,

        "decision": {

            "signal": str(signal),

            "confidence": confidence,

            "summary": (
                "Decisão quantitativa produzida pelo "
                "SP500 Cycle Atlas."
            ),

            "existing_position": existing_position,

            "new_contribution_equity": equity_allocation,

            "new_contribution_reserve": reserve_allocation
        },

        "metrics": {

            "sp500": _safe_float(
                state.get("sp500")
            ),

            "drawdown": _safe_float(
                state.get("drawdown")
            ),

            "cape": _safe_float(
                state.get("cape")
            ),

            "cape_percentile": _safe_float(
                state.get("cape_percentile")
            ),

            "valuation_regime": state.get(
                "valuation_regime"
            ),

            "market_regime": state.get(
                "market_regime"
            ),

            "cycle_phase": state.get(
                "cycle_phase"
            ),

            "structural_risk": state.get(
                "structural_risk"
            ),

            "top_timing": state.get(
                "top_timing"
            ),

            "operational_regime": state.get(
                "operational_regime"
            ),

            "momentum_regime": state.get(
                "momentum_regime"
            ),

            "labor_regime": state.get(
                "labor_regime"
            ),

            "industrial_regime": state.get(
                "industrial_regime"
            ),

            "inflation_regime": state.get(
                "inflation_regime"
            ),

            "monetary_regime": state.get(
                "monetary_regime"
            ),

            "curve_regime": state.get(
                "curve_regime"
            )
        },

        "risk": {

            "level": state.get(
                "structural_risk"
            ),

            "score": _safe_float(
                state.get("risk_score")
            ),

            "alerts": []
        },

        "data_quality": {

            "score": _safe_float(
                state.get("data_quality_score")
            ),

            "missing_fields": missing_fields,

            "warnings": warnings
        },

        "positions": [],

        "opportunities": [],

        "audit": {

            "status": state.get(
                "audit_status"
            ),

            "engine_consistency_score": (
                _safe_float(
                    state.get(
                        "engine_consistency_score"
                    )
                )
            ),

            "data_quality_score": (
                _safe_float(
                    state.get(
                        "data_quality_score"
                    )
                )
            ),

            "ai_dissent": state.get(
                "ai_dissent"
            )
        },

        "metadata": {

            "source": "SP500_CYCLE_ATLAS",

            "adapter": (
                "sp500_cycle_adapter"
            ),

            "adapter_version": "1.0",

            "reserve_stage": state.get(
                "reserve_stage"
            ),

            "reserve_stage_fraction": (
                _safe_float(
                    state.get(
                        "reserve_stage_fraction"
                    )
                )
            ),

            "reserve_cumulative_fraction": (
                _safe_float(
                    state.get(
                        "reserve_cumulative_fraction"
                    )
                )
            ),

            "reserve_deployment_status": (
                state.get(
                    "reserve_deployment_status"
                )
            ),

            "reserve_pending": state.get(
                "reserve_pending"
            ),

            "reserve_blocked_by_regime": (
                state.get(
                    "reserve_blocked_by_regime"
                )
            )
        }
    }

    return output
