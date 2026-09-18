# ============================================================
# INVESTMENT CIO AGENT
# tests/test_fii_adapter.py
# ============================================================
#
# Testes do adapter:
# FII INSTITUTIONAL SCANNER
#
# Objetivo:
# garantir que o adapter traduza a saída do scanner sem:
#
# - recalcular scores;
# - reordenar ranking;
# - alterar membros da carteira;
# - alterar pesos;
# - alterar decisões operacionais;
# - transformar reserva em exclusão;
# - criar recomendação BUY/HOLD global;
# - executar ordens.
#
# ============================================================

from adapters.fii_adapter import (
    SYSTEM_ID,
    SYSTEM_NAME,
    adapt,
    adapt_fii_output,
)


# ============================================================
# FIXTURE REPRESENTATIVA DA SAÍDA REAL
# ============================================================

def build_raw_output():

    return {

        "source_system":
            "FII_INSTITUTIONAL_SCANNER",

        "export_version":
            "1.0",

        "generated_at":
            "2026-09-18T18:30:00+00:00",

        "summary": {

            "database_count":
                36,

            "fundamentals_count":
                29,

            "technical_count":
                29,

            "ranking_count":
                29,

            "portfolio_count":
                10,

            "strategic_weight_sum":
                1.0,

            "executable_weight_sum":
                0.7062863228,

            "reserved_weight_sum":
                0.2937136772,

            "optimization_success":
                True,

            "optimization_message":
                "Optimization terminated successfully",
        },

        "database":
            [],

        "fundamentals":
            [],

        "technical":
            [],

        # ----------------------------------------------------
        # O teste usa uma amostra do ranking.
        #
        # A ordem é proposital:
        # GTWR11 primeiro e KNCR11 depois.
        #
        # O adapter NÃO pode usar sorted().
        # ----------------------------------------------------

        "ranking": [

            {
                "ticker":
                    "GTWR11",

                "ranking_institucional":
                    1,

                "categoria_motor":
                    "TIJOLO",

                "segmento":
                    "Lajes Corporativas",

                "fundamental_score_final":
                    95.50,

                "status_fundamental":
                    "APROVADO",

                "fundamental_aprovado_final":
                    True,

                "technical_score":
                    90.25,

                "classificacao_tecnica":
                    "FORTE",

                "status_timing":
                    "ENTRADA TÉCNICA FORTE",

                "institutional_score":
                    94.45,

                "classificacao_institucional":
                    "PREMIUM",

                "decisao_operacional":
                    "ENTRADA FORTE",

                "prioridade_portfolio":
                    "ALTA",

                "candidato_carteira":
                    True,

                "dy_12m":
                    0.115,

                "pvp":
                    0.82,

                "confianca_dados":
                    0.95,

                "liquidez_media_60d":
                    2500000.0,

                "pilar_renda":
                    90.0,

                "pilar_estrutura":
                    92.0,

                "pilar_valuation":
                    96.0,

                "pilar_robustez":
                    93.0,

                "pilar_risco":
                    88.0,

                "rsi14":
                    55.0,

                "retorno_1m":
                    0.03,

                "retorno_3m":
                    0.08,

                "retorno_6m":
                    0.12,

                "dist_sma20":
                    0.02,

                "dist_sma50":
                    0.04,

                "dist_sma200":
                    0.10,

                "distancia_max_52s":
                    -0.05,

                "volume_relativo":
                    1.20,

                "score_tendencia":
                    85.0,

                "penalidade_estiramento":
                    0.0,
            },

            {
                "ticker":
                    "KNCR11",

                "ranking_institucional":
                    2,

                "categoria_motor":
                    "PAPEL",

                "segmento":
                    "Recebíveis",

                "fundamental_score_final":
                    93.20,

                "status_fundamental":
                    "APROVADO",

                "fundamental_aprovado_final":
                    True,

                "technical_score":
                    88.10,

                "classificacao_tecnica":
                    "FORTE",

                "status_timing":
                    "ENTRADA TÉCNICA FORTE",

                "institutional_score":
                    92.18,

                "classificacao_institucional":
                    "PREMIUM",

                "decisao_operacional":
                    "ENTRADA FORTE",

                "prioridade_portfolio":
                    "ALTA",

                "candidato_carteira":
                    True,

                "dy_12m":
                    0.125,

                "pvp":
                    1.02,

                "confianca_dados":
                    0.97,

                "liquidez_media_60d":
                    5000000.0,
            },

        ],

        # ----------------------------------------------------
        # Carteira estratégica representativa.
        #
        # MXRF11 é deliberadamente mantido na carteira com
        # peso executável zero e peso reservado positivo.
        #
        # Isso testa a semântica:
        #
        # RESERVADO != EXCLUÍDO
        # ----------------------------------------------------

        "portfolio": [

            {
                "ticker":
                    "GTWR11",

                "categoria_motor":
                    "TIJOLO",

                "segmento":
                    "Lajes Corporativas",

                "fundamental_score_final":
                    95.50,

                "technical_score":
                    90.25,

                "institutional_score":
                    94.45,

                "classificacao_institucional":
                    "PREMIUM",

                "status_timing":
                    "ENTRADA TÉCNICA FORTE",

                "decisao_operacional":
                    "ENTRADA FORTE",

                "status_final":
                    "COMPRAR AGORA",

                "peso_estrategico":
                    0.20,

                "peso_estrategico_pct":
                    20.0,

                "fracao_execucao":
                    1.0,

                "peso_executavel":
                    0.20,

                "peso_executavel_pct":
                    20.0,

                "peso_reservado":
                    0.0,

                "peso_reservado_pct":
                    0.0,

                "dy_12m":
                    0.115,

                "pvp":
                    0.82,

                "confianca_dados":
                    0.95,

                "prioridade_portfolio":
                    "ALTA",
            },

            {
                "ticker":
                    "KNCR11",

                "categoria_motor":
                    "PAPEL",

                "segmento":
                    "Recebíveis",

                "fundamental_score_final":
                    93.20,

                "technical_score":
                    88.10,

                "institutional_score":
                    92.18,

                "classificacao_institucional":
                    "PREMIUM",

                "status_timing":
                    "ENTRADA TÉCNICA FORTE",

                "decisao_operacional":
                    "ENTRADA FORTE",

                "status_final":
                    "COMPRAR AGORA",

                "peso_estrategico":
                    0.30,

                "peso_estrategico_pct":
                    30.0,

                "fracao_execucao":
                    1.0,

                "peso_executavel":
                    0.30,

                "peso_executavel_pct":
                    30.0,

                "peso_reservado":
                    0.0,

                "peso_reservado_pct":
                    0.0,

                "dy_12m":
                    0.125,

                "pvp":
                    1.02,

                "confianca_dados":
                    0.97,

                "prioridade_portfolio":
                    "ALTA",
            },

            {
                "ticker":
                    "MXRF11",

                "categoria_motor":
                    "PAPEL",

                "segmento":
                    "Recebíveis",

                "fundamental_score_final":
                    86.40,

                "technical_score":
                    55.00,

                "institutional_score":
                    80.12,

                "classificacao_institucional":
                    "FORTE",

                "status_timing":
                    "AGUARDAR CONFIRMAÇÃO",

                "decisao_operacional":
                    "FUNDAMENTO FORTE — AGUARDAR GATILHO",

                "status_final":
                    "RESERVA ESTRATÉGICA",

                "peso_estrategico":
                    0.50,

                "peso_estrategico_pct":
                    50.0,

                "fracao_execucao":
                    0.4125726456,

                "peso_executavel":
                    0.2062863228,

                "peso_executavel_pct":
                    20.62863228,

                "peso_reservado":
                    0.2937136772,

                "peso_reservado_pct":
                    29.37136772,

                "dy_12m":
                    0.12,

                "pvp":
                    1.00,

                "confianca_dados":
                    0.90,

                "prioridade_portfolio":
                    "MÉDIA",
            },

        ],

        "diagnostics": {

            "fundamental_score":
                89.48,

            "technical_score":
                77.03,

            "institutional_score":
                86.99,

            "dy_12m":
                0.1174,

            "volatilidade_robusta":
                0.0497,

            "hhi":
                0.1179,

            "numero_efetivo_fiis":
                8.48,

            "pregoes_risco":
                252,

            "peso_executavel":
                0.7062863228,

            "peso_reservado":
                0.2937136772,

            "optimization_success":
                True,

            "optimization_message":
                "Optimization terminated successfully",

            "exposicao": {

                "PAPEL":
                    0.45,

                "TIJOLO":
                    0.50,

                "ALTERNATIVO":
                    0.05,
            },

            "eventos_extremos": {

                "GTWR11":
                    0,

                "KNCR11":
                    0,

                "MXRF11":
                    1,
            },
        },

        "metadata": {

            "export_policy": {

                "recalculates_scores":
                    False,

                "recalculates_ranking":
                    False,

                "reorders_ranking":
                    False,

                "recalculates_portfolio":
                    False,

                "changes_portfolio_members":
                    False,

                "recalculates_weights":
                    False,

                "changes_operational_decisions":
                    False,

                "changes_execution_fraction":
                    False,

                "changes_executable_weight":
                    False,

                "changes_reserved_weight":
                    False,

                "creates_new_investment_signal":
                    False,

                "executes_broker_orders":
                    False,
            }
        },
    }


