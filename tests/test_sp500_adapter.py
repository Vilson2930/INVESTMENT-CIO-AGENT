# ============================================================
# INVESTMENT CIO AGENT
# tests/test_sp500_adapter.py
# ============================================================
#
# Teste oficial do adaptador:
# SP500_CYCLE_ATLAS -> INVESTMENT CIO AGENT
#
# Baseado na estrutura REAL produzida por:
# outputs/agent_output_raw.json
#
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
    # 1. PAYLOAD REAL DO SP500 CYCLE ATLAS
    # ========================================================

    atlas_payload = {

        "source_system": "SP500_CYCLE_ATLAS",

        "export_version": "1.0",

        "generated_at": (
            "2026-09-17T17:38:11.232136+00:00"
        ),

        "current_state": {

            "date": "2026-09-01",

            "sp500": 7633.7001953125,

            "drawdown": -0.006822662672481106,

            "return_12m": 0.1413240476724793,

            "cape": 40.52,

            "cape_percentile": (
                0.9797639123102867
            ),

            "bull_start_date": "2022-09-01",

            "bull_start_price": (
                3585.6201171875
            ),

            "bull_age_years": 4.0,

            "bull_return": (
                1.1289762846657179
            ),

            "fed_funds": 3.63,

            "fed_change_12m": (
                -0.7000000000000002
            ),

            "yield_curve_10y_2y": (
                0.45999999999999996
            ),

            "inflation_yoy": (
                3.353016322755642
            ),

            "inflation_change_6m": (
                0.9190122123824196
            ),

            "unemployment": 4.1,

            "sahm_indicator": -0.07,

            "industrial_production_yoy": (
                1.0794551200266955
            ),

            "valuation_regime": (
                "EXTREME_TOP_5"
            ),

            "momentum_regime": "POSITIVE",

            "drawdown_regime": "NORMAL",

            "labor_regime": "STABLE",

            "industrial_regime": "EXPANSION",

            "inflation_regime": (
                "REACCELERATING"
            ),

            "monetary_regime": "EASING",

            "curve_regime": (
                "FLAT_POSITIVE"
            ),

            "market_regime": "BULL MARKET",

            "cycle_phase": (
                "LATE_EXPANSION / "
                "VALUATION_EXTREME"
            ),

            "structural_risk": "HIGH",

            "top_timing": "NOT_CONFIRMED",

            "macro_deterioration_count": 1,

            "market_deterioration_count": 0,

            "operational_regime": (
                "YELLOW_EXPENSIVE_BULL"
            ),

            "existing_position": "HOLD",

            "new_contribution_equity": 0.60,

            "new_contribution_reserve": 0.40,

            "reserve_stage": 0,

            "reserve_stage_fraction": 0.0,

            "reserve_cumulative_fraction": 0.0,

            "reserve_deployment_status": (
                "NOT_ACTIVE"
            ),

            "reserve_pending": False,

            "reserve_blocked_by_regime": False,
        },

        "ai_audit": {

            "audit_status": (
                "CONFIRMED_WITH_WARNINGS"
            ),

            "engine_consistency_score": 92.0,

            "data_quality_score": 78.0,

            "ai_dissent": False,

            "regime_audit": (
                "Regime operacional confirmado "
                "pela auditoria."
            ),

            "data_integrity": (
                "Dados válidos com defasagem "
                "em séries macroeconômicas."
            ),

            "rule_consistency": (
                "Regras do Atlas consistentes."
            ),

            "policy_consistency": (
                "Política de aporte consistente "
                "com o regime."
            ),

            "reserve_consistency": (
                "Política da reserva consistente."
            ),

            "cross_evidence": (
                "Sem contradições materiais."
            ),

            "warnings": [
                (
                    "Defasagem de 1 a 2 meses "
                    "em séries macroeconômicas."
                )
            ],

            "strengths": [
                (
                    "Consistência entre engine "
                    "e política operacional."
                )
            ],

            "manual_review_points": [
                (
                    "Monitorar frescor das séries "
                    "macroeconômicas."
                )
            ],

            "final_opinion": (
                "Execução internamente consistente."
            ),
        },
    }

    # ========================================================
    # 2. ADAPTAÇÃO
    # ========================================================

    output = build_sp500_agent_output(
        atlas_payload
    )

    assert output["system_id"] == (
        "sp500_cycle"
    )

    assert output["system_name"] == (
        "SP500_CYCLE_ATLAS"
    )

    print("IDENTIDADE DO SISTEMA: OK")

    # ========================================================
    # 3. STATUS DA AUDITORIA
    # ========================================================

    # A auditoria real possui warnings.
    # Portanto o CIO deve receber WARNING.

    assert output["status"] == "WARNING"

    assert output["audit"]["status"] == (
        "CONFIRMED_WITH_WARNINGS"
    )

    assert output["audit"][
        "ai_dissent"
    ] is False

    print("STATUS DA AUDITORIA: OK")

    # ========================================================
    # 4. DECISÃO DO ATLAS
    # ========================================================

    assert output["decision"]["signal"] == (
        "HOLD"
    )

    assert output["decision"][
        "operational_regime"
    ] == "YELLOW_EXPENSIVE_BULL"

    assert output["decision"][
        "new_contribution_equity"
    ] == 0.60

    assert output["decision"][
        "new_contribution_reserve"
    ] == 0.40

    print("DECISÃO DO ATLAS: OK")

    # ========================================================
    # 5. CONFIANÇA
    # ========================================================

    # 92/100 deve ser normalizado para 0.92.

    assert output["decision"][
        "confidence"
    ] == 0.92

    print("NORMALIZAÇÃO DA CONFIANÇA: OK")

    # ========================================================
    # 6. PRESERVAÇÃO DAS MÉTRICAS
    # ========================================================

    assert output["metrics"]["sp500"] == (
        7633.7001953125
    )

    assert output["metrics"]["cape"] == 40.52

    assert output["metrics"][
        "cape_percentile"
    ] == 0.9797639123102867

    assert output["metrics"][
        "operational_regime"
    ] == "YELLOW_EXPENSIVE_BULL"

    assert output["metrics"][
        "structural_risk"
    ] == "HIGH"

    print("PRESERVAÇÃO DAS MÉTRICAS: OK")

    # ========================================================
    # 7. PRESERVAÇÃO DA AUDITORIA
    # ========================================================

    assert output["audit"][
        "engine_consistency_score"
    ] == 92.0

    assert output["audit"][
        "data_quality_score"
    ] == 78.0

    assert output["data_quality"][
        "score"
    ] == 78.0

    print("PRESERVAÇÃO DA AUDITORIA: OK")

    # ========================================================
    # 8. METADADOS
    # ========================================================

    assert output["generated_at"] == (
        "2026-09-17T17:38:11.232136+00:00"
    )

    assert output["metadata"][
        "source_export_version"
    ] == "1.0"

    assert output["metadata"][
        "adapter_version"
    ] == "1.1"

    assert output["metadata"][
        "reserve_deployment_status"
    ] == "NOT_ACTIVE"

    print("METADADOS: OK")

    # ========================================================
    # 9. VALIDAÇÃO CONTRA O SCHEMA UNIVERSAL
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

    print("SCHEMA UNIVERSAL: OK")

    # ========================================================
    # 10. TESTE DE DADOS INCOMPLETOS
    # ========================================================

    incomplete_payload = {

        "source_system": (
            "SP500_CYCLE_ATLAS"
        ),

        "export_version": "1.0",

        "generated_at": (
            "2026-09-17T17:38:11+00:00"
        ),

        "current_state": {

            "existing_position": "HOLD",
        },

        "ai_audit": {},
    }

    incomplete_output = (
        build_sp500_agent_output(
            incomplete_payload
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

    # ========================================================
    # 11. TESTE DE PROTEÇÃO CONTRA SISTEMA ERRADO
    # ========================================================

    wrong_payload = {

        "source_system": "OUTRO_SISTEMA",

        "current_state": {},

        "ai_audit": {},
    }

    error_detected = False

    try:

        build_sp500_agent_output(
            wrong_payload
        )

    except ValueError:

        error_detected = True

    assert error_detected is True

    print(
        "PROTEÇÃO DE SOURCE_SYSTEM: OK"
    )

    # ========================================================
    # RESULTADO FINAL
    # ========================================================

    print()
    print("=" * 70)
    print(
        "SP500 CYCLE ATLAS ADAPTER — TESTE OK"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
