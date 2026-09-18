# ============================================================
# INVESTMENT CIO AGENT
# tests/test_risk_agent.py
# ============================================================
#
# Teste oficial da camada central de risco.
#
# Verifica:
# 1. Identificação do Risk Agent.
# 2. Preservação do risco global.
# 3. Detecção do Survival Kill Switch.
# 4. Detecção de risco crítico.
# 5. Detecção de postura defensiva.
# 6. Detecção de divergência macro/risco.
# 7. Preservação dos sinais dos motores.
# 8. Preservação da ordem das oportunidades.
# 9. Coexistência entre oportunidade e restrição.
# 10. Ausência de recálculo, override e execução.
#
# ============================================================

from agents.synthesis_agent import synthesize_outputs
from agents.risk_agent import (
    assess_risk,
    run_risk_agent,
    InvalidSynthesisError,
)

from tests.test_synthesis_agent import (
    build_all_outputs,
    build_sp500_output,
    build_global_output,
)


def build_synthesis():
    return synthesize_outputs(
        build_all_outputs()
    )


def test_identification():
    result = assess_risk(
        build_synthesis()
    )

    assert result["risk_agent_version"] == "1.0"
    assert result["source_synthesis_version"] == "2.0"

    print("RISK — IDENTIFICAÇÃO: OK")


def test_global_risk_preserved():
    result = assess_risk(
        build_synthesis()
    )

    global_risk = result["global_risk"]

    assert global_risk["sp500_risk_level"] == "HIGH"
    assert global_risk["global_risk_level"] == "CRITICO"
    assert global_risk["global_survival_status"] == (
        "REPROVADO_OPERACIONALMENTE"
    )
    assert global_risk["global_kill_switch"] is True

    print("RISK — RISCO GLOBAL PRESERVADO: OK")


def test_kill_switch_restriction():
    result = assess_risk(
        build_synthesis()
    )

    assert "GLOBAL_KILL_SWITCH_ACTIVE" in (
        result["restriction_codes"]
    )

    print("RISK — KILL SWITCH: OK")


def test_critical_risk_restriction():
    result = assess_risk(
        build_synthesis()
    )

    assert "GLOBAL_RISK_CRITICAL" in (
        result["restriction_codes"]
    )

    print("RISK — RISCO CRÍTICO: OK")


def test_defensive_stance_restriction():
    result = assess_risk(
        build_synthesis()
    )

    assert "GLOBAL_DEFENSIVE_STANCE" in (
        result["restriction_codes"]
    )

    print("RISK — POSTURA DEFENSIVA: OK")


def test_divergence_restriction():
    result = assess_risk(
        build_synthesis()
    )

    assert "MACRO_RISK_DIVERGENCE" in (
        result["restriction_codes"]
    )

    print("RISK — DIVERGÊNCIA: OK")


def test_warning_status():
    result = assess_risk(
        build_synthesis()
    )

    assert result["status"] == "WARNING"

    print("RISK — STATUS WARNING: OK")


def test_asset_selection_evidence():
    result = assess_risk(
        build_synthesis()
    )

    evidence = result["evidence"]

    assert len(evidence["asset_selection"]) == 3

    ids = [
        item["system_id"]
        for item in evidence["asset_selection"]
    ]

    assert ids == [
        "us_equities",
        "b3_equities",
        "fii",
    ]

    print("RISK — SELEÇÃO DE ATIVOS PRESERVADA: OK")


def test_opportunity_evidence():
    result = assess_risk(
        build_synthesis()
    )

    evidence = result["evidence"]

    assert len(
        evidence["opportunity_scanners"]
    ) == 2

    ids = [
        item["system_id"]
        for item in evidence["opportunity_scanners"]
    ]

    assert ids == [
        "ai_infrastructure",
        "growth",
    ]

    print("RISK — SCANNERS PRESERVADOS: OK")


