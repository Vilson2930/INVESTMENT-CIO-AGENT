# ============================================================
# INVESTMENT CIO AGENT
# tests/test_collector.py
# ============================================================
#
# Teste oficial do Collector Central.
#
# Verifica:
# 1. Identificação do sistema de origem.
# 2. Seleção automática do adaptador.
# 3. Conversão para o contrato universal.
# 4. Validação do output.
# 5. Proteção contra sistemas desconhecidos.
#
# ============================================================

from agents.collector import (
    collect_payload,
    identify_source_system,
    get_registered_systems,
    is_system_supported,
    UnsupportedSystemError,
)


def build_atlas_payload():

    return {

        "source_system": "SP500_CYCLE_ATLAS",

        "export_version": "1.0",

        "generated_at": (
            "2026-09-17T17:38:11.232136+00:00"
        ),

        "current_state": {

            "date": "2026-09-01",

            "sp500": 7633.7001953125,

            "drawdown": (
                -0.006822662672481106
            ),

            "return_12m": (
                0.1413240476724793
            ),

            "cape": 40.52,

            "cape_percentile": (
                0.9797639123102867
            ),

            "bull_start_date": (
                "2022-09-01"
            ),

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

            "momentum_regime": (
                "POSITIVE"
            ),

            "drawdown_regime": (
                "NORMAL"
            ),

            "labor_regime": (
                "STABLE"
            ),

            "industrial_regime": (
                "EXPANSION"
            ),

            "inflation_regime": (
                "REACCELERATING"
            ),

            "monetary_regime": (
                "EASING"
            ),

            "curve_regime": (
                "FLAT_POSITIVE"
            ),

            "market_regime": (
                "BULL MARKET"
            ),

            "cycle_phase": (
                "LATE_EXPANSION / "
                "VALUATION_EXTREME"
            ),

            "structural_risk": (
                "HIGH"
            ),

            "top_timing": (
                "NOT_CONFIRMED"
            ),

            "macro_deterioration_count": 1,

            "market_deterioration_count": 0,

            "operational_regime": (
                "YELLOW_EXPENSIVE_BULL"
            ),

            "existing_position": (
                "HOLD"
            ),

            "new_contribution_equity": (
                0.60
            ),

            "new_contribution_reserve": (
                0.40
            ),

            "reserve_stage": 0,

            "reserve_stage_fraction": 0.0,

            "reserve_cumulative_fraction": (
                0.0
            ),

            "reserve_deployment_status": (
                "NOT_ACTIVE"
            ),

            "reserve_pending": False,

            "reserve_blocked_by_regime": (
                False
            ),
        },

        "ai_audit": {

            "audit_status": (
                "CONFIRMED_WITH_WARNINGS"
            ),

            "engine_consistency_score": (
                92.0
            ),

            "data_quality_score": (
                78.0
            ),

            "ai_dissent": False,

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
                "Execução internamente "
                "consistente."
            ),
        },
    }


def main():

    print("=" * 70)
    print("TESTE — INVESTMENT CIO COLLECTOR")
    print("=" * 70)

    # ========================================================
    # 1. REGISTRO DE SISTEMAS
    # ========================================================

    registered = get_registered_systems()

    assert (
        "SP500_CYCLE_ATLAS"
        in registered
    )

    assert is_system_supported(
        "SP500_CYCLE_ATLAS"
    ) is True

    print(
        "REGISTRO DO SP500 CYCLE ATLAS: OK"
    )

    # ========================================================
    # 2. PAYLOAD
    # ========================================================

    payload = build_atlas_payload()

    source_system = (
        identify_source_system(
            payload
        )
    )

    assert source_system == (
        "SP500_CYCLE_ATLAS"
    )

    print(
        "IDENTIFICAÇÃO DO SISTEMA: OK"
    )

    # ========================================================
    # 3. COLLECTOR
    # ========================================================

    output = collect_payload(
        payload
    )

    assert output[
        "system_id"
    ] == "sp500_cycle"

    assert output[
        "system_name"
    ] == "SP500_CYCLE_ATLAS"

    print(
        "ENCAMINHAMENTO AO ADAPTADOR: OK"
    )

    # ========================================================
    # 4. DECISÃO
    # ========================================================

    assert output[
        "decision"
    ]["signal"] == "HOLD"

    assert output[
        "decision"
    ]["operational_regime"] == (
        "YELLOW_EXPENSIVE_BULL"
    )

    assert output[
        "decision"
    ]["new_contribution_equity"] == (
        0.60
    )

    assert output[
        "decision"
    ]["new_contribution_reserve"] == (
        0.40
    )

    print(
        "DECISÃO PRESERVADA: OK"
    )

    # ========================================================
    # 5. AUDITORIA
    # ========================================================

    assert output[
        "audit"
    ]["engine_consistency_score"] == (
        92.0
    )

    assert output[
        "audit"
    ]["data_quality_score"] == (
        78.0
    )

    assert output[
        "audit"
    ]["ai_dissent"] is False

    assert output[
        "status"
    ] == "WARNING"

    print(
        "AUDITORIA PRESERVADA: OK"
    )

    # ========================================================
    # 6. PROTEÇÃO CONTRA SISTEMA DESCONHECIDO
    # ========================================================

    unsupported_payload = {

        "source_system": (
            "SISTEMA_DESCONHECIDO"
        ),

        "current_state": {},
    }

    unsupported_detected = False

    try:

        collect_payload(
            unsupported_payload
        )

    except UnsupportedSystemError:

        unsupported_detected = True

    assert unsupported_detected is True

    assert is_system_supported(
        "SISTEMA_DESCONHECIDO"
    ) is False

    print(
        "PROTEÇÃO CONTRA SISTEMA "
        "DESCONHECIDO: OK"
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    print()
    print("=" * 70)
    print(
        "INVESTMENT CIO COLLECTOR — TESTE OK"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
