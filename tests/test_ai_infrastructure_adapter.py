# ============================================================
# INVESTMENT CIO AGENT
# tests/test_ai_infrastructure_adapter.py
# ============================================================

from adapters.ai_infrastructure_adapter import (
    adapt,
    adapt_ai_infrastructure_output,
)


def build_sample_raw():
    """
    Amostra baseada na estrutura real produzida pelo
    AI_INFRASTRUCTURE_SCANNER.
    """

    panw = {
        "ranking": 1,
        "ticker": "PANW",
        "company": "Palo Alto Networks",
        "setor": "Cibersegurança",

        "signal_status":
            "PRÉ-ENTRADA — AGUARDAR GATILHO",

        "signal_approved": False,
        "signal_strength": "FORTE",

        "ranking_quality":
            "PRÉ-ENTRADA QUALIFICADA",

        "opportunity_profile":
            "PRÉ-ENTRADA COM GATILHO PENDENTE",

        "priority_score": 85.43,
        "final_score": 76.82,

        "institutional_score": 71.11,

        "institutional_classification":
            "FLUXO INSTITUCIONAL FAVORÁVEL",

        "institutional_diagnosis":
            "LÍDER EM SETOR FORTE",

        "technical_entry_score": 77.54,
        "technical_classification": "BOA",

        "technical_diagnosis":
            "ENTRADA CONFIRMADA",

        "entry_timing_score": 84.32,
        "timing_status": "PRÉ-ENTRADA",
        "timing_approved": False,
        "timing_confidence": 80.0,

        "pullback_probability": 15.0,
        "parabolic_risk": "BAIXO",

        "entry_probability": 88.38,
        "estimated_upside_percent": 13.61,
        "risk_reward_ratio": 2.17,

        "close": 360.855,

        "signal_positive_factors":
            "fluxo institucional aprovado; "
            "score técnico aprovado",

        "signal_pending_conditions":
            "timing de entrada não aprovado; "
            "aguardar confirmação de volume",

        "signal_rejection_reasons":
            "volume relativo muito baixo",

        "executive_decision":
            "PANW: confluência elevada, mas ainda "
            "falta um gatilho complementar. "
            "Nota final 76.82.",

        "timing_veto": False,
        "pullback_required": False,
    }

    msft = {
        "ranking": 2,
        "ticker": "MSFT",
        "company": "Microsoft",
        "setor": "Cloud",

        "signal_status":
            "PRÉ-ENTRADA — AGUARDAR GATILHO",

        "signal_approved": False,
        "signal_strength": "FORTE",

        "ranking_quality":
            "PRÉ-ENTRADA QUALIFICADA",

        "opportunity_profile":
            "PRÉ-ENTRADA COM GATILHO PENDENTE",

        "priority_score": 79.51,

        # Deliberadamente maior que PANW.
        # O adapter NÃO pode reordenar.
        "final_score": 78.94,

        "institutional_score": 76.32,

        "institutional_classification":
            "FLUXO INSTITUCIONAL FORTE",

        "institutional_diagnosis":
            "PREÇO FORTE, MAS FLUXO "
            "AINDA NÃO CONFIRMADO",

        "technical_entry_score": 76.12,
        "technical_classification": "BOA",

        "technical_diagnosis":
            "NEUTRA / OBSERVAÇÃO",

        "entry_timing_score": 87.12,
        "timing_status": "PRÉ-ENTRADA",
        "timing_approved": False,
        "timing_confidence": 80.0,

        "pullback_probability": 15.0,
        "parabolic_risk": "BAIXO",

        "entry_probability": 73.71,
        "estimated_upside_percent": 9.02,
        "risk_reward_ratio": 2.25,

        "close": 494.10,

        "signal_positive_factors":
            "fluxo institucional aprovado",

        "signal_pending_conditions":
            "aguardar confirmação de volume",

        "signal_rejection_reasons":
            "volume relativo muito fraco",

        "executive_decision":
            "MSFT: confluência elevada, mas ainda "
            "falta um gatilho complementar. "
            "Nota final 78.94.",

        "timing_veto": False,
        "pullback_required": False,
    }

    return {
        "source_system":
            "AI_INFRASTRUCTURE_SCANNER",

        "export_version":
            "1.0",

        "generated_at":
            "2026-09-18T17:23:31+00:00",

        "summary": {
            "classified_companies": 2,
            "approved_entries": 0,
            "watchlist_size": 2,
            "represented_sectors": 2,
        },

        "executive_ranking": [
            panw,
            msft,
        ],

        "ranking": [
            panw,
            msft,
        ],

        "approved_entries": [],

        "watchlist": [
            panw,
            msft,
        ],

        "best_by_sector": [
            panw,
            msft,
        ],

        "metadata": {
            "export_policy": {
                "indicators_recalculated": False,
                "institutional_score_recalculated": False,
                "technical_score_recalculated": False,
                "entry_timing_recalculated": False,
                "signals_recalculated": False,
                "ranking_recalculated": False,
                "executive_decisions_modified": False,
                "broker_execution_allowed": False,
                "source_results_preserved": True,
            }
        },
    }


