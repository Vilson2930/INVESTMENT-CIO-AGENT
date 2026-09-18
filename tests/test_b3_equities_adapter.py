# ============================================================
# tests/test_b3_equities_adapter.py
# INVESTMENT CIO AGENT
#
# TESTE — PORTFOLIO-B3-OPERATIONAL ADAPTER
# ============================================================

from adapters.b3_equities_adapter import (
    adapt,
    adapt_b3_equities_output,
)


# ============================================================
# SAMPLE REALISTA
# Baseado na estrutura real produzida pelo
# Portfolio-B3-Operational.
# ============================================================

def build_sample_raw():

    positions = []

    sectors = {
        "INDUSTRIALS": {
            "top4_rank": 1,
            "sector_weight": 0.40,
            "tickers": [
                ("SEQL3", "AGUARDAR"),
                ("AVLL3", "EVITAR"),
                ("GFSA3", "FRACO"),
            ],
        },

        "FINANCIALS": {
            "top4_rank": 2,
            "sector_weight": 0.30,
            "tickers": [
                ("BSLI4", "EVITAR"),
                ("BSLI3", "EVITAR"),
                ("QUAL3", "FRACO"),
            ],
        },

        "UTILITIES": {
            "top4_rank": 3,
            "sector_weight": 0.20,
            "tickers": [
                ("CEBR3", "AGUARDAR"),
                ("AMBP3", "EVITAR"),
                ("RNEW4", "COMPRA"),
            ],
        },

        "TECHNOLOGY": {
            "top4_rank": 4,
            "sector_weight": 0.10,
            "tickers": [
                ("ECOM3", "FRACO"),
                ("TOTS3", "COMPRA"),
                ("OBTC3", "SEM CONFIRMAÇÃO"),
            ],
        },
    }

    for sector, config in sectors.items():

        for sector_rank, (
            ticker,
            signal,
        ) in enumerate(
            config["tickers"],
            start=1,
        ):

            sector_weight = (
                config["sector_weight"]
            )

            portfolio_weight = (
                sector_weight / 3.0
            )

            technical_status = "PASS"

            technical_score = 60.0

            conviction = "MODERADA"

            technical_risk = "MODERADO"

            operational_action = (
                "AGUARDAR MELHOR PONTO"
            )

            if signal == "COMPRA":
                conviction = "ALTA"
                operational_action = (
                    "ENTRADA LIBERADA"
                )

            elif signal == "EVITAR":
                conviction = "MUITO BAIXA"
                technical_risk = "ELEVADO"
                operational_action = (
                    "BLOQUEAR ENTRADA "
                    "TEMPORARIAMENTE"
                )

            elif signal == "FRACO":
                conviction = "BAIXA"
                technical_risk = "ELEVADO"
                operational_action = (
                    "NÃO ENTRAR AGORA"
                )

            elif signal == "SEM CONFIRMAÇÃO":
                technical_status = (
                    "INSUFFICIENT_INDICATORS"
                )
                technical_score = None
                conviction = "INDEFINIDA"
                technical_risk = "INDEFINIDO"
                operational_action = (
                    "SEM CONFIRMAÇÃO TÉCNICA"
                )

            position = {
                "TOP4_RANK":
                    config["top4_rank"],

                "MACRO_SECTOR":
                    sector,

                "SECTOR_RANK":
                    sector_rank,

                "TICKER":
                    ticker,

                "PRICE_QUALITY_STATUS":
                    "PASS",

                "DISCOUNT_52W":
                    0.50,

                "DISCOUNT_SCORE":
                    0.90,

                "FUND_COMPONENTS_VALID":
                    5,

                "FUND_SCORE":
                    0.70,

                "FINAL_SCORE":
                    0.86,

                "SECTOR_WEIGHT":
                    sector_weight,

                "WITHIN_SECTOR_WEIGHT":
                    1.0 / 3.0,

                "PORTFOLIO_WEIGHT":
                    portfolio_weight,

                "TECHNICAL_STATUS":
                    technical_status,

                "TECHNICAL_DATE":
                    "2026-09-16",

                "TECHNICAL_OBS":
                    499,

                "TECH_PRICE":
                    (
                        None
                        if technical_status
                        == "INSUFFICIENT_INDICATORS"
                        else 10.0
                    ),

                "MM20":
                    None,

                "MM50":
                    None,

                "MM200":
                    None,

                "RSI14":
                    None,

                "MACD":
                    None,

                "MACD_SIGNAL":
                    None,

                "MACD_HIST":
                    None,

                "ATR14":
                    None,

                "ATR_PCT":
                    None,

                "RETURN_20D":
                    None,

                "RETURN_60D":
                    None,

                "DIST_MM20":
                    None,

                "DIST_MM50":
                    None,

                "DIST_MM200":
                    None,

                "VOLUME_STRENGTH":
                    None,

                "SCORE_TREND":
                    None,

                "SCORE_ENTRY":
                    None,

                "SCORE_MOMENTUM":
                    None,

                "SCORE_VOLUME":
                    None,

                "SCORE_RISK":
                    None,

                "SCORE_TECHNICAL":
                    technical_score,

                "SIGNAL_TECHNICAL":
                    signal,

                "CONVICTION_TECHNICAL":
                    conviction,

                "RISK_TECHNICAL":
                    technical_risk,

                "OPERATIONAL_ACTION":
                    operational_action,

                "TREND_STATUS":
                    "TEST",

                "RSI_STATUS":
                    "TEST",

                "MOMENTUM_STATUS":
                    "TEST",

                "VOLUME_STATUS":
                    "TEST",

                "VOLATILITY_STATUS":
                    "TEST",

                "TECHNICAL_DIAGNOSTIC":
                    "Diagnóstico técnico preservado.",
            }

            positions.append(
                position
            )

    return {
        "source_system":
            "PORTFOLIO_B3_OPERATIONAL",

        "export_version":
            "1.0",

        "generated_at":
            "2026-09-18T15:55:39+00:00",

        "engine": {
            "name":
                "Portfolio-B3-Operational",

            "role":
                "BRAZIL_EQUITY_SELECTION",

            "asset_class":
                "BRAZIL_EQUITIES",

            "portfolio_size":
                12,

            "architecture":
                "4_SECTORS_X_3_STOCKS",

            "sector_rule":
                "TOP4_1Y",

            "stock_rule":
                "DISCOUNT_80_FUNDAMENTALS_20",

            "technical_layer":
                "COMPLEMENTARY_NON_OVERRIDE",
        },

        "portfolio_audit": {
            "valid":
                True,

            "number_of_stocks":
                12,

            "number_of_sectors":
                4,

            "sector_counts": {
                "FINANCIALS": 3,
                "INDUSTRIALS": 3,
                "TECHNOLOGY": 3,
                "UTILITIES": 3,
            },

            "duplicate_tickers":
                0,

            "missing_fields":
                [],

            "warnings":
                [],
        },

        "sector_summary":
            [],

        "technical_audit": {
            "available":
                True,

            "rows":
                14,

            "status_counts": {
                "PASS": 13,
                "REVIEW": 1,
            },
        },

        "price_audit": {
            "available":
                True,

            "rows":
                12,

            "engine_status_counts": {
                "PASS": 12,
            },

            "external_status_counts": {
                "PASS": 8,
                "REVIEW": 4,
            },

            "price_quality_status_counts": {
                "PASS": 12,
            },
        },

        "positions":
            positions,

        "source_files":
            {},

        "policy": {
            "selection_recalculated":
                False,

            "technical_signal_recalculated":
                False,

            "weights_recalculated":
                False,

            "source_decisions_preserved":
                True,

            "portfolio_selection_overridden":
                False,

            "technical_layer_overrides_selection":
                False,

            "broker_execution_allowed":
                False,
        },
    }


