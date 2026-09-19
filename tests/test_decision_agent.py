# ============================================================
# INVESTMENT CIO AGENT
# tests/test_decision_agent.py
# ============================================================
#
# Testes oficiais do Decision Agent V1.
#
# Objetivos:
# - validar integração Synthesis V2 + Risk V1;
# - preservar decisões e sinais dos motores;
# - detectar divergência macro/risco;
# - detectar oportunidade sob restrição global;
# - garantir que Kill Switch permaneça visível;
# - garantir que nenhum score novo seja criado;
# - garantir que não exista execução automática;
# - garantir decisão humana obrigatória.
#
# ============================================================

from copy import deepcopy

from agents.synthesis_agent import synthesize_outputs
from agents.risk_agent import assess_risk

from agents.decision_agent import (
    DECISION_AGENT_VERSION,
    InvalidDecisionInputError,
    build_decision,
    run_decision_agent,
)

from tests.test_synthesis_agent import (
    build_all_outputs,
    build_sp500_output,
    build_global_output,
)


# ============================================================
# BUILDERS
# ============================================================


def build_full_synthesis():
    return synthesize_outputs(
        build_all_outputs()
    )


def build_full_risk():
    synthesis = build_full_synthesis()

    return assess_risk(
        synthesis
    )


def build_full_decision():
    synthesis = build_full_synthesis()

    risk = assess_risk(
        synthesis
    )

    return build_decision(
        synthesis,
        risk,
    )


def build_two_base_synthesis():
    return synthesize_outputs([
        build_sp500_output(),
        build_global_output(),
    ])


def build_two_base_decision():
    synthesis = (
        build_two_base_synthesis()
    )

    risk = assess_risk(
        synthesis
    )

    return build_decision(
        synthesis,
        risk,
    )


# ============================================================
# 1 — IDENTIFICAÇÃO
# ============================================================


def test_identification():

    result = build_full_decision()

    assert (
        result[
            "decision_agent_version"
        ]
        == DECISION_AGENT_VERSION
    )

    assert (
        result[
            "decision_agent_version"
        ]
        == "1.0"
    )

    assert (
        result[
            "source_versions"
        ]["synthesis_agent"]
        == "2.0"
    )

    assert (
        result[
            "source_versions"
        ]["risk_agent"]
        == "1.0"
    )

    print(
        "DECISION — IDENTIFICAÇÃO: OK"
    )


# ============================================================
# 2 — STATUS
# ============================================================


def test_status_preserved():

    result = build_full_decision()

    assert result["status"] == "WARNING"

    print(
        "DECISION — STATUS WARNING: OK"
    )


# ============================================================
# 3 — CONTEXTO MACRO
# ============================================================


def test_macro_context():

    result = build_full_decision()

    macro = result[
        "macro_context"
    ]

    assert (
        macro["sp500_stance"]
        == "RISK_SEEKING"
    )

    assert (
        macro["global_stance"]
        == "DEFENSIVE"
    )

    assert (
        macro["relationship"]
        == "DIVERGENCE"
    )

    print(
        "DECISION — CONTEXTO MACRO: OK"
    )


# ============================================================
# 4 — KILL SWITCH PRESERVADO
# ============================================================


def test_kill_switch_preserved():

    result = build_full_decision()

    global_risk = (
        result[
            "risk_context"
        ]["global_risk"]
    )

    assert (
        global_risk[
            "global_kill_switch"
        ]
        is True
    )

    print(
        "DECISION — KILL SWITCH PRESERVADO: OK"
    )


# ============================================================
# 5 — RISCO CRÍTICO PRESERVADO
# ============================================================


def test_critical_risk_preserved():

    result = build_full_decision()

    global_risk = (
        result[
            "risk_context"
        ]["global_risk"]
    )

    assert (
        global_risk[
            "global_risk_level"
        ]
        == "CRITICO"
    )

    print(
        "DECISION — RISCO CRÍTICO PRESERVADO: OK"
    )


# ============================================================
# 6 — RESTRIÇÕES PRESERVADAS
# ============================================================


def test_restrictions_preserved():

    result = build_full_decision()

    restrictions = (
        result[
            "risk_context"
        ]["restrictions"]
    )

    codes = [
        item.get("code")
        for item in restrictions
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
        "DECISION — RESTRIÇÕES PRESERVADAS: OK"
    )


# ============================================================
# 7 — ESTADO OPERACIONAL
# ============================================================


def test_operational_context():

    result = build_full_decision()

    operational = result[
        "operational_context"
    ]

    assert (
        operational["state"]
        == "GLOBAL_RISK_RESTRICTION"
    )

    assert (
        operational["governance"]
        == "HARD_RESTRICTION_PRESENT"
    )

    assert (
        operational[
            "has_positive_entry_evidence"
        ]
        is True
    )

    print(
        "DECISION — CONTEXTO OPERACIONAL: OK"
    )


