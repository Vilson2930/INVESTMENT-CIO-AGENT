# ============================================================
# INVESTMENT CIO AGENT
# tests/test_orchestrator.py
# ============================================================
#
# TESTES — ORCHESTRATOR V1
#
# Valida o pipeline central completo:
#
# outputs dos motores
#       ↓
# Synthesis Agent V2
#       ↓
# Risk Agent V1
#       ↓
# Decision Agent V1
#       ↓
# Executive Report Agent V1
#       ↓
# Orchestrator V1
#
# ============================================================

from copy import deepcopy

from agents.orchestrator import (
    ORCHESTRATOR_VERSION,
    PIPELINE_STAGES,
    InvalidOrchestratorInputError,
    OrchestratorStageError,
    run_pipeline,
    orchestrate,
    run_orchestrator,
)

from tests.test_synthesis_agent import (
    build_all_outputs,
    build_sp500_output,
    build_global_output,
)


# ============================================================
# BUILDERS
# ============================================================


def build_full_pipeline():

    return run_pipeline(
        build_all_outputs()
    )


def build_two_base_pipeline():

    return run_pipeline([
        build_sp500_output(),
        build_global_output(),
    ])


# ============================================================
# 1 — IDENTIFICAÇÃO
# ============================================================


def test_identification():

    result = build_full_pipeline()

    assert (
        result["orchestrator_version"]
        == ORCHESTRATOR_VERSION
    )

    assert (
        result["orchestrator_version"]
        == "1.0"
    )

    assert (
        result["pipeline_name"]
        == "INVESTMENT_CIO_CORE_PIPELINE"
    )

    print(
        "ORCHESTRATOR — IDENTIFICAÇÃO: OK"
    )


# ============================================================
# 2 — STATUS FINAL
# ============================================================


def test_final_status():

    result = build_full_pipeline()

    assert result["status"] == "WARNING"

    assert (
        result["summary"]["status"]
        == "WARNING"
    )

    print(
        "ORCHESTRATOR — STATUS FINAL: OK"
    )


# ============================================================
# 3 — ORDEM DO PIPELINE
# ============================================================


def test_pipeline_order():

    result = build_full_pipeline()

    assert result["stages"] == [
        "synthesis",
        "risk",
        "decision",
        "executive_report",
    ]

    assert tuple(
        result["stages"]
    ) == PIPELINE_STAGES

    print(
        "ORCHESTRATOR — ORDEM DO PIPELINE: OK"
    )


# ============================================================
# 4 — SYNTHESIS
# ============================================================


def test_synthesis_stage():

    result = build_full_pipeline()

    synthesis = result["synthesis"]

    assert (
        synthesis["synthesis_version"]
        == "2.0"
    )

    assert (
        result["stage_status"]
        ["synthesis"]
        ["completed"]
        is True
    )

    assert (
        result["stage_status"]
        ["synthesis"]
        ["version"]
        == "2.0"
    )

    print(
        "ORCHESTRATOR — SYNTHESIS V2: OK"
    )


# ============================================================
# 5 — RISK
# ============================================================


def test_risk_stage():

    result = build_full_pipeline()

    risk = result["risk"]

    assert (
        risk["risk_agent_version"]
        == "1.0"
    )

    assert (
        result["stage_status"]
        ["risk"]
        ["completed"]
        is True
    )

    assert (
        result["stage_status"]
        ["risk"]
        ["version"]
        == "1.0"
    )

    print(
        "ORCHESTRATOR — RISK V1: OK"
    )


# ============================================================
# 6 — DECISION
# ============================================================


def test_decision_stage():

    result = build_full_pipeline()

    decision = result["decision"]

    assert (
        decision["decision_agent_version"]
        == "1.0"
    )

    assert (
        result["stage_status"]
        ["decision"]
        ["completed"]
        is True
    )

    assert (
        result["stage_status"]
        ["decision"]
        ["version"]
        == "1.0"
    )

    print(
        "ORCHESTRATOR — DECISION V1: OK"
    )


# ============================================================
# 7 — EXECUTIVE REPORT
# ============================================================


def test_report_stage():

    result = build_full_pipeline()

    report = result[
        "executive_report"
    ]

    assert (
        report[
            "executive_report_agent_version"
        ]
        == "1.0"
    )

    assert (
        result["stage_status"]
        ["executive_report"]
        ["completed"]
        is True
    )

    assert (
        result["stage_status"]
        ["executive_report"]
        ["version"]
        == "1.0"
    )

    print(
        "ORCHESTRATOR — EXECUTIVE REPORT V1: OK"
    )


# ============================================================
# 8 — SETE SISTEMAS
# ============================================================