# ============================================================
# 1. IDENTIDADE DO ADAPTER
# ============================================================

def test_adapter_identity():

    raw = build_raw_output()

    result = adapt_fii_output(
        raw
    )

    assert result[
        "system_id"
    ] == SYSTEM_ID

    assert result[
        "system_id"
    ] == "fii"

    assert result[
        "system_name"
    ] == SYSTEM_NAME


# ============================================================
# 2. STATUS
# ============================================================

def test_adapter_status_ok():

    result = adapt_fii_output(
        build_raw_output()
    )

    assert result[
        "status"
    ] == "OK"


# ============================================================
# 3. NÃO CRIA BUY/HOLD GLOBAL
# ============================================================

def test_does_not_create_global_buy_signal():

    result = adapt_fii_output(
        build_raw_output()
    )

    assert (
        result[
            "decision"
        ][
            "signal"
        ]
        ==
        "STRATEGIC_PORTFOLIO_WITH_EXECUTION"
    )

    assert (
        result[
            "decision"
        ][
            "signal"
        ]
        not in {
            "BUY",
            "SELL",
            "HOLD",
        }
    )

    assert (
        result[
            "decision"
        ][
            "confidence"
        ]
        is None
    )


# ============================================================
# 4. RANKING NÃO É REORDENADO
# ============================================================