# ============================================================
# TESTES
# ============================================================

def test_adapter():
    raw = build_sample_raw()

    output = adapt_ai_infrastructure_output(
        raw
    )

    assert output["system_id"] == (
        "ai_infrastructure"
    )

    assert output["system_name"] == (
        "AI Infrastructure Scanner"
    )

    assert output["status"] == "OK"

    assert output["schema_version"] == "1.0"


def test_no_global_buy_signal():
    output = adapt_ai_infrastructure_output(
        build_sample_raw()
    )

    assert (
        output["decision"]["signal"]
        == "OPPORTUNITY_SCANNER"
    )

    assert (
        output["decision"]["confidence"]
        is None
    )

    assert (
        output["decision"]["signal"]
        not in {
            "BUY",
            "COMPRA",
            "STRONG_BUY",
            "ENTRADA",
            "ENTRADA_FORTE",
        }
    )


def test_opportunities_preserved():
    output = adapt_ai_infrastructure_output(
        build_sample_raw()
    )

    opportunities = output[
        "opportunities"
    ]

    assert len(opportunities) == 2

    assert (
        opportunities[0]["ticker"]
        == "PANW"
    )

    assert (
        opportunities[1]["ticker"]
        == "MSFT"
    )


def test_ranking_not_reordered():
    output = adapt_ai_infrastructure_output(
        build_sample_raw()
    )

    opportunities = output[
        "opportunities"
    ]

    assert opportunities[0]["ranking"] == 1
    assert opportunities[0]["ticker"] == "PANW"

    assert opportunities[1]["ranking"] == 2
    assert opportunities[1]["ticker"] == "MSFT"

    # MSFT possui final_score maior.
    # Mesmo assim não pode ultrapassar PANW.
    assert (
        opportunities[1]["final_score"]
        >
        opportunities[0]["final_score"]
    )


def test_scores_preserved():
    output = adapt_ai_infrastructure_output(
        build_sample_raw()
    )

    panw = output[
        "opportunities"
    ][0]

    assert (
        panw["institutional_score"]
        == 71.11
    )

    assert (
        panw["technical_entry_score"]
        == 77.54
    )

    assert (
        panw["entry_timing_score"]
        == 84.32
    )

    assert (
        panw["final_score"]
        == 76.82
    )

    assert (
        panw["priority_score"]
        == 85.43
    )


def test_timing_veto_preserved():
    output = adapt_ai_infrastructure_output(
        build_sample_raw()
    )

    panw = output[
        "opportunities"
    ][0]

    assert (
        panw["timing_approved"]
        is False
    )

    assert (
        panw["signal_approved"]
        is False
    )

    assert (
        panw["signal"]
        ==
        "PRÉ-ENTRADA — AGUARDAR GATILHO"
    )


def test_executive_decision_preserved():
    output = adapt_ai_infrastructure_output(
        build_sample_raw()
    )

    panw = output[
        "opportunities"
    ][0]

    assert (
        "falta um gatilho complementar"
        in panw["executive_decision"]
    )


