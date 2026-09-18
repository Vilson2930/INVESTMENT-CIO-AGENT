# ============================================================
# INVESTMENT CIO AGENT
# tests/test_us_equities_adapter.py
# ============================================================
#
# Teste do adapter:
# portfolio-acoes-americana-teste
#
# Objetivos:
# 1. Testar o adapter isoladamente.
# 2. Confirmar preservação dos sinais do robô.
# 3. Confirmar estrutura 15 ações / 3 setores.
# 4. Validar o output contra o schema universal.
# 5. Confirmar integração com o Collector.
#
# ============================================================

from adapters.us_equities_adapter import (
    adapt_us_equities_output,
)

from agents.collector import (
    collect_payload,
    get_registered_systems,
    is_system_supported,
)

from agents.validator import (
    validate_agent_output,
)


# ============================================================
# PAYLOAD DE TESTE
# ============================================================

def build_sample_payload():

    positions = []

    # --------------------------------------------------------
    # INFORMATION TECHNOLOGY
    # --------------------------------------------------------

    technology = [
        ("SNDK", "ENTRADA FORTE", 0.902464, 1.000000),
        ("FFIV", "ENTRADA", 0.667351, 0.800000),
        ("VRSN", "AGUARDAR", 0.347023, 0.500000),
        ("SMCI", "AGUARDAR", 0.253593, 0.400000),
        ("PLTR", "NÃO COMPRAR AGORA", 0.084189, 0.300000),
    ]

    for priority, (
        ticker,
        signal,
        percentile,
        final_score,
    ) in enumerate(
        technology,
        start=1,
    ):

        positions.append(
            {
                "sector": "Information Technology",
                "buy_priority_sector": float(priority),
                "ticker": ticker,
                "selection_status": "APROVADA",
                "selection_factor": "financial_strength",
                "selection_score": 0.90,
                "valuation_status": "N/D",
                "discount_status": "N/D",
                "fundamental_status": "N/D",
                "timing_method": "Momentum 6M + 12M",
                "sector_validation_status": (
                    "REGRA ALTERNATIVA APROVADA"
                ),
                "final_signal_score": final_score,
                "signal_percentile": percentile,
                "entry_signal": signal,
                "sector_weight": 0.50,
                "stock_weight": 0.10,
            }
        )

    # --------------------------------------------------------
    # INDUSTRIALS
    # --------------------------------------------------------

    industrials = [
        ("HUBB", 0.982759, 0.960096),
        ("FIX", 0.941379, 0.882934),
        ("PAYX", 0.920690, 0.848878),
        ("PNR", 0.915517, 0.841727),
        ("PWR", 0.505172, 0.648509),
    ]

    for priority, (
        ticker,
        percentile,
        final_score,
    ) in enumerate(
        industrials,
        start=1,
    ):

        positions.append(
            {
                "sector": "Industrials",
                "buy_priority_sector": float(priority),
                "ticker": ticker,
                "selection_status": "APROVADA",
                "selection_factor": "growth",
                "selection_score": 0.88,
                "valuation_status": "CARA",
                "discount_status": "ALTO",
                "fundamental_status": "MUITO FORTES",
                "timing_method": (
                    "20% Desconto + 80% Fundamentos"
                ),
                "sector_validation_status": "CONDICIONAL",
                "final_signal_score": final_score,
                "signal_percentile": percentile,
                "entry_signal": "ENTRADA",
                "sector_weight": 0.25,
                "stock_weight": 0.05,
            }
        )

    # --------------------------------------------------------
    # HEALTH CARE
    # --------------------------------------------------------

    health_care = [
        ("DXCM", "AGUARDAR", 0.409434, 0.525572),
        ("EW", "AGUARDAR", 0.371698, 0.496598),
        ("VRTX", "AGUARDAR", 0.283019, 0.402160),
        (
            "TECH",
            "NÃO COMPRAR AGORA",
            0.192453,
            0.305966,
        ),
        (
            "MRNA",
            "NÃO COMPRAR AGORA",
            0.037736,
            0.134730,
        ),
    ]

    for priority, (
        ticker,
        signal,
        percentile,
        final_score,
    ) in enumerate(
        health_care,
        start=1,
    ):

        positions.append(
            {
                "sector": "Health Care",
                "buy_priority_sector": float(priority),
                "ticker": ticker,
                "selection_status": "APROVADA",
                "selection_factor": "financial_strength",
                "selection_score": 0.90,
                "valuation_status": "NEUTRA",
                "discount_status": "MÉDIO",
                "fundamental_status": "PRESERVADOS",
                "timing_method": (
                    "10% Valuation + "
                    "80% Desconto + "
                    "10% Fundamentos"
                ),
                "sector_validation_status": "APROVADO",
                "final_signal_score": final_score,
                "signal_percentile": percentile,
                "entry_signal": signal,
                "sector_weight": 0.25,
                "stock_weight": 0.05,
            }
        )

    # --------------------------------------------------------
    # PAYLOAD RAW
    # --------------------------------------------------------

    return {

        "source_system": (
            "PORTFOLIO_ACOES_AMERICANA"
        ),

        "export_version": "1.0",

        "generated_at": (
            "2026-09-18T12:01:53.983283"
        ),

        "engine": {
            "name": "PORTFOLIO ACOES AMERICANO",
            "role": "US_EQUITY_SELECTION_TIMING",
            "asset_class": "US_EQUITIES",
            "portfolio_size": 15,
        },

        "portfolio_audit": {
            "number_of_stocks": 15,
            "number_of_sectors": 3,

            "sector_counts": {
                "Health Care": 5,
                "Industrials": 5,
                "Information Technology": 5,
            },

            "signal_counts": {
                "ENTRADA FORTE": 1,
                "ENTRADA": 6,
                "AGUARDAR": 5,
                "NÃO COMPRAR AGORA": 3,
            },

            "total_weight": 1.0,
        },

        "signal_summary": {
            "ENTRADA FORTE": 1,
            "ENTRADA": 6,
            "AGUARDAR": 5,
            "NÃO COMPRAR AGORA": 3,
        },

        "sector_summary": [

            {
                "sector": "Health Care",
                "stocks": 5,
                "sector_weight": 0.25,

                "signal_counts": {
                    "AGUARDAR": 3,
                    "NÃO COMPRAR AGORA": 2,
                },
            },

            {
                "sector": "Industrials",
                "stocks": 5,
                "sector_weight": 0.25,

                "signal_counts": {
                    "ENTRADA": 5,
                },
            },

            {
                "sector": "Information Technology",
                "stocks": 5,
                "sector_weight": 0.50,

                "signal_counts": {
                    "ENTRADA FORTE": 1,
                    "ENTRADA": 1,
                    "AGUARDAR": 2,
                    "NÃO COMPRAR AGORA": 1,
                },
            },
        ],

        "positions": positions,

        "ranking": positions,

        "policy": {
            "signals_preserved": True,
            "scores_preserved": True,
            "weights_preserved": True,
        },
    }