def test_ranking_order_is_preserved():

    result = adapt_fii_output(
        build_raw_output()
    )

    tickers = [

        item[
            "ticker"
        ]

        for item
        in result[
            "opportunities"
        ]

    ]

    assert tickers == [

        "GTWR11",
        "KNCR11",

    ]


# ============================================================
# 5. SCORES SÃO PRESERVADOS
# ============================================================

def test_scores_are_preserved():

    raw = build_raw_output()

    result = adapt_fii_output(
        raw
    )

    first_raw = raw[
        "ranking"
    ][0]

    first_output = result[
        "opportunities"
    ][0]

    assert (
        first_output[
            "fundamental_score_final"
        ]
        ==
        first_raw[
            "fundamental_score_final"
        ]
    )

    assert (
        first_output[
            "technical_score"
        ]
        ==
        first_raw[
            "technical_score"
        ]
    )

    assert (
        first_output[
            "institutional_score"
        ]
        ==
        first_raw[
            "institutional_score"
        ]
    )


# ============================================================
# 6. DECISÃO OPERACIONAL É PRESERVADA
# ============================================================

def test_operational_decision_is_preserved():

    raw = build_raw_output()

    result = adapt_fii_output(
        raw
    )

    assert (
        result[
            "positions"
        ][0][
            "operational_decision"
        ]
        ==
        raw[
            "portfolio"
        ][0][
            "decisao_operacional"
        ]
    )