def test_seven_systems():

    result = build_full_pipeline()

    inventory = result[
        "input_inventory"
    ]

    assert (
        inventory["input_count"]
        == 7
    )

    assert (
        inventory[
            "unique_system_count"
        ]
        == 7
    )

    expected = [
        "sp500_cycle",
        "global_portfolio",
        "us_equities",
        "b3_equities",
        "fii",
        "ai_infrastructure",
        "growth",
    ]

    assert (
        inventory["system_ids"]
        == expected
    )

    assert (
        inventory[
            "unique_system_ids"
        ]
        == expected
    )

    print(
        "ORCHESTRATOR — 7 SISTEMAS: OK"
    )


# ============================================================
# 9 — KILL SWITCH
# ============================================================


def test_kill_switch_preserved():

    result = build_full_pipeline()

    assert (
        result[
            "executive_report"
        ][
            "executive_overview"
        ][
            "global_kill_switch"
        ]
        is True
    )

    assert (
        result[
            "summary"
        ][
            "global_kill_switch"
        ]
        is True
    )

    print(
        "ORCHESTRATOR — KILL SWITCH PRESERVADO: OK"
    )


# ============================================================
# 10 — HARD BLOCK
# ============================================================


def test_hard_block():

    result = build_full_pipeline()

    assert (
        result[
            "risk"
        ][
            "global_constraint"
        ][
            "hard_block"
        ]
        is True
    )

    assert (
        result[
            "summary"
        ][
            "hard_block"
        ]
        is True
    )

    print(
        "ORCHESTRATOR — HARD BLOCK PRESERVADO: OK"
    )


# ============================================================
# 11 — DIVERGÊNCIA
# ============================================================


def test_macro_divergence():

    result = build_full_pipeline()

    assert (
        result[
            "summary"
        ][
            "macro_relationship"
        ]
        == "DIVERGENCE"
    )

    assert (
        result[
            "decision"
        ][
            "macro_context"
        ][
            "relationship"
        ]
        == "DIVERGENCE"
    )

    print(
        "ORCHESTRATOR — DIVERGÊNCIA PRESERVADA: OK"
    )


# ============================================================
# 12 — ESTADO OPERACIONAL
# ============================================================


def test_operational_state():

    result = build_full_pipeline()

    assert (
        result[
            "summary"
        ][
            "operational_state"
        ]
        == "GLOBAL_RISK_RESTRICTION"
    )

    assert (
        result[
            "summary"
        ][
            "governance_state"
        ]
        == "HARD_RESTRICTION_PRESENT"
    )

    print(
        "ORCHESTRATOR — ESTADO OPERACIONAL: OK"
    )


# ============================================================
# 13 — GROWTH
# ============================================================


def test_growth_preserved():

    result = build_full_pipeline()

    signals = result[
        "executive_report"
    ][
        "signals_by_system"
    ][
        "growth"
    ]

    opportunities = [
        item
        for item in signals
        if (
            item.get("scope")
            == "OPPORTUNITY"
        )
    ]

    assert [
        item["ticker"]
        for item in opportunities
    ] == [
        "HOOD",
        "UBER",
        "XYZ",
    ]

    assert [
        item["signal"]
        for item in opportunities
    ] == [
        "ENTRADA_FORTE",
        "ENTRADA_FORTE",
        "AGUARDAR",
    ]

    print(
        "ORCHESTRATOR — GROWTH PRESERVADO: OK"
    )


# ============================================================
# 14 — AI INFRASTRUCTURE
# ============================================================


def test_ai_infrastructure_preserved():

    result = build_full_pipeline()

    signals = result[
        "executive_report"
    ][
        "signals_by_system"
    ][
        "ai_infrastructure"
    ]

    opportunities = [
        item
        for item in signals
        if (
            item.get("scope")
            == "OPPORTUNITY"
        )
    ]

    assert [
        item["ticker"]
        for item in opportunities
    ] == [
        "PANW",
        "MSFT",
    ]

    assert [
        item["signal"]
        for item in opportunities
    ] == [
        "OBSERVAÇÃO PRIORITÁRIA",
        "AGUARDAR PULLBACK",
    ]

    print(
        "ORCHESTRATOR — AI INFRASTRUCTURE PRESERVADO: OK"
    )


# ============================================================
# 15 — CAMADAS
# ============================================================


def test_layers_preserved():

    result = build_full_pipeline()

    layers = result[
        "executive_report"
    ][
        "system_layers"
    ]

    assert len(
        layers["regime"]
    ) == 1

    assert len(
        layers["global_risk"]
    ) == 1

    assert len(
        layers["asset_selection"]
    ) == 3

    assert len(
        layers[
            "opportunity_scanners"
        ]
    ) == 2

    print(
        "ORCHESTRATOR — CAMADAS PRESERVADAS: OK"
    )