# ============================================================
# TESTE DO ADAPTER
# ============================================================

def test_adapter():

    payload = build_sample_payload()

    output = adapt_us_equities_output(
        payload
    )

    assert (
        output["system_id"]
        == "us_equities"
    )

    assert (
        output["system_name"]
        == "portfolio-acoes-americana-teste"
    )

    assert (
        output["status"]
        == "OK"
    )

    assert (
        output["decision"]["signal"]
        == "MULTI_ASSET_SELECTION"
    )

    assert (
        output["decision"]["confidence"]
        is None
    )

    assert (
        output["metrics"]["portfolio_size"]
        == 15
    )

    assert (
        output["metrics"]["number_of_sectors"]
        == 3
    )

    assert (
        output["metrics"]["total_weight"]
        == 1.0
    )

    assert (
        output["metrics"]["entry_strong"]
        == 1
    )

    assert (
        output["metrics"]["entry"]
        == 6
    )

    assert (
        output["metrics"]["wait"]
        == 5
    )

    assert (
        output["metrics"]["do_not_buy_now"]
        == 3
    )

    assert len(
        output["positions"]
    ) == 15

    assert len(
        output["opportunities"]
    ) == 15


# ============================================================
# TESTE DE PRESERVAÇÃO DOS SINAIS
# ============================================================