# ============================================================
# 8 — CONFLITO MACRO/RISCO
# ============================================================


def test_macro_risk_conflict():

    result = build_full_decision()

    conflict_codes = [
        item.get("code")
        for item in result[
            "conflicts"
        ]
    ]

    assert (
        "REGIME_GLOBAL_RISK_DIVERGENCE"
        in conflict_codes
    )

    print(
        "DECISION — DIVERGÊNCIA MACRO/RISCO: OK"
    )


# ============================================================
# 9 — OPORTUNIDADE VS RISCO
# ============================================================


def test_opportunity_vs_risk_conflict():

    result = build_full_decision()

    conflict_codes = [
        item.get("code")
        for item in result[
            "conflicts"
        ]
    ]

    assert (
        "OPPORTUNITY_VS_GLOBAL_RISK"
        in conflict_codes
    )

    print(
        "DECISION — OPORTUNIDADE VS RISCO: OK"
    )


# ============================================================
# 10 — CAMADAS
# ============================================================


def test_layers():

    result = build_full_decision()

    layers = result["layers"]

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
        "DECISION — CAMADAS PRESERVADAS: OK"
    )


# ============================================================
# 11 — SISTEMAS DE SELEÇÃO
# ============================================================


def test_asset_selection_order():

    result = build_full_decision()

    systems = [
        item["system_id"]
        for item in (
            result[
                "layers"
            ]["asset_selection"]
        )
    ]

    assert systems == [
        "us_equities",
        "b3_equities",
        "fii",
    ]

    print(
        "DECISION — SELEÇÃO DE ATIVOS PRESERVADA: OK"
    )


# ============================================================
# 12 — SCANNERS
# ============================================================


def test_scanner_order():

    result = build_full_decision()

    systems = [
        item["system_id"]
        for item in (
            result[
                "layers"
            ][
                "opportunity_scanners"
            ]
        )
    ]

    assert systems == [
        "ai_infrastructure",
        "growth",
    ]

    print(
        "DECISION — SCANNERS PRESERVADOS: OK"
    )


# ============================================================
# 13 — GROWTH PRESERVADO
# ============================================================


def test_growth_preserved():

    result = build_full_decision()

    growth_signals = [
        item
        for item in result[
            "source_signals"
        ]
        if (
            item.get("system_id")
            == "growth"
            and
            item.get("scope")
            == "OPPORTUNITY"
        )
    ]

    assert [
        item["ticker"]
        for item in growth_signals
    ] == [
        "HOOD",
        "UBER",
        "XYZ",
    ]

    assert [
        item["signal"]
        for item in growth_signals
    ] == [
        "ENTRADA_FORTE",
        "ENTRADA_FORTE",
        "AGUARDAR",
    ]

    print(
        "DECISION — GROWTH PRESERVADO: OK"
    )


# ============================================================
# 14 — AI INFRASTRUCTURE PRESERVADO
# ============================================================


def test_ai_infrastructure_preserved():

    result = build_full_decision()

    signals = [
        item
        for item in result[
            "source_signals"
        ]
        if (
            item.get("system_id")
            == "ai_infrastructure"
            and
            item.get("scope")
            == "OPPORTUNITY"
        )
    ]

    assert [
        item["ticker"]
        for item in signals
    ] == [
        "PANW",
        "MSFT",
    ]

    assert [
        item["signal"]
        for item in signals
    ] == [
        "OBSERVAÇÃO PRIORITÁRIA",
        "AGUARDAR PULLBACK",
    ]

    print(
        "DECISION — AI INFRASTRUCTURE PRESERVADO: OK"
    )


# ============================================================
# 15 — INPUT NÃO ALTERADO
# ============================================================


def test_inputs_not_mutated():

    synthesis = build_full_synthesis()

    risk = assess_risk(
        synthesis
    )

    synthesis_before = deepcopy(
        synthesis
    )

    risk_before = deepcopy(
        risk
    )

    build_decision(
        synthesis,
        risk,
    )

    assert (
        synthesis
        == synthesis_before
    )

    assert (
        risk
        == risk_before
    )

    print(
        "DECISION — INPUTS NÃO ALTERADOS: OK"
    )


# ============================================================
# 16 — POLÍTICA DE SEGURANÇA
# ============================================================