# ============================================================
# 7. PESOS SÃO PRESERVADOS
# ============================================================

def test_weights_are_preserved():

    raw = build_raw_output()

    result = adapt_fii_output(
        raw
    )

    for index in range(
        len(
            raw[
                "portfolio"
            ]
        )
    ):

        source = raw[
            "portfolio"
        ][index]

        output = result[
            "positions"
        ][index]

        assert (
            output[
                "strategic_weight"
            ]
            ==
            source[
                "peso_estrategico"
            ]
        )

        assert (
            output[
                "execution_fraction"
            ]
            ==
            source[
                "fracao_execucao"
            ]
        )

        assert (
            output[
                "executable_weight"
            ]
            ==
            source[
                "peso_executavel"
            ]
        )

        assert (
            output[
                "reserved_weight"
            ]
            ==
            source[
                "peso_reservado"
            ]
        )


# ============================================================
# 8. RESERVA NÃO REMOVE ATIVO
# ============================================================

def test_reserved_position_is_not_removed():

    result = adapt_fii_output(
        build_raw_output()
    )

    mxrf = next(

        position

        for position
        in result[
            "positions"
        ]

        if position[
            "ticker"
        ] == "MXRF11"

    )

    assert (
        mxrf[
            "strategic_weight"
        ]
        ==
        0.50
    )

    assert (
        mxrf[
            "reserved_weight"
        ]
        ==
        0.2937136772
    )

    assert (
        mxrf[
            "final_status"
        ]
        ==
        "RESERVA ESTRATÉGICA"
    )


# ============================================================
# 9. EXECUTÁVEL + RESERVADO PRESERVADOS
# ============================================================

def test_execution_totals_are_preserved():

    result = adapt_fii_output(
        build_raw_output()
    )

    assert abs(
        result[
            "metrics"
        ][
            "executable_weight"
        ]
        -
        0.7062863228
    ) < 1e-10

    assert abs(
        result[
            "metrics"
        ][
            "reserved_weight"
        ]
        -
        0.2937136772
    ) < 1e-10

    assert abs(
        (
            result[
                "metrics"
            ][
                "executable_weight"
            ]
            +
            result[
                "metrics"
            ][
                "reserved_weight"
            ]
        )
        -
        1.0
    ) < 1e-10


# ============================================================
# 10. MÉTRICAS DO MOTOR SÃO PRESERVADAS
# ============================================================

def test_portfolio_metrics_are_preserved():

    result = adapt_fii_output(
        build_raw_output()
    )

    metrics = result[
        "metrics"
    ]

    assert (
        metrics[
            "fundamental_score"
        ]
        ==
        89.48
    )

    assert (
        metrics[
            "technical_score"
        ]
        ==
        77.03
    )

    assert (
        metrics[
            "institutional_score"
        ]
        ==
        86.99
    )

    assert (
        metrics[
            "dy_12m"
        ]
        ==
        0.1174
    )

    assert (
        metrics[
            "robust_volatility"
        ]
        ==
        0.0497
    )

    assert (
        metrics[
            "effective_fiis"
        ]
        ==
        8.48
    )


# ============================================================
# 11. EXPOSIÇÕES SÃO PRESERVADAS
# ============================================================

def test_exposure_is_preserved():

    result = adapt_fii_output(
        build_raw_output()
    )

    exposure = result[
        "metrics"
    ][
        "exposure"
    ]

    assert (
        exposure[
            "PAPEL"
        ]
        ==
        0.45
    )

    assert (
        exposure[
            "TIJOLO"
        ]
        ==
        0.50
    )

    assert (
        exposure[
            "ALTERNATIVO"
        ]
        ==
        0.05
    )


