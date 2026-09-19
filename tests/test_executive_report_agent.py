# ============================================================
# INVESTMENT CIO AGENT
# tests/test_executive_report_agent.py
# ============================================================
#
# TESTES — EXECUTIVE REPORT AGENT V1
#
# Valida a cadeia:
#
# 7 motores
#   ↓
# Synthesis Agent V2
#   ↓
# Risk Agent V1
#   ↓
# Decision Agent V1
#   ↓
# Executive Report Agent V1
#
# ============================================================

from copy import deepcopy

from agents.synthesis_agent import synthesize_outputs
from agents.risk_agent import assess_risk
from agents.decision_agent import build_decision

from agents.executive_report_agent import (
    EXECUTIVE_REPORT_AGENT_VERSION,
    InvalidExecutiveReportInputError,
    build_executive_report,
    run_executive_report_agent,
)

from tests.test_synthesis_agent import (
    build_all_outputs,
    build_sp500_output,
    build_global_output,
)


# ============================================================
# BUILDERS
# ============================================================


def build_full_decision():

    synthesis = synthesize_outputs(
        build_all_outputs()
    )

    risk = assess_risk(
        synthesis
    )

    return build_decision(
        synthesis,
        risk,
    )


def build_full_report():

    return build_executive_report(
        build_full_decision()
    )


def build_two_base_report():

    synthesis = synthesize_outputs([
        build_sp500_output(),
        build_global_output(),
    ])

    risk = assess_risk(
        synthesis
    )

    decision = build_decision(
        synthesis,
        risk,
    )

    return build_executive_report(
        decision
    )


# ============================================================
# 1 — IDENTIFICAÇÃO
# ============================================================


def test_identification():

    report = build_full_report()

    assert (
        report[
            "executive_report_agent_version"
        ]
        == EXECUTIVE_REPORT_AGENT_VERSION
    )

    assert (
        report[
            "executive_report_agent_version"
        ]
        == "1.0"
    )

    print(
        "REPORT — IDENTIFICAÇÃO: OK"
    )


# ============================================================
# 2 — STATUS
# ============================================================


def test_status():

    report = build_full_report()

    assert report["status"] == "WARNING"

    assert (
        report["header"]["status"]
        == "WARNING"
    )

    print(
        "REPORT — STATUS WARNING: OK"
    )


# ============================================================
# 3 — CABEÇALHO
# ============================================================


def test_header():

    report = build_full_report()

    header = report["header"]

    assert (
        header["title"]
        == (
            "INVESTMENT CIO AI — "
            "RELATÓRIO EXECUTIVO"
        )
    )

    assert (
        header["report_type"]
        == "CONSOLIDATED_DECISION_SUPPORT"
    )

    assert (
        header["decision_agent_version"]
        == "1.0"
    )

    assert (
        header["human_decision_required"]
        is True
    )

    print(
        "REPORT — CABEÇALHO: OK"
    )


# ============================================================
# 4 — CONTEXTO MACRO
# ============================================================


def test_macro_context():

    report = build_full_report()

    overview = report[
        "executive_overview"
    ]

    assert (
        overview["sp500_stance"]
        == "RISK_SEEKING"
    )

    assert (
        overview["global_stance"]
        == "DEFENSIVE"
    )

    assert (
        overview[
            "macro_risk_relationship"
        ]
        == "DIVERGENCE"
    )

    print(
        "REPORT — CONTEXTO MACRO: OK"
    )


# ============================================================
# 5 — RISCO GLOBAL
# ============================================================


def test_global_risk():

    report = build_full_report()

    overview = report[
        "executive_overview"
    ]

    assert (
        overview["global_risk_level"]
        == "CRITICO"
    )

    assert (
        overview[
            "global_survival_status"
        ]
        == "REPROVADO_OPERACIONALMENTE"
    )

    print(
        "REPORT — RISCO GLOBAL: OK"
    )


