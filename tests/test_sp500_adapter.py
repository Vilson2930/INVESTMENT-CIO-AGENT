# ============================================================
# INVESTMENT CIO AGENT
# tests/test_sp500_adapter.py
# ============================================================

from adapters.sp500_cycle_adapter import (
    build_sp500_agent_output,
)

from agents.validator import (
    validate_agent_output,
)


def main():

    print("=" * 70)
    print("TESTE — SP500 CYCLE ATLAS ADAPTER")
    print("=" * 70)

    # ========================================================
    # SAÍDA SIMULADA DO SP500 CYCLE ATLAS
    # ========================================================

    atlas_state = {

        "sp500": 7662.15,

        "drawdown": -0.31,

        "cape": 42.17,

        "cape_percentile": 98.82,

        "valuation_regime": "EXPENSIVE",

        "market_regime": "BULL",

        "cycle_phase": "LATE_CYCLE",

        "structural_risk": "HIGH",

        "top_timing": "NEUTRAL",

        "operational_regime": (
            "YELLOW_EXPENSIVE_BULL"
        ),

        "momentum_regime": "POSITIVE",

        "labor_regime": "NEUTRAL",

        "industrial_regime": "NEUTRAL",

        "inflation_regime": "NEUTRAL",

        "monetary_regime": "RESTRICTIVE",

        "curve_regime": "NORMAL",

        "existing_position": "HOLD",

        "new_contribution_equity": 0.60,

        "new_contribution_reserve": 0.40,

        "reserve_stage": 0,

        "reserve_stage_fraction": 0.0,

        "reserve_cumulative_fraction": 0.0,

        "reserve_deployment_status": "NOT_ACTIVE",

        "reserve_pending": True,

        "reserve_blocked_by_regime": True,

        "confidence": 0.92,

        "risk_score": 75.0,

        "audit_status": "CONFIRMED_WITH_ALERTS",

        "engine_consistency_score": 96.0,

        "data_quality_score": 78.0,

        "ai_dissent": False
    }

    # ========================================================
    # ADAPTAÇÃO
    # ========================================================

    output = build_sp500_agent_output(
        atlas_state
    )

    assert output["system_id"] == (
        "sp500_cycle"
    )

    assert output["system_name"] == (
        "SP500_CYCLE_ATLAS"
    )

    assert output["status"] == "OK"

    assert output["decision"]["signal"] == (
        "HOLD"
    )

    assert output["decision"][
        "new_contribution_equity"
    ] == 0.60

    assert output["decision"][
        "new_contribution_reserve"
    ] == 0.40

    print("ADAPTER: OK")

    # ========================================================
    # VALIDAÇÃO CONTRA O SCHEMA UNIVERSAL
    # ========================================================

    validation = validate_agent_output(
        output
    )

    if not validation["valid"]:

        print()
        print("ERROS DE VALIDAÇÃO:")

        for error in validation["errors"]:
            print(
                f"- {error['path']}: "
                f"{error['message']}"
            )

    assert validation["valid"] is True

    print("SCHEMA VALIDATION: OK")

    # ========================================================
    # TESTE DE PRESERVAÇÃO
    # ========================================================

    assert output["metrics"]["cape"] == 42.17

    assert output["metrics"][
        "cape_percentile"
    ] == 98.82

    assert output["metrics"][
        "operational_regime"
    ] == "YELLOW_EXPENSIVE_BULL"

    assert output["audit"][
        "engine_consistency_score"
    ] == 96.0

    print("PRESERVAÇÃO DOS DADOS: OK")

    # ========================================================
    # TESTE DE DADO INCOMPLETO
    # ========================================================

    incomplete_state = {
        "existing_position": "HOLD"
    }

    incomplete_output = (
        build_sp500_agent_output(
            incomplete_state
        )
    )

    assert incomplete_output[
        "status"
    ] == "WARNING"

    assert len(
        incomplete_output[
            "data_quality"
        ]["missing_fields"]
    ) > 0

    incomplete_validation = (
        validate_agent_output(
            incomplete_output
        )
    )

    assert incomplete_validation[
        "valid"
    ] is True

    print(
        "DADOS INCOMPLETOS: "
        "WARNING CORRETAMENTE"
    )

    print()
    print("=" * 70)
    print(
        "SP500 CYCLE ATLAS ADAPTER — TESTE OK"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