def test_growth_signals_preserved():
    result = assess_risk(
        build_synthesis()
    )

    growth_signals = [
        item
        for item in result["source_signals"]
        if item.get("system_id") == "growth"
        and item.get("scope") == "OPPORTUNITY"
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

    print("RISK — GROWTH PRESERVADO: OK")


def test_ai_order_preserved():
    result = assess_risk(
        build_synthesis()
    )

    ai_signals = [
        item
        for item in result["source_signals"]
        if item.get("system_id") == "ai_infrastructure"
        and item.get("scope") == "OPPORTUNITY"
    ]

    assert [
        item["ticker"]
        for item in ai_signals
    ] == [
        "PANW",
        "MSFT",
    ]

    assert [
        item["signal"]
        for item in ai_signals
    ] == [
        "OBSERVAÇÃO PRIORITÁRIA",
        "AGUARDAR PULLBACK",
    ]

    print("RISK — ORDEM AI INFRASTRUCTURE PRESERVADA: OK")


def test_opportunity_under_risk_restriction():
    result = assess_risk(
        build_synthesis()
    )

    context = result[
        "risk_opportunity_context"
    ]

    assert context["state"] == (
        "OPPORTUNITY_UNDER_RISK_RESTRICTION"
    )
    assert context[
        "has_global_restrictions"
    ] is True
    assert context[
        "has_positive_entry_evidence"
    ] is True

    print("RISK — OPORTUNIDADE SOB RESTRIÇÃO: OK")


def test_source_signals_not_changed():
    synthesis = build_synthesis()

    before_growth = synthesis[
        "layers"
    ]["OPPORTUNITY_SCANNER"][1][
        "opportunities"
    ]

    before = [
        (
            item.get("ticker"),
            item.get("signal"),
        )
        for item in before_growth
    ]

    assess_risk(synthesis)

    after_growth = synthesis[
        "layers"
    ]["OPPORTUNITY_SCANNER"][1][
        "opportunities"
    ]

    after = [
        (
            item.get("ticker"),
            item.get("signal"),
        )
        for item in after_growth
    ]

    assert before == after

    print("RISK — SINAIS NÃO ALTERADOS: OK")


def test_policy():
    result = assess_risk(
        build_synthesis()
    )

    policy = result["policy"]

    assert policy["source_signals_preserved"] is True
    assert policy["source_order_preserved"] is True
    assert policy["indicators_recalculated"] is False
    assert policy["new_quantitative_score_created"] is False
    assert policy["source_decisions_overridden"] is False
    assert (
        policy["risk_restrictions_change_source_signals"]
        is False
    )
    assert (
        policy["selection_systems_used_as_macro_votes"]
        is False
    )
    assert (
        policy["opportunity_systems_used_as_macro_votes"]
        is False
    )
    assert policy["broker_execution_allowed"] is False
    assert policy["human_decision_required"] is True

    print("RISK — POLÍTICA DE SEGURANÇA: OK")


def test_generic_interface():
    synthesis = build_synthesis()

    direct = assess_risk(synthesis)
    generic = run_risk_agent(synthesis)

    assert (
        direct["restriction_codes"]
        == generic["restriction_codes"]
    )

    assert (
        direct["risk_opportunity_context"]["state"]
        == generic["risk_opportunity_context"]["state"]
    )

    print("RISK — INTERFACE GENÉRICA: OK")


def test_invalid_synthesis():
    try:
        assess_risk({
            "synthesis_version": "2.0",
        })
    except InvalidSynthesisError:
        print("RISK — PROTEÇÃO SÍNTESE INVÁLIDA: OK")
        return

    raise AssertionError(
        "Risk Agent deveria rejeitar "
        "síntese incompleta."
    )


def test_two_base_system_compatibility():
    synthesis = synthesize_outputs([
        build_sp500_output(),
        build_global_output(),
    ])

    result = assess_risk(
        synthesis
    )

    assert result["status"] == "WARNING"
    assert result["evidence"]["asset_selection"] == []
    assert result["evidence"]["opportunity_scanners"] == []
    assert "GLOBAL_KILL_SWITCH_ACTIVE" in (
        result["restriction_codes"]
    )

    print("RISK — COMPATIBILIDADE DOIS MOTORES: OK")


def run_all_tests():
    print("=" * 70)
    print("INVESTMENT CIO AGENT")
    print("TESTE — RISK AGENT")
    print("=" * 70)

    test_identification()
    test_global_risk_preserved()
    test_kill_switch_restriction()
    test_critical_risk_restriction()
    test_defensive_stance_restriction()
    test_divergence_restriction()
    test_warning_status()
    test_asset_selection_evidence()
    test_opportunity_evidence()
    test_growth_signals_preserved()
    test_ai_order_preserved()
    test_opportunity_under_risk_restriction()
    test_source_signals_not_changed()
    test_policy()
    test_generic_interface()
    test_invalid_synthesis()
    test_two_base_system_compatibility()

    print("=" * 70)
    print("RISK AGENT — 17 TESTES OK")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