# ============================================================
# 6 — KILL SWITCH
# ============================================================


def test_kill_switch():

    report = build_full_report()

    assert (
        report[
            "executive_overview"
        ]["global_kill_switch"]
        is True
    )

    assert (
        report[
            "report_summary"
        ]["global_kill_switch"]
        is True
    )

    print(
        "REPORT — KILL SWITCH PRESERVADO: OK"
    )


# ============================================================
# 7 — ESTADO OPERACIONAL
# ============================================================


def test_operational_state():

    report = build_full_report()

    overview = report[
        "executive_overview"
    ]

    assert (
        overview["operational_state"]
        == "GLOBAL_RISK_RESTRICTION"
    )

    assert (
        overview["governance_state"]
        == "HARD_RESTRICTION_PRESENT"
    )

    print(
        "REPORT — ESTADO OPERACIONAL: OK"
    )


# ============================================================
# 8 — RESTRIÇÕES
# ============================================================


def test_restrictions():

    report = build_full_report()

    codes = [
        item.get("code")
        for item in report["restrictions"]
    ]

    assert (
        "GLOBAL_KILL_SWITCH_ACTIVE"
        in codes
    )

    assert (
        "GLOBAL_RISK_CRITICAL"
        in codes
    )

    assert (
        "GLOBAL_DEFENSIVE_STANCE"
        in codes
    )

    assert (
        "MACRO_RISK_DIVERGENCE"
        in codes
    )

    print(
        "REPORT — RESTRIÇÕES PRESERVADAS: OK"
    )


# ============================================================
# 9 — CONFLITOS
# ============================================================


def test_conflicts():

    report = build_full_report()

    codes = [
        item.get("code")
        for item in report["conflicts"]
    ]

    assert (
        "REGIME_GLOBAL_RISK_DIVERGENCE"
        in codes
    )

    assert (
        "OPPORTUNITY_VS_GLOBAL_RISK"
        in codes
    )

    print(
        "REPORT — CONFLITOS PRESERVADOS: OK"
    )


# ============================================================
# 10 — DESTAQUES DE RISCO
# ============================================================


def test_risk_highlights():

    report = build_full_report()

    codes = [
        item.get("code")
        for item in report[
            "risk_highlights"
        ]
    ]

    assert (
        "GLOBAL_KILL_SWITCH_ACTIVE"
        in codes
    )

    assert (
        "GLOBAL_RISK_CRITICAL"
        in codes
    )

    assert (
        "MACRO_RISK_DIVERGENCE"
        in codes
    )

    print(
        "REPORT — DESTAQUES DE RISCO: OK"
    )


# ============================================================
# 11 — DESTAQUES DE OPORTUNIDADE
# ============================================================


def test_opportunity_highlights():

    report = build_full_report()

    codes = [
        item.get("code")
        for item in report[
            "opportunity_highlights"
        ]
    ]

    assert (
        "POSITIVE_ENTRY_EVIDENCE_PRESENT"
        in codes
    )

    assert (
        "OPPORTUNITY_UNDER_GLOBAL_RISK"
        in codes
    )

    print(
        "REPORT — DESTAQUES DE OPORTUNIDADE: OK"
    )


# ============================================================
# 12 — CAMADAS
# ============================================================


def test_system_layers():

    report = build_full_report()

    layers = report["system_layers"]

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
        layers["opportunity_scanners"]
    ) == 2

    print(
        "REPORT — CAMADAS PRESERVADAS: OK"
    )


# ============================================================
# 13 — ORDEM DOS SISTEMAS
# ============================================================


def test_system_order():

    report = build_full_report()

    layers = report["system_layers"]

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
        "REPORT — ORDEM DOS SISTEMAS: OK"
    )


# ============================================================
# 14 — GROWTH
# ============================================================


def test_growth_preserved():

    report = build_full_report()

    growth = report[
        "signals_by_system"
    ]["growth"]

    opportunities = [
        item
        for item in growth
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
        "REPORT — GROWTH PRESERVADO: OK"
    )