def test_policy():

    result = build_full_decision()

    policy = result["policy"]

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
            "selection_systems_used_as_macro_votes"
        ]
        is False
    )

    assert (
        policy[
            "opportunity_systems_used_as_macro_votes"
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
        "DECISION — POLÍTICA DE SEGURANÇA: OK"
    )


# ============================================================
# 17 — RESUMO EXECUTIVO
# ============================================================


def test_summary():

    result = build_full_decision()

    summary = result["summary"]

    assert (
        summary["operational_state"]
        == "GLOBAL_RISK_RESTRICTION"
    )

    assert (
        summary["governance_state"]
        == "HARD_RESTRICTION_PRESENT"
    )

    assert (
        summary[
            "asset_selection_systems"
        ]
        == 3
    )

    assert (
        summary[
            "opportunity_scanners"
        ]
        == 2
    )

    assert (
        summary["conflict_count"]
        >= 2
    )

    print(
        "DECISION — RESUMO EXECUTIVO: OK"
    )


# ============================================================
# 18 — INTERFACE GENÉRICA
# ============================================================


def test_generic_interface():

    synthesis = build_full_synthesis()

    risk = assess_risk(
        synthesis
    )

    direct = build_decision(
        synthesis,
        risk,
    )

    generic = run_decision_agent(
        synthesis,
        risk,
    )

    assert (
        direct[
            "operational_context"
        ]
        ==
        generic[
            "operational_context"
        ]
    )

    assert (
        direct["conflicts"]
        ==
        generic["conflicts"]
    )

    assert (
        direct["summary"]
        ==
        generic["summary"]
    )

    print(
        "DECISION — INTERFACE GENÉRICA: OK"
    )


# ============================================================
# 19 — SYNTHESIS INVÁLIDO
# ============================================================


def test_invalid_synthesis():

    synthesis = {
        "synthesis_version": "2.0"
    }

    risk = build_full_risk()

    try:

        build_decision(
            synthesis,
            risk,
        )

    except InvalidDecisionInputError:

        print(
            "DECISION — PROTEÇÃO SYNTHESIS INVÁLIDO: OK"
        )

        return

    raise AssertionError(
        "Decision Agent deveria rejeitar "
        "Synthesis incompleto."
    )


# ============================================================
# 20 — RISK INVÁLIDO
# ============================================================


def test_invalid_risk():

    synthesis = build_full_synthesis()

    risk = {
        "risk_agent_version": "1.0"
    }

    try:

        build_decision(
            synthesis,
            risk,
        )

    except InvalidDecisionInputError:

        print(
            "DECISION — PROTEÇÃO RISK INVÁLIDO: OK"
        )

        return

    raise AssertionError(
        "Decision Agent deveria rejeitar "
        "Risk assessment incompleto."
    )


# ============================================================
# 21 — COMPATIBILIDADE COM OS DOIS MOTORES BASE
# ============================================================


def test_two_base_system_compatibility():

    result = (
        build_two_base_decision()
    )

    assert (
        result["status"]
        == "WARNING"
    )

    assert (
        result[
            "operational_context"
        ]["state"]
        == "GLOBAL_RISK_RESTRICTION"
    )

    assert (
        result[
            "layers"
        ]["asset_selection"]
        == []
    )

    assert (
        result[
            "layers"
        ]["opportunity_scanners"]
        == []
    )

    print(
        "DECISION — COMPATIBILIDADE DOIS MOTORES: OK"
    )


# ============================================================
# 22 — DECISÃO HUMANA
# ============================================================


def test_human_decision_required():

    result = build_full_decision()

    assert (
        result[
            "policy"
        ][
            "human_decision_required"
        ]
        is True
    )

    assert (
        result[
            "policy"
        ][
            "broker_execution_allowed"
        ]
        is False
    )

    assert (
        result[
            "policy"
        ][
            "automatic_trade_decision_created"
        ]
        is False
    )

    print(
        "DECISION — DECISÃO HUMANA OBRIGATÓRIA: OK"
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
        "TESTE — DECISION AGENT V1"
    )

    print("=" * 70)

    test_identification()

    test_status_preserved()

    test_macro_context()

    test_kill_switch_preserved()

    test_critical_risk_preserved()

    test_restrictions_preserved()

    test_operational_context()

    test_macro_risk_conflict()

    test_opportunity_vs_risk_conflict()

    test_layers()

    test_asset_selection_order()

    test_scanner_order()

    test_growth_preserved()

    test_ai_infrastructure_preserved()

    test_inputs_not_mutated()

    test_policy()

    test_summary()

    test_generic_interface()

    test_invalid_synthesis()

    test_invalid_risk()

    test_two_base_system_compatibility()

    test_human_decision_required()

    print("=" * 70)

    print(
        "DECISION AGENT V1 — 22 TESTES OK"
    )

    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
