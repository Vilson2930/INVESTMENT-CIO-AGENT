# ============================================================
# INVESTMENT CIO AGENT
# tests/test_collector.py
# ============================================================
#
# Teste oficial do Collector Central.
#
# Verifica:
# 1. Registro dos sistemas suportados.
# 2. Identificação do sistema de origem.
# 3. Seleção automática do adaptador correto.
# 4. Conversão para o contrato universal.
# 5. Preservação das decisões dos robôs.
# 6. Preservação dos principais dados de risco.
# 7. Integração de US Equities.
# 8. Integração de B3 Equities.
# 9. Proteção contra sistemas desconhecidos.
#
# Sistemas atualmente testados:
# - SP500_CYCLE_ATLAS
# - COPIAULTIMOROB
# - PORTFOLIO_ACOES_AMERICANA
# - PORTFOLIO_B3_OPERATIONAL
#
# ============================================================

from agents.collector import (
    collect_payload,
    identify_source_system,
    get_registered_systems,
    is_system_supported,
    UnsupportedSystemError,
)

from tests.test_us_equities_adapter import (
    build_sample_payload as build_us_equities_payload,
)

from tests.test_b3_equities_adapter import (
    build_sample_raw as build_b3_equities_payload,
)


# ============================================================
# PAYLOAD — SP500 CYCLE ATLAS
# ============================================================

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


# ============================================================
# PAYLOAD — COPIAULTIMOROB
# ============================================================

def build_copiaultimorob_payload():

    return {

        "source_system": "COPIAULTIMOROB",

        "export_version": "1.0",

        "generated_at": (
            "2026-09-17T22:00:00+00:00"
        ),

        "macro": {

            "regime": "NEUTRO",

            "sinal_operacional": "NEUTRO",

            "macro_conviction": 0.0,

            "confidence_score": 0.0,
        },

        "portfolio": {

            "total_value": 100000.0,

            "gross_turnover_final": 0.0,

            "turnover_status": "OK",

            "kill_switch": False,
        },

        "allocation": {

            "allocation_alignment_score": 0.0,

            "allocation_alignment_level": (
                "DESALINHADO"
            ),

            "total_model_drift_pct": 0.0,

            "top_gap_asset": "N/D",

            "top_gap_abs_pct": 0.0,
        },

        "survival": {

            "survival_status": (
                "REPROVADO_OPERACIONALMENTE"
            ),

            "ruin_risk": "ALTO",

            "survival_kill_switch": True,
        },

        "stress": {

            "stress_level": "CRITICO",

            "stress_score": 100.0,

            "max_drawdown_pct": -50.0,

            "forced_selling_any": True,
        },

        "risk_budget": {

            "risk_budget_level": "CRITICO",

            "risk_budget_score": 100.0,

            "top_risk_asset": "BTC",

            "max_risk_contribution_pct": 50.0,
        },

        "liquidity": {

            "liquidity_level": "OK",

            "liquidity_score": 100.0,

            "aggregate_haircut_pct": 0.0,
        },

        "counterparty": {

            "counterparty_level": "OK",

            "counterparty_score": 100.0,

            "largest_counterparty": "N/D",
        },

        "governance": {

            "integrated_risk_level": "CRITICO",

            "committee_action": (
                "BLOQUEAR_NOVAS_COMPRAS"
            ),

            "final_verdict": (
                "REPROVADO_OPERACIONALMENTE"
            ),
        },

        "ai_audit": {

            "ai_audit_status": (
                "CONFIRMADO_COM_ALERTAS"
            ),

            "ai_audit_score": 90.0,

            "root_cause": (
                "RISCO_OPERACIONAL_ELEVADO"
            ),
        },

        "nvidia_audit": {

            "openai_audit_status": (
                "CONFIRMED_WITH_WARNINGS"
            ),

            "audit_verdict": (
                "CONSISTENT_WITH_WARNINGS"
            ),

            "audit_score": 90.0,

            "audit_confidence": 0.90,

            "severity": "HIGH",

            "root_cause": (
                "RISK_CONCENTRATION"
            ),

            "final_opinion": (
                "O engine permanece internamente "
                "consistente, mas apresenta "
                "alertas relevantes de risco."
            ),
        },
    }


# ============================================================
# TESTE PRINCIPAL
# ============================================================