# ============================================================
# 15 — AI INFRASTRUCTURE
# ============================================================


def test_ai_infrastructure_preserved():

    report = build_full_report()

    signals = report[
        "signals_by_system"
    ]["ai_infrastructure"]

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
        "REPORT — AI INFRASTRUCTURE PRESERVADO: OK"
    )


# ============================================================
# 16 — AGRUPAMENTO
# ============================================================


def test_signals_grouped():

    report = build_full_report()

    grouped = report[
        "signals_by_system"
    ]

    assert "growth" in grouped

    assert (
        "ai_infrastructure"
        in grouped
    )

    print(
        "REPORT — SINAIS AGRUPADOS: OK"
    )


# ============================================================
# 17 — RASTREABILIDADE
# ============================================================


def test_traceability():

    report = build_full_report()

    traceability = report[
        "traceability"
    ]

    systems = traceability[
        "systems_present"
    ]

    assert (
        traceability["system_count"]
        == 7
    )

    assert (
        "sp500_cycle"
        in systems
    )

    assert (
        "global_portfolio"
        in systems
    )

    assert (
        "us_equities"
        in systems
    )

    assert (
        "b3_equities"
        in systems
    )

    assert "fii" in systems

    assert (
        "ai_infrastructure"
        in systems
    )

    assert "growth" in systems

    print(
        "REPORT — RASTREABILIDADE: OK"
    )


# ============================================================
# 18 — TEXTO EXECUTIVO
# ============================================================


def test_executive_text():

    report = build_full_report()

    text = report[
        "executive_text"
    ]

    assert isinstance(
        text,
        str,
    )

    assert (
        "GLOBAL_RISK_RESTRICTION"
        in text
    )

    assert (
        "RISK_SEEKING"
        in text
    )

    assert (
        "DEFENSIVE"
        in text
    )

    assert (
        "CRITICO"
        in text
    )

    assert (
        "Survival Kill Switch: ATIVO"
        in text
    )

    assert (
        "decisão final permanece humana"
        in text
    )

    print(
        "REPORT — TEXTO EXECUTIVO: OK"
    )


# ============================================================
# 19 — GOVERNANÇA
# ============================================================


