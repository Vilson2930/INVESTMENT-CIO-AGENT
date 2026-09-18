# =============================================================================
# INVESTMENT CIO AGENT
# tests/test_growth_adapter.py
#
# Testes do adapter:
# GROWTH OPPORTUNITY ENGINE
# =============================================================================

from adapters.growth_adapter import (
    adapt,
    adapt_growth_output,
)


# =============================================================================
# PAYLOAD DE TESTE
# =============================================================================

def build_payload():

    return {
        "source_system":
            "GROWTH_OPPORTUNITY_ENGINE",

        "export_version":
            "1.0",

        "generated_at":
            "2026-09-18T22:30:00+00:00",

        "summary": {
            "market_tickers":
                3,

            "fundamentals_count":
                3,

            "institutional_count":
                3,

            "signals_count":
                3,

            "strategy_count":
                3,

            "signal_counts": {
                "ENTRADA_FORTE": 1,
                "ENTRADA_PARCIAL": 1,
                "AGUARDAR": 1,
            },

            "pullback_zone_count":
                2,

            "confirmation_executed_count":
                0,

            "initial_weight_sum":
                1.6,

            "effective_weight_sum":
                1.6,

            "current_cash_weight_sum":
                1.4,
        },

        "market_data": [
            {
                "ticker": "AAA",
                "rows": 1000,
            },
            {
                "ticker": "BBB",
                "rows": 1000,
            },
            {
                "ticker": "CCC",
                "rows": 1000,
            },
        ],

        "fundamentals": [
            {
                "ticker": "AAA",
                "fundamentals_ok": True,
            },
            {
                "ticker": "BBB",
                "fundamentals_ok": True,
            },
            {
                "ticker": "CCC",
                "fundamentals_ok": False,
            },
        ],

        "institutional": [
            {
                "ticker": "AAA",
                "institutional_score": 2,
            },
            {
                "ticker": "BBB",
                "institutional_score": 1,
            },
            {
                "ticker": "CCC",
                "institutional_score": 0,
            },
        ],

        "signals": [
            {
                "ticker": "AAA",
                "pullback": 0.22,
                "pullback_zone": True,
                "falling_score": 1,
                "falling_risk": "BAIXO",
                "confirmations_total": 2,
            },
            {
                "ticker": "BBB",
                "pullback": 0.26,
                "pullback_zone": True,
                "falling_score": 2,
                "falling_risk": "MODERADO",
                "confirmations_total": 1,
            },
            {
                "ticker": "CCC",
                "pullback": 0.10,
                "pullback_zone": False,
                "falling_score": 3,
                "falling_risk": "ALTO",
                "confirmations_total": 0,
            },
        ],

        "strategy": [
            {
                "ticker":
                    "AAA",

                "signal":
                    "ENTRADA_FORTE",

                "pullback":
                    0.22,

                "pullback_zone":
                    True,

                "falling_score":
                    1,

                "falling_risk":
                    "BAIXO",

                "confirmations_total":
                    2,

                "institutional_score":
                    2,

                "fundamentals_ok":
                    True,

                "growth_class":
                    "CRESCIMENTO_FORTE",

                "initial_weight":
                    1.0,

                "confirmation_weight":
                    0.0,

                "effective_weight":
                    1.0,

                "current_cash_weight":
                    0.0,

                "needs_confirmation":
                    False,

                "confirmation_executed":
                    False,

                "reason":
                    "Entrada forte segundo o motor.",
            },

            {
                "ticker":
                    "BBB",

                "signal":
                    "ENTRADA_PARCIAL",

                "pullback":
                    0.26,

                "pullback_zone":
                    True,

                "falling_score":
                    2,

                "falling_risk":
                    "MODERADO",

                "confirmations_total":
                    1,

                "institutional_score":
                    1,

                "fundamentals_ok":
                    True,

                "growth_class":
                    "CRESCIMENTO_FORTE",

                "initial_weight":
                    0.6,

                "confirmation_weight":
                    0.4,

                "effective_weight":
                    0.6,

                "current_cash_weight":
                    0.4,

                "needs_confirmation":
                    True,

                "confirmation_executed":
                    False,

                "reason":
                    "Entrada parcial segundo o motor.",
            },

            {
                "ticker":
                    "CCC",

                "signal":
                    "AGUARDAR",

                "pullback":
                    0.10,

                "pullback_zone":
                    False,

                "falling_score":
                    3,

                "falling_risk":
                    "ALTO",

                "confirmations_total":
                    0,

                "institutional_score":
                    0,

                "fundamentals_ok":
                    False,

                "growth_class":
                    "NAO_APROVADO",

                "initial_weight":
                    0.0,

                "confirmation_weight":
                    0.0,

                "effective_weight":
                    0.0,

                "current_cash_weight":
                    1.0,

                "needs_confirmation":
                    False,

                "confirmation_executed":
                    False,

                "reason":
                    "Aguardar segundo o motor.",
            },
        ],

        "outputs": {
            "opportunities_csv":
                "output/opportunities.csv",

            "report_pdf":
                "output/report.pdf",
        },

        "metadata": {
            "architecture": {
                "decision_engine":
                    "engine.strategy",
            },

            "export_policy": {
                "recalculates_market_indicators":
                    False,

                "recalculates_fundamentals":
                    False,

                "recalculates_institutional_score":
                    False,

                "recalculates_pullback":
                    False,

                "recalculates_falling_score":
                    False,

                "recalculates_confirmations":
                    False,

                "recalculates_signals":
                    False,

                "reclassifies_signals":
                    False,

                "recalculates_ranking":
                    False,

                "reorders_ranking":
                    False,

                "recalculates_weights":
                    False,

                "changes_capital_plan":
                    False,

                "changes_confirmation_state":
                    False,

                "removes_waiting_opportunities":
                    False,

                "creates_new_investment_signal":
                    False,

                "executes_broker_orders":
                    False,
            },
        },
    }