# ============================================================
# TESTES
# ============================================================

def test_adapter():

    raw = build_sample_raw()

    result = (
        adapt_b3_equities_output(
            raw
        )
    )

    assert result[
        "system_id"
    ] == "b3_equities"

    assert result[
        "system_name"
    ] == "Portfolio-B3-Operational"

    print(
        "[OK] Adapter"
    )


def test_portfolio_structure():

    result = adapt(
        build_sample_raw()
    )

    assert len(
        result["positions"]
    ) == 12

    assert (
        result["metrics"][
            "number_of_stocks"
        ]
        == 12
    )

    assert (
        result["metrics"][
            "number_of_sectors"
        ]
        == 4
    )

    assert result[
        "metrics"
    ][
        "sector_counts"
    ] == {
        "INDUSTRIALS": 3,
        "FINANCIALS": 3,
        "UTILITIES": 3,
        "TECHNOLOGY": 3,
    }

    print(
        "[OK] Estrutura 4 setores x 3 ações"
    )


def test_signals_preserved():

    result = adapt(
        build_sample_raw()
    )

    signals = {
        position["ticker"]:
            position[
                "decision"
            ][
                "signal"
            ]
        for position
        in result["positions"]
    }

    assert signals[
        "RNEW4"
    ] == "COMPRA"

    assert signals[
        "TOTS3"
    ] == "COMPRA"

    assert signals[
        "AVLL3"
    ] == "EVITAR"

    assert signals[
        "OBTC3"
    ] == "SEM CONFIRMAÇÃO"

    print(
        "[OK] Preservação dos sinais técnicos"
    )