def test_governance():

    report = build_full_report()

    governance = report[
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
            "source_decisions_preserved"
        ]
        is True
    )

    assert (
        governance[
            "source_risk_preserved"
        ]
        is True
    )

    assert (
        governance[
            "indicators_recalculated"
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
            "source_decisions_overridden"
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

    print(
        "REPORT — GOVERNANÇA PRESERVADA: OK"
    )


# ============================================================
# 20 — POLÍTICA DO REPORT AGENT
# ============================================================


def test_report_policy():

    report = build_full_report()

    policy = report["policy"]

    assert (
        policy[
            "presentation_layer_only"
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
            "source_decisions_preserved"
        ]
        is True
    )

    assert (
        policy[
            "source_risk_preserved"
        ]
        is True
    )

    assert (
        policy[
            "indicators_recalculated"
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
            "source_decisions_overridden"
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
        "REPORT — POLÍTICA DE SEGURANÇA: OK"
    )


# ============================================================
# 21 — INPUT NÃO ALTERADO
# ============================================================


def test_input_not_mutated():

    decision = build_full_decision()

    before = deepcopy(
        decision
    )

    build_executive_report(
        decision
    )

    assert decision == before

    print(
        "REPORT — INPUT NÃO ALTERADO: OK"
    )


# ============================================================
# 22 — INTERFACE GENÉRICA
# ============================================================


def test_generic_interface():

    decision = build_full_decision()

    direct = build_executive_report(
        decision
    )

    generic = (
        run_executive_report_agent(
            decision
        )
    )

    assert (
        direct["executive_overview"]
        ==
        generic["executive_overview"]
    )

    assert (
        direct["restrictions"]
        ==
        generic["restrictions"]
    )

    assert (
        direct["conflicts"]
        ==
        generic["conflicts"]
    )

    assert (
        direct["source_signals"]
        ==
        generic["source_signals"]
    )

    assert (
        direct["report_summary"]
        ==
        generic["report_summary"]
    )

    print(
        "REPORT — INTERFACE GENÉRICA: OK"
    )


# ============================================================
# 23 — INPUT INVÁLIDO
# ============================================================


def test_invalid_input():

    invalid = {
        "decision_agent_version": "1.0"
    }

    try:

        build_executive_report(
            invalid
        )

    except InvalidExecutiveReportInputError:

        print(
            "REPORT — PROTEÇÃO INPUT INVÁLIDO: OK"
        )

        return

    raise AssertionError(
        "Executive Report Agent deveria "
        "rejeitar Decision incompleto."
    )


# ============================================================
# 24 — COMPATIBILIDADE COM DOIS MOTORES
# ============================================================


def test_two_base_compatibility():

    report = build_two_base_report()

    assert (
        report["status"]
        == "WARNING"
    )

    assert (
        report[
            "executive_overview"
        ]["operational_state"]
        == "GLOBAL_RISK_RESTRICTION"
    )

    assert (
        report[
            "system_layers"
        ]["asset_selection"]
        == []
    )

    assert (
        report[
            "system_layers"
        ]["opportunity_scanners"]
        == []
    )

    assert (
        report[
            "traceability"
        ]["system_count"]
        == 2
    )

    print(
        "REPORT — COMPATIBILIDADE DOIS MOTORES: OK"
    )


# ============================================================
# 25 — DECISÃO HUMANA
# ============================================================


def test_human_decision_required():

    report = build_full_report()

    assert (
        report[
            "policy"
        ][
            "human_decision_required"
        ]
        is True
    )

    assert (
        report[
            "policy"
        ][
            "broker_execution_allowed"
        ]
        is False
    )

    assert (
        report[
            "policy"
        ][
            "recommendation_created"
        ]
        is False
    )

    print(
        "REPORT — DECISÃO HUMANA OBRIGATÓRIA: OK"
    )


# ============================================================
# 26 — RESUMO DO RELATÓRIO
# ============================================================


def test_report_summary():

    report = build_full_report()

    summary = report[
        "report_summary"
    ]

    assert (
        summary["status"]
        == "WARNING"
    )

    assert (
        summary["operational_state"]
        == "GLOBAL_RISK_RESTRICTION"
    )

    assert (
        summary["governance_state"]
        == "HARD_RESTRICTION_PRESENT"
    )

    assert (
        summary["global_kill_switch"]
        is True
    )

    assert (
        summary["restriction_count"]
        >= 4
    )

    assert (
        summary["conflict_count"]
        >= 2
    )

    assert (
        summary["system_count"]
        == 7
    )

    print(
        "REPORT — RESUMO DO RELATÓRIO: OK"
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
        "TESTE — EXECUTIVE REPORT AGENT V1"
    )

    print("=" * 70)

    test_identification()

    test_status()

    test_header()

    test_macro_context()

    test_global_risk()

    test_kill_switch()

    test_operational_state()

    test_restrictions()

    test_conflicts()

    test_risk_highlights()

    test_opportunity_highlights()

    test_system_layers()

    test_system_order()

    test_growth_preserved()

    test_ai_infrastructure_preserved()

    test_signals_grouped()

    test_traceability()

    test_executive_text()

    test_governance()

    test_report_policy()

    test_input_not_mutated()

    test_generic_interface()

    test_invalid_input()

    test_two_base_compatibility()

    test_human_decision_required()

    test_report_summary()

    print("=" * 70)

    print(
        "EXECUTIVE REPORT AGENT V1 — "
        "26 TESTES OK"
    )

    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