# ============================================================
# 16 — ORDEM DOS SISTEMAS
# ============================================================


def test_source_order_preserved():

    result = build_full_pipeline()

    layers = result[
        "executive_report"
    ][
        "system_layers"
    ]

    asset_ids = [
        item["system_id"]
        for item in layers[
            "asset_selection"
        ]
    ]

    scanner_ids = [
        item["system_id"]
        for item in layers[
            "opportunity_scanners"
        ]
    ]

    assert asset_ids == [
        "us_equities",
        "b3_equities",
        "fii",
    ]

    assert scanner_ids == [
        "ai_infrastructure",
        "growth",
    ]

    print(
        "ORCHESTRATOR — ORDEM PRESERVADA: OK"
    )


# ============================================================
# 17 — INPUT NÃO ALTERADO
# ============================================================


def test_input_not_mutated():

    outputs = build_all_outputs()

    before = deepcopy(
        outputs
    )

    run_pipeline(
        outputs
    )

    assert outputs == before

    print(
        "ORCHESTRATOR — INPUT NÃO ALTERADO: OK"
    )


# ============================================================
# 18 — GOVERNANÇA
# ============================================================


def test_governance():

    result = build_full_pipeline()

    governance = result[
        "governance"
    ]

    assert (
        governance[
            "source_signals_preserved"
        ]
        is True
    )

    assert (
        governance[
            "source_order_preserved"
        ]
        is True
    )

    assert (
        governance[
            "source_decisions_overridden"
        ]
        is False
    )

    assert (
        governance[
            "source_risk_recalculated"
        ]
        is False
    )

    assert (
        governance[
            "new_quantitative_score_created"
        ]
        is False
    )

    assert (
        governance[
            "automatic_trade_decision_created"
        ]
        is False
    )

    assert (
        governance[
            "broker_execution_allowed"
        ]
        is False
    )

    assert (
        governance[
            "human_decision_required"
        ]
        is True
    )

    assert (
        governance[
            "pipeline_only_coordinates_layers"
        ]
        is True
    )

    print(
        "ORCHESTRATOR — GOVERNANÇA: OK"
    )


# ============================================================
# 19 — POLÍTICA
# ============================================================


def test_policy():

    result = build_full_pipeline()

    policy = result["policy"]

    assert (
        policy[
            "orchestration_only"
        ]
        is True
    )

    assert (
        policy[
            "source_outputs_preserved"
        ]
        is True
    )

    assert (
        policy[
            "source_signals_preserved"
        ]
        is True
    )

    assert (
        policy[
            "source_order_preserved"
        ]
        is True
    )

    assert (
        policy[
            "source_decisions_overridden"
        ]
        is False
    )

    assert (
        policy[
            "source_risk_recalculated"
        ]
        is False
    )

    assert (
        policy[
            "new_quantitative_score_created"
        ]
        is False
    )

    assert (
        policy[
            "recommendation_created"
        ]
        is False
    )

    assert (
        policy[
            "automatic_trade_decision_created"
        ]
        is False
    )

    assert (
        policy[
            "broker_execution_allowed"
        ]
        is False
    )

    assert (
        policy[
            "human_decision_required"
        ]
        is True
    )

    print(
        "ORCHESTRATOR — POLÍTICA DE SEGURANÇA: OK"
    )


# ============================================================
# 20 — DECISÃO HUMANA
# ============================================================


def test_human_decision_required():

    result = build_full_pipeline()

    assert (
        result[
            "summary"
        ][
            "human_decision_required"
        ]
        is True
    )

    assert (
        result[
            "summary"
        ][
            "broker_execution_allowed"
        ]
        is False
    )

    print(
        "ORCHESTRATOR — DECISÃO HUMANA OBRIGATÓRIA: OK"
    )


# ============================================================
# 21 — INTERFACE ORCHESTRATE
# ============================================================


def test_orchestrate_interface():

    outputs = build_all_outputs()

    direct = run_pipeline(
        outputs
    )

    alias = orchestrate(
        outputs
    )

    assert (
        direct["status"]
        == alias["status"]
    )

    assert (
        direct["summary"]
        == alias["summary"]
    )

    assert (
        direct["executive_report"]
        ["executive_overview"]
        ==
        alias["executive_report"]
        ["executive_overview"]
    )

    print(
        "ORCHESTRATOR — INTERFACE ORCHESTRATE: OK"
    )


# ============================================================
# 22 — INTERFACE GENÉRICA
# ============================================================


def test_generic_interface():

    outputs = build_all_outputs()

    direct = run_pipeline(
        outputs
    )

    generic = run_orchestrator(
        outputs
    )

    assert (
        direct["status"]
        == generic["status"]
    )

    assert (
        direct["summary"]
        == generic["summary"]
    )

    assert (
        direct["input_inventory"]
        == generic["input_inventory"]
    )

    print(
        "ORCHESTRATOR — INTERFACE GENÉRICA: OK"
    )