def test_signal_distribution():

    result = adapt(
        build_sample_raw()
    )

    counts = (
        result[
            "metrics"
        ][
            "asset_signal_counts"
        ]
    )

    assert counts[
        "COMPRA"
    ] == 2

    assert counts[
        "AGUARDAR"
    ] == 2

    assert counts[
        "FRACO"
    ] == 3

    assert counts[
        "EVITAR"
    ] == 4

    assert counts[
        "SEM CONFIRMAÇÃO"
    ] == 1

    print(
        "[OK] Distribuição dos sinais"
    )


def test_weights_preserved():

    raw = build_sample_raw()

    result = adapt(
        raw
    )

    original_weights = {
        position["TICKER"]:
            position[
                "PORTFOLIO_WEIGHT"
            ]
        for position
        in raw["positions"]
    }

    adapted_weights = {
        position["ticker"]:
            position[
                "allocation"
            ][
                "portfolio_weight"
            ]
        for position
        in result["positions"]
    }

    assert (
        original_weights
        == adapted_weights
    )

    total_weight = (
        result[
            "metrics"
        ][
            "portfolio_weight_sum"
        ]
    )

    assert abs(
        total_weight - 1.0
    ) < 1e-9

    print(
        "[OK] Preservação dos pesos"
    )


def test_no_recalculation():

    result = adapt(
        build_sample_raw()
    )

    policy = (
        result[
            "metadata"
        ][
            "adapter_policy"
        ]
    )

    assert (
        policy[
            "selection_recalculated"
        ]
        is False
    )

    assert (
        policy[
            "technical_signal_recalculated"
        ]
        is False
    )

    assert (
        policy[
            "weights_recalculated"
        ]
        is False
    )

    assert (
        policy[
            "portfolio_modified"
        ]
        is False
    )

    assert (
        policy[
            "source_decisions_preserved"
        ]
        is True
    )

    assert (
        policy[
            "broker_execution_allowed"
        ]
        is False
    )

    print(
        "[OK] Não recálculo"
    )


def test_insufficient_indicators_preserved():

    result = adapt(
        build_sample_raw()
    )

    obtc = next(
        position
        for position
        in result["positions"]
        if position["ticker"]
        == "OBTC3"
    )

    assert (
        obtc[
            "technical"
        ][
            "status"
        ]
        == "INSUFFICIENT_INDICATORS"
    )

    assert (
        obtc[
            "decision"
        ][
            "signal"
        ]
        == "SEM CONFIRMAÇÃO"
    )

    assert (
        obtc[
            "decision"
        ][
            "operational_action"
        ]
        == "SEM CONFIRMAÇÃO TÉCNICA"
    )

    print(
        "[OK] Indicadores insuficientes preservados"
    )


def test_global_signal_not_invented():

    result = adapt(
        build_sample_raw()
    )

    assert (
        result[
            "decision"
        ][
            "signal"
        ]
        == "PORTFOLIO_WITH_ASSET_SIGNALS"
    )

    assert (
        result[
            "decision"
        ][
            "confidence"
        ]
        is None
    )

    print(
        "[OK] Sinal global não inventado"
    )


def test_data_quality_warning():

    result = adapt(
        build_sample_raw()
    )

    # O JSON real possui:
    # - 1 REVIEW na auditoria técnica
    # - 4 REVIEW na validação externa de preços
    # - OBTC3 com indicadores insuficientes
    #
    # Portanto WARNING é comportamento esperado.

    assert (
        result["status"]
        == "WARNING"
    )

    warnings = (
        result[
            "data_quality"
        ][
            "warnings"
        ]
    )

    assert len(
        warnings
    ) >= 3

    print(
        "[OK] Qualidade dos dados"
    )


def test_generic_interface():

    raw = build_sample_raw()

    direct = (
        adapt_b3_equities_output(
            raw
        )
    )

    generic = adapt(
        raw
    )

    assert (
        direct
        == generic
    )

    print(
        "[OK] Interface genérica"
    )


def test_invalid_source():

    raw = build_sample_raw()

    raw[
        "source_system"
    ] = "OUTRO_SISTEMA"

    try:

        adapt(
            raw
        )

    except ValueError:

        print(
            "[OK] Fonte inválida rejeitada"
        )

        return

    raise AssertionError(
        "Adapter deveria rejeitar "
        "source_system inválido."
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print(
        "INVESTMENT CIO AGENT"
    )
    print(
        "TESTE — B3 EQUITIES ADAPTER"
    )
    print("=" * 70)

    test_adapter()

    test_portfolio_structure()

    test_signals_preserved()

    test_signal_distribution()

    test_weights_preserved()

    test_no_recalculation()

    test_insufficient_indicators_preserved()

    test_global_signal_not_invented()

    test_data_quality_warning()

    test_generic_interface()

    test_invalid_source()

    print("=" * 70)
    print(
        "B3 EQUITIES ADAPTER "
        "VALIDADO COM SUCESSO"
    )
    print("=" * 70)