# =============================================================================
# TESTES
# =============================================================================

def test_identity():

    result = adapt_growth_output(
        build_payload()
    )

    assert (
        result["system_id"]
        == "growth"
    )

    assert (
        result["system_name"]
        == "Growth Opportunity Engine"
    )

    print(
        "GROWTH — IDENTIFICAÇÃO: OK"
    )


def test_status():

    result = adapt_growth_output(
        build_payload()
    )

    assert result["status"] == "OK"

    print(
        "GROWTH — STATUS: OK"
    )


def test_universal_signal():

    result = adapt_growth_output(
        build_payload()
    )

    assert (
        result["decision"]["signal"]
        == "OPPORTUNITY_SET_WITH_ENTRY_SIGNALS"
    )

    assert (
        result["decision"]["confidence"]
        is None
    )

    print(
        "GROWTH — SINAL UNIVERSAL: OK"
    )


def test_no_global_buy_signal():

    result = adapt_growth_output(
        build_payload()
    )

    assert (
        result["decision"]["signal"]
        not in {
            "BUY",
            "STRONG_BUY",
            "COMPRAR",
            "ENTRADA_FORTE",
            "ENTRADA_PARCIAL",
        }
    )

    print(
        "GROWTH — SEM COMPRA GLOBAL: OK"
    )


def test_preserves_ranking_order():

    payload = build_payload()

    result = adapt_growth_output(
        payload
    )

    source_order = [
        row["ticker"]
        for row
        in payload["strategy"]
    ]

    adapted_order = [
        row["ticker"]
        for row
        in result["opportunities"]
    ]

    assert adapted_order == source_order

    print(
        "GROWTH — ORDEM DO RANKING PRESERVADA: OK"
    )


def test_preserves_signals():

    payload = build_payload()

    result = adapt_growth_output(
        payload
    )

    source_signals = [
        row["signal"]
        for row
        in payload["strategy"]
    ]

    adapted_signals = [
        row["signal"]
        for row
        in result["opportunities"]
    ]

    assert adapted_signals == source_signals

    print(
        "GROWTH — SINAIS PRESERVADOS: OK"
    )


def test_wait_is_preserved():

    result = adapt_growth_output(
        build_payload()
    )

    wait_rows = [
        row
        for row
        in result["opportunities"]
        if row["signal"] == "AGUARDAR"
    ]

    assert len(wait_rows) == 1

    assert (
        wait_rows[0]["ticker"]
        == "CCC"
    )

    print(
        "GROWTH — AGUARDAR PRESERVADO: OK"
    )


def test_preserves_falling_score():

    result = adapt_growth_output(
        build_payload()
    )

    assert (
        result["opportunities"][0][
            "falling_score"
        ]
        == 1
    )

    assert (
        result["opportunities"][1][
            "falling_score"
        ]
        == 2
    )

    print(
        "GROWTH — FALLING SCORE PRESERVADO: OK"
    )


def test_preserves_confirmations():

    result = adapt_growth_output(
        build_payload()
    )

    assert (
        result["opportunities"][0][
            "confirmations_total"
        ]
        == 2
    )

    assert (
        result["opportunities"][1][
            "confirmations_total"
        ]
        == 1
    )

    print(
        "GROWTH — CONFIRMAÇÕES PRESERVADAS: OK"
    )