def main():

    print("=" * 70)
    print("TESTE — INVESTMENT CIO COLLECTOR")
    print("=" * 70)

    # ========================================================
    # 1. REGISTRO DOS QUATRO SISTEMAS
    # ========================================================

    registered = get_registered_systems()

    expected_systems = [
        "SP500_CYCLE_ATLAS",
        "COPIAULTIMOROB",
        "PORTFOLIO_ACOES_AMERICANA",
        "PORTFOLIO_B3_OPERATIONAL",
    ]

    for system in expected_systems:

        assert system in registered

        assert is_system_supported(
            system
        ) is True

    print(
        "REGISTRO DOS QUATRO SISTEMAS: OK"
    )

    # ========================================================
    # 2. SP500 — IDENTIFICAÇÃO
    # ========================================================

    atlas_payload = build_atlas_payload()

    atlas_source = identify_source_system(
        atlas_payload
    )

    assert atlas_source == (
        "SP500_CYCLE_ATLAS"
    )

    print(
        "SP500 — IDENTIFICAÇÃO: OK"
    )

    # ========================================================
    # 3. SP500 — COLLECTOR
    # ========================================================

    atlas_output = collect_payload(
        atlas_payload
    )

    assert atlas_output[
        "system_id"
    ] == "sp500_cycle"

    assert atlas_output[
        "system_name"
    ] == "SP500_CYCLE_ATLAS"

    assert atlas_output[
        "decision"
    ]["signal"] == "HOLD"

    assert atlas_output[
        "decision"
    ]["operational_regime"] == (
        "YELLOW_EXPENSIVE_BULL"
    )

    assert atlas_output[
        "decision"
    ]["new_contribution_equity"] == (
        0.60
    )

    assert atlas_output[
        "decision"
    ]["new_contribution_reserve"] == (
        0.40
    )

    assert atlas_output[
        "audit"
    ]["engine_consistency_score"] == (
        92.0
    )

    assert atlas_output[
        "audit"
    ]["data_quality_score"] == (
        78.0
    )

    assert atlas_output[
        "audit"
    ]["ai_dissent"] is False

    assert atlas_output[
        "status"
    ] == "WARNING"

    print(
        "SP500 — COLETA E VALIDAÇÃO: OK"
    )

    # ========================================================
    # 4. COPIAULTIMOROB — IDENTIFICAÇÃO
    # ========================================================

    copia_payload = (
        build_copiaultimorob_payload()
    )

    copia_source = identify_source_system(
        copia_payload
    )

    assert copia_source == (
        "COPIAULTIMOROB"
    )

    print(
        "COPIAULTIMOROB — IDENTIFICAÇÃO: OK"
    )

    # ========================================================
    # 5. COPIAULTIMOROB — COLLECTOR
    # ========================================================

    copia_output = collect_payload(
        copia_payload
    )

    assert copia_output[
        "system_id"
    ] == "global_portfolio"

    assert copia_output[
        "system_name"
    ] == "COPIAULTIMOROB"

    assert copia_output[
        "decision"
    ]["signal"] == "NEUTRO"

    assert copia_output[
        "metrics"
    ]["final_verdict"] == (
        "REPROVADO_OPERACIONALMENTE"
    )

    assert copia_output[
        "metrics"
    ]["survival_kill_switch"] is True

    assert copia_output[
        "metrics"
    ]["stress_level"] == "CRITICO"

    assert copia_output[
        "metrics"
    ]["forced_selling_any"] is True

    assert copia_output[
        "metrics"
    ]["risk_budget_level"] == "CRITICO"

    assert copia_output[
        "metrics"
    ]["top_risk_asset"] == "BTC"

    assert copia_output[
        "risk"
    ]["level"] == "CRITICO"

    assert copia_output[
        "metrics"
    ]["committee_action"] == (
        "BLOQUEAR_NOVAS_COMPRAS"
    )

    assert copia_output[
        "audit"
    ]["ai_audit_status"] == (
        "CONFIRMADO_COM_ALERTAS"
    )

    assert copia_output[
        "audit"
    ]["ai_audit_score"] == 90.0

    assert copia_output[
        "audit"
    ]["nvidia_audit_status"] == (
        "CONFIRMED_WITH_WARNINGS"
    )

    assert copia_output[
        "audit"
    ]["nvidia_audit_score"] == 90.0

    assert copia_output[
        "status"
    ] == "WARNING"

    print(
        "COPIAULTIMOROB — "
        "COLETA E VALIDAÇÃO: OK"
    )

    # ========================================================
    # 6. US EQUITIES — IDENTIFICAÇÃO
    # ========================================================

    us_payload = (
        build_us_equities_payload()
    )

    us_source = identify_source_system(
        us_payload
    )

    assert us_source == (
        "PORTFOLIO_ACOES_AMERICANA"
    )

    print(
        "US EQUITIES — IDENTIFICAÇÃO: OK"
    )

    # ========================================================
    # 7. US EQUITIES — COLLECTOR
    # ========================================================

    us_output = collect_payload(
        us_payload
    )

    assert us_output[
        "system_id"
    ] == "us_equities"

    assert us_output[
        "system_name"
    ] == (
        "portfolio-acoes-americana-teste"
    )

    assert us_output[
        "status"
    ] == "OK"

    assert us_output[
        "decision"
    ]["signal"] == (
        "MULTI_ASSET_SELECTION"
    )

    assert us_output[
        "decision"
    ]["confidence"] is None

    assert us_output[
        "metrics"
    ]["portfolio_size"] == 15

    assert us_output[
        "metrics"
    ]["number_of_sectors"] == 3

    assert us_output[
        "metrics"
    ]["total_weight"] == 1.0

    assert len(
        us_output["positions"]
    ) == 15

    us_signals = {
        position["ticker"]:
            position["entry_signal"]
        for position
        in us_output["positions"]
    }

    assert (
        us_signals["SNDK"]
        == "ENTRADA FORTE"
    )

    assert (
        us_signals["HUBB"]
        == "ENTRADA"
    )

    assert (
        us_signals["DXCM"]
        == "AGUARDAR"
    )

    assert (
        us_signals["PLTR"]
        == "NÃO COMPRAR AGORA"
    )

    print(
        "US EQUITIES — "
        "COLETA E VALIDAÇÃO: OK"
    )

    # ========================================================
    # 8. B3 EQUITIES — IDENTIFICAÇÃO
    # ========================================================

    b3_payload = (
        build_b3_equities_payload()
    )

    b3_source = identify_source_system(
        b3_payload
    )

    assert b3_source == (
        "PORTFOLIO_B3_OPERATIONAL"
    )

    print(
        "B3 EQUITIES — IDENTIFICAÇÃO: OK"
    )

    # ========================================================
    # 9. B3 EQUITIES — COLLECTOR
    # ========================================================

    b3_output = collect_payload(
        b3_payload
    )

    assert b3_output[
        "system_id"
    ] == "b3_equities"

    assert b3_output[
        "system_name"
    ] == "Portfolio-B3-Operational"

    assert b3_output[
        "status"
    ] == "WARNING"

    assert b3_output[
        "decision"
    ]["signal"] == (
        "PORTFOLIO_WITH_ASSET_SIGNALS"
    )

    assert b3_output[
        "decision"
    ]["confidence"] is None

    assert b3_output[
        "metrics"
    ]["number_of_stocks"] == 12

    assert b3_output[
        "metrics"
    ]["number_of_sectors"] == 4

    assert len(
        b3_output["positions"]
    ) == 12

    assert abs(
        b3_output[
            "metrics"
        ]["portfolio_weight_sum"]
        - 1.0
    ) < 1e-9

    b3_signals = {
        position["ticker"]:
            position["decision"]["signal"]
        for position
        in b3_output["positions"]
    }

    assert (
        b3_signals["RNEW4"]
        == "COMPRA"
    )

    assert (
        b3_signals["TOTS3"]
        == "COMPRA"
    )

    assert (
        b3_signals["AVLL3"]
        == "EVITAR"
    )

    assert (
        b3_signals["OBTC3"]
        == "SEM CONFIRMAÇÃO"
    )

    print(
        "B3 EQUITIES — "
        "COLETA E VALIDAÇÃO: OK"
    )

    # ========================================================
    # 10. PROTEÇÃO CONTRA SISTEMA DESCONHECIDO
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
        "INVESTMENT CIO COLLECTOR — "
        "4 SISTEMAS — TESTE OK"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