# ============================================================
# 12. EVENTO EXTREMO VIRA ALERTA, NÃO NOVA DECISÃO
# ============================================================

def test_extreme_event_creates_alert_only():

    result = adapt_fii_output(
        build_raw_output()
    )

    alerts = result[
        "risk"
    ][
        "alerts"
    ]

    assert any(

        "MXRF11"

        in alert

        for alert
        in alerts

    )

    assert (
        result[
            "risk"
        ][
            "level"
        ]
        is None
    )

    assert (
        result[
            "risk"
        ][
            "score"
        ]
        is None
    )


# ============================================================
# 13. NÃO RECALCULA
# ============================================================

def test_adapter_policy_no_recalculation():

    result = adapt_fii_output(
        build_raw_output()
    )

    policy = result[
        "metadata"
    ][
        "adapter_policy"
    ]

    assert (
        policy[
            "recalculates_scores"
        ]
        is False
    )

    assert (
        policy[
            "recalculates_ranking"
        ]
        is False
    )

    assert (
        policy[
            "reorders_ranking"
        ]
        is False
    )

    assert (
        policy[
            "recalculates_portfolio"
        ]
        is False
    )

    assert (
        policy[
            "changes_portfolio_members"
        ]
        is False
    )

    assert (
        policy[
            "recalculates_weights"
        ]
        is False
    )

    assert (
        policy[
            "changes_operational_decisions"
        ]
        is False
    )


# ============================================================
# 14. NÃO EXECUTA CORRETORA
# ============================================================

def test_no_broker_execution():

    result = adapt_fii_output(
        build_raw_output()
    )

    assert (
        result[
            "metadata"
        ][
            "adapter_policy"
        ][
            "executes_broker_orders"
        ]
        is False
    )


# ============================================================
# 15. QUALIDADE DOS DADOS
# ============================================================

def test_data_quality():

    result = adapt_fii_output(
        build_raw_output()
    )

    assert (
        result[
            "data_quality"
        ][
            "score"
        ]
        is None
    )

    assert (
        result[
            "data_quality"
        ][
            "missing_fields"
        ]
        ==
        []
    )


# ============================================================
# 16. INTERFACE GENÉRICA
# ============================================================

def test_generic_interface():

    raw = build_raw_output()

    direct = adapt_fii_output(
        raw
    )

    generic = adapt(
        raw
    )

    assert (
        direct
        ==
        generic
    )


# ============================================================
# 17. SOURCE SYSTEM INVÁLIDO
# ============================================================

def test_invalid_source_rejected():

    raw = build_raw_output()

    raw[
        "source_system"
    ] = "OUTRO_SISTEMA"

    try:

        adapt_fii_output(
            raw
        )

    except ValueError:

        return

    raise AssertionError(
        "Adapter deveria rejeitar "
        "source_system inválido."
    )


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

def main():

    tests = [

        test_adapter_identity,
        test_adapter_status_ok,
        test_does_not_create_global_buy_signal,
        test_ranking_order_is_preserved,
        test_scores_are_preserved,
        test_operational_decision_is_preserved,
        test_weights_are_preserved,
        test_reserved_position_is_not_removed,
        test_execution_totals_are_preserved,
        test_portfolio_metrics_are_preserved,
        test_exposure_is_preserved,
        test_extreme_event_creates_alert_only,
        test_adapter_policy_no_recalculation,
        test_no_broker_execution,
        test_data_quality,
        test_generic_interface,
        test_invalid_source_rejected,

    ]

    print(
        "=" * 80
    )

    print(
        "TEST FII ADAPTER"
    )

    print(
        "=" * 80
    )

    for test in tests:

        test()

        print(
            f"PASS — {test.__name__}"
        )

    print(
        "=" * 80
    )

    print(
        f"ALL TESTS PASSED — "
        f"{len(tests)} tests"
    )

    print(
        "=" * 80
    )


if __name__ == "__main__":
    main()