# ============================================================
# 23 — PROTEÇÃO LISTA VAZIA
# ============================================================


def test_empty_input():

    try:

        run_pipeline([])

    except InvalidOrchestratorInputError:

        print(
            "ORCHESTRATOR — PROTEÇÃO LISTA VAZIA: OK"
        )

        return

    raise AssertionError(
        "Orchestrator deveria rejeitar lista vazia."
    )


# ============================================================
# 24 — PROTEÇÃO TIPO INVÁLIDO
# ============================================================


def test_invalid_input_type():

    try:

        run_pipeline({
            "system_id": "invalid"
        })

    except InvalidOrchestratorInputError:

        print(
            "ORCHESTRATOR — PROTEÇÃO TIPO INVÁLIDO: OK"
        )

        return

    raise AssertionError(
        "Orchestrator deveria rejeitar "
        "entrada que não seja lista."
    )


# ============================================================
# 25 — SYSTEM_ID OBRIGATÓRIO
# ============================================================


def test_missing_system_id():

    try:

        run_pipeline([
            {
                "system_name": "Teste"
            }
        ])

    except InvalidOrchestratorInputError:

        print(
            "ORCHESTRATOR — SYSTEM_ID OBRIGATÓRIO: OK"
        )

        return

    raise AssertionError(
        "Orchestrator deveria rejeitar "
        "output sem system_id."
    )


# ============================================================
# 26 — COMPATIBILIDADE DOIS MOTORES
# ============================================================


def test_two_base_compatibility():

    result = build_two_base_pipeline()

    assert (
        result[
            "input_inventory"
        ][
            "unique_system_count"
        ]
        == 2
    )

    assert (
        result[
            "executive_report"
        ][
            "system_layers"
        ][
            "asset_selection"
        ]
        == []
    )

    assert (
        result[
            "executive_report"
        ][
            "system_layers"
        ][
            "opportunity_scanners"
        ]
        == []
    )

    assert (
        result["status"]
        == "WARNING"
    )

    print(
        "ORCHESTRATOR — COMPATIBILIDADE DOIS MOTORES: OK"
    )


# ============================================================
# 27 — RESUMO
# ============================================================


def test_summary():

    result = build_full_pipeline()

    summary = result["summary"]

    assert (
        summary[
            "input_system_count"
        ]
        == 7
    )

    assert (
        summary[
            "macro_relationship"
        ]
        == "DIVERGENCE"
    )

    assert (
        summary[
            "hard_block"
        ]
        is True
    )

    assert (
        summary[
            "operational_state"
        ]
        == "GLOBAL_RISK_RESTRICTION"
    )

    assert (
        summary[
            "governance_state"
        ]
        == "HARD_RESTRICTION_PRESENT"
    )

    print(
        "ORCHESTRATOR — RESUMO: OK"
    )


# ============================================================
# 28 — RELATÓRIO FINAL PRESENTE
# ============================================================


def test_final_report_present():

    result = build_full_pipeline()

    report = result[
        "executive_report"
    ]

    assert (
        report["header"]["title"]
        == (
            "INVESTMENT CIO AI — "
            "RELATÓRIO EXECUTIVO"
        )
    )

    assert isinstance(
        report["executive_text"],
        str,
    )

    assert (
        len(
            report["executive_text"]
        )
        > 0
    )

    print(
        "ORCHESTRATOR — RELATÓRIO FINAL PRESENTE: OK"
    )


# ============================================================
# EXECUÇÃO
# ============================================================


def run_all_tests():

    print("=" * 70)

    print(
        "INVESTMENT CIO AGENT"
    )

    print(
        "TESTE — ORCHESTRATOR V1"
    )

    print("=" * 70)

    test_identification()

    test_final_status()

    test_pipeline_order()

    test_synthesis_stage()

    test_risk_stage()

    test_decision_stage()

    test_report_stage()

    test_seven_systems()

    test_kill_switch_preserved()

    test_hard_block()

    test_macro_divergence()

    test_operational_state()

    test_growth_preserved()

    test_ai_infrastructure_preserved()

    test_layers_preserved()

    test_source_order_preserved()

    test_input_not_mutated()

    test_governance()

    test_policy()

    test_human_decision_required()

    test_orchestrate_interface()

    test_generic_interface()

    test_empty_input()

    test_invalid_input_type()

    test_missing_system_id()

    test_two_base_compatibility()

    test_summary()

    test_final_report_present()

    print("=" * 70)

    print(
        "ORCHESTRATOR V1 — 28 TESTES OK"
    )

    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