def test_metrics():
    output = adapt_ai_infrastructure_output(
        build_sample_raw()
    )

    metrics = output["metrics"]

    assert (
        metrics["classified_companies"]
        == 2
    )

    assert (
        metrics["approved_entries"]
        == 0
    )

    assert (
        metrics["watchlist_size"]
        == 2
    )

    assert (
        metrics["represented_sectors"]
        == 2
    )


def test_signal_distribution():
    output = adapt_ai_infrastructure_output(
        build_sample_raw()
    )

    signal_counts = (
        output["metrics"]["signal_counts"]
    )

    assert (
        signal_counts[
            "PRÉ-ENTRADA — AGUARDAR GATILHO"
        ]
        == 2
    )


def test_no_recalculation():
    output = adapt_ai_infrastructure_output(
        build_sample_raw()
    )

    audit = output["audit"]

    assert (
        audit["indicators_recalculated"]
        is False
    )

    assert (
        audit[
            "institutional_score_recalculated"
        ]
        is False
    )

    assert (
        audit[
            "technical_score_recalculated"
        ]
        is False
    )

    assert (
        audit[
            "entry_timing_recalculated"
        ]
        is False
    )

    assert (
        audit["signals_recalculated"]
        is False
    )

    assert (
        audit["ranking_recalculated"]
        is False
    )

    assert (
        audit[
            "executive_decisions_modified"
        ]
        is False
    )

    assert (
        audit["source_results_preserved"]
        is True
    )


def test_no_broker_execution():
    output = adapt_ai_infrastructure_output(
        build_sample_raw()
    )

    assert (
        output["audit"][
            "broker_execution_allowed"
        ]
        is False
    )

    assert (
        output["metadata"][
            "adapter_policy"
        ]["broker_execution"]
        is False
    )


def test_data_quality():
    output = adapt_ai_infrastructure_output(
        build_sample_raw()
    )

    quality = output[
        "data_quality"
    ]

    assert (
        quality["missing_fields"]
        == []
    )

    assert (
        quality["warnings"]
        == []
    )

    assert (
        quality["score"]
        == 1.0
    )


def test_generic_interface():
    raw = build_sample_raw()

    output = adapt(raw)

    assert (
        output["system_id"]
        == "ai_infrastructure"
    )


def test_invalid_source_rejected():
    raw = build_sample_raw()

    raw["source_system"] = (
        "OUTRO_SISTEMA"
    )

    error_detected = False

    try:

        adapt_ai_infrastructure_output(
            raw
        )

    except ValueError:

        error_detected = True

    assert error_detected is True


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

def main():
    print("=" * 70)
    print("INVESTMENT CIO AGENT")
    print(
        "TESTE — AI INFRASTRUCTURE ADAPTER"
    )
    print("=" * 70)

    tests = [
        (
            "Adapter",
            test_adapter,
        ),
        (
            "Sinal global não inventado",
            test_no_global_buy_signal,
        ),
        (
            "Oportunidades preservadas",
            test_opportunities_preserved,
        ),
        (
            "Ranking não reordenado",
            test_ranking_not_reordered,
        ),
        (
            "Scores preservados",
            test_scores_preserved,
        ),
        (
            "Timing e sinal preservados",
            test_timing_veto_preserved,
        ),
        (
            "Decisão executiva preservada",
            test_executive_decision_preserved,
        ),
        (
            "Métricas",
            test_metrics,
        ),
        (
            "Distribuição dos sinais",
            test_signal_distribution,
        ),
        (
            "Não recálculo",
            test_no_recalculation,
        ),
        (
            "Sem execução em corretora",
            test_no_broker_execution,
        ),
        (
            "Qualidade dos dados",
            test_data_quality,
        ),
        (
            "Interface genérica",
            test_generic_interface,
        ),
        (
            "Fonte inválida rejeitada",
            test_invalid_source_rejected,
        ),
    ]

    for name, test in tests:

        test()

        print(
            f"[OK] {name}"
        )

    print("=" * 70)
    print(
        "AI INFRASTRUCTURE ADAPTER "
        "VALIDADO COM SUCESSO"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