def test_signal_preservation():

    payload = build_sample_payload()

    output = adapt_us_equities_output(
        payload
    )

    signals = {
        position["ticker"]:
        position["entry_signal"]

        for position
        in output["positions"]
    }

    assert (
        signals["SNDK"]
        == "ENTRADA FORTE"
    )

    assert (
        signals["HUBB"]
        == "ENTRADA"
    )

    assert (
        signals["DXCM"]
        == "AGUARDAR"
    )

    assert (
        signals["PLTR"]
        == "NÃO COMPRAR AGORA"
    )

    assert (
        signals["MRNA"]
        == "NÃO COMPRAR AGORA"
    )


# ============================================================
# TESTE DE NÃO RECÁLCULO
# ============================================================

def test_adapter_does_not_recalculate():

    payload = build_sample_payload()

    original_sndk = next(
        item
        for item in payload["positions"]
        if item["ticker"] == "SNDK"
    )

    output = adapt_us_equities_output(
        payload
    )

    adapted_sndk = next(
        item
        for item in output["positions"]
        if item["ticker"] == "SNDK"
    )

    assert (
        adapted_sndk["entry_signal"]
        == original_sndk["entry_signal"]
    )

    assert (
        adapted_sndk["final_signal_score"]
        == original_sndk["final_signal_score"]
    )

    assert (
        adapted_sndk["signal_percentile"]
        == original_sndk["signal_percentile"]
    )

    assert (
        adapted_sndk["stock_weight"]
        == original_sndk["stock_weight"]
    )

    assert (
        output["audit"][
            "adapter_recalculated_signals"
        ]
        is False
    )


# ============================================================
# TESTE DO SCHEMA UNIVERSAL
# ============================================================

def test_universal_schema():

    payload = build_sample_payload()

    output = adapt_us_equities_output(
        payload
    )

    validation = validate_agent_output(
        output
    )

    assert validation["valid"], (
        validation["errors"]
    )


# ============================================================
# TESTE DO COLLECTOR
# ============================================================

def test_collector():

    payload = build_sample_payload()

    output = collect_payload(
        payload
    )

    assert (
        output["system_id"]
        == "us_equities"
    )

    assert (
        output["system_name"]
        == "portfolio-acoes-americana-teste"
    )

    assert (
        output["status"]
        == "OK"
    )

    assert len(
        output["positions"]
    ) == 15


# ============================================================
# TESTE DO REGISTRO
# ============================================================

def test_registry():

    assert is_system_supported(
        "PORTFOLIO_ACOES_AMERICANA"
    )

    registered = (
        get_registered_systems()
    )

    assert (
        "SP500_CYCLE_ATLAS"
        in registered
    )

    assert (
        "COPIAULTIMOROB"
        in registered
    )

    assert (
        "PORTFOLIO_ACOES_AMERICANA"
        in registered
    )


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "INVESTMENT CIO AGENT"
    )

    print(
        "TESTE — US EQUITIES ADAPTER"
    )

    print(
        "=" * 70
    )

    test_adapter()

    print(
        "[OK] Adapter"
    )

    test_signal_preservation()

    print(
        "[OK] Preservação dos sinais"
    )

    test_adapter_does_not_recalculate()

    print(
        "[OK] Não recálculo"
    )

    test_universal_schema()

    print(
        "[OK] Schema universal"
    )

    test_collector()

    print(
        "[OK] Collector"
    )

    test_registry()

    print(
        "[OK] Registro do sistema"
    )

    print(
        "=" * 70
    )

    print(
        "US EQUITIES ADAPTER VALIDADO COM SUCESSO"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()