def test_preserves_weights():

    result = adapt_growth_output(
        build_payload()
    )

    strong = result[
        "opportunities"
    ][0]

    partial = result[
        "opportunities"
    ][1]

    wait = result[
        "opportunities"
    ][2]

    assert (
        strong["initial_weight"]
        == 1.0
    )

    assert (
        strong["effective_weight"]
        == 1.0
    )

    assert (
        partial["initial_weight"]
        == 0.6
    )

    assert (
        partial["confirmation_weight"]
        == 0.4
    )

    assert (
        partial["effective_weight"]
        == 0.6
    )

    assert (
        partial["current_cash_weight"]
        == 0.4
    )

    assert (
        wait["effective_weight"]
        == 0.0
    )

    assert (
        wait["current_cash_weight"]
        == 1.0
    )

    print(
        "GROWTH — PESOS PRESERVADOS: OK"
    )


def test_preserves_source_row():

    payload = build_payload()

    result = adapt_growth_output(
        payload
    )

    assert (
        result["opportunities"][0][
            "source_data"
        ]
        == payload["strategy"][0]
    )

    print(
        "GROWTH — LINHA ORIGINAL PRESERVADA: OK"
    )


def test_metrics():

    result = adapt_growth_output(
        build_payload()
    )

    metrics = result["metrics"]

    assert (
        metrics["market_tickers"]
        == 3
    )

    assert (
        metrics["fundamentals_count"]
        == 3
    )

    assert (
        metrics["institutional_count"]
        == 3
    )

    assert (
        metrics["signals_count"]
        == 3
    )

    assert (
        metrics["strategy_count"]
        == 3
    )

    print(
        "GROWTH — MÉTRICAS: OK"
    )


def test_no_invented_risk():

    result = adapt_growth_output(
        build_payload()
    )

    assert (
        result["risk"]["level"]
        is None
    )

    assert (
        result["risk"]["score"]
        is None
    )

    assert (
        result["risk"]["alerts"]
        == []
    )

    print(
        "GROWTH — SEM RISCO INVENTADO: OK"
    )


def test_no_recalculation():

    result = adapt_growth_output(
        build_payload()
    )

    audit = result["audit"]

    assert (
        audit[
            "recalculates_indicators"
        ]
        is False
    )

    assert (
        audit[
            "recalculates_fundamentals"
        ]
        is False
    )

    assert (
        audit[
            "recalculates_signals"
        ]
        is False
    )

    assert (
        audit[
            "recalculates_ranking"
        ]
        is False
    )

    assert (
        audit[
            "recalculates_weights"
        ]
        is False
    )

    print(
        "GROWTH — SEM RECÁLCULO: OK"
    )


def test_no_broker_execution():

    result = adapt_growth_output(
        build_payload()
    )

    assert (
        result["audit"][
            "executes_broker_orders"
        ]
        is False
    )

    print(
        "GROWTH — SEM EXECUÇÃO EM CORRETORA: OK"
    )


def test_data_quality():

    result = adapt_growth_output(
        build_payload()
    )

    assert (
        result["data_quality"][
            "missing_fields"
        ]
        == []
    )

    assert (
        result["data_quality"][
            "warnings"
        ]
        == []
    )

    print(
        "GROWTH — DATA QUALITY: OK"
    )


def test_generic_interface():

    result = adapt(
        build_payload()
    )

    assert (
        result["system_id"]
        == "growth"
    )

    print(
        "GROWTH — INTERFACE GENÉRICA: OK"
    )


def test_invalid_source():

    payload = build_payload()

    payload[
        "source_system"
    ] = "OUTRO_SISTEMA"

    try:

        adapt_growth_output(
            payload
        )

    except ValueError:

        print(
            "GROWTH — PROTEÇÃO SOURCE_SYSTEM: OK"
        )

        return

    raise AssertionError(
        "Adapter aceitou source_system inválido."
    )


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================

def main():

    test_identity()
    test_status()
    test_universal_signal()
    test_no_global_buy_signal()
    test_preserves_ranking_order()
    test_preserves_signals()
    test_wait_is_preserved()
    test_preserves_falling_score()
    test_preserves_confirmations()
    test_preserves_weights()
    test_preserves_source_row()
    test_metrics()
    test_no_invented_risk()
    test_no_recalculation()
    test_no_broker_execution()
    test_data_quality()
    test_generic_interface()
    test_invalid_source()

    print()
    print(
        "INVESTMENT CIO AGENT "
        "— GROWTH ADAPTER — 18 TESTES OK"
    )


if __name__ == "__main__":

    main()
