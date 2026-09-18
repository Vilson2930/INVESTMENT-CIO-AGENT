# ============================================================
# INVESTMENT CIO AGENT
# tests/test_synthesis_agent.py
# ============================================================
#
# Teste oficial da camada de síntese.
#
# Verifica:
# 1. Preservação das decisões originais.
# 2. Identificação de divergência.
# 3. Consolidação dos riscos.
# 4. Preservação das auditorias.
# 5. Política de não sobrescrever os robôs.
# 6. Interface genérica de síntese.
#
# ============================================================

from agents.synthesis_agent import (
    build_synthesis,
    synthesize_outputs,
    SynthesisError,
)


# ============================================================
# SP500 CYCLE ATLAS
# ============================================================

def build_sp500_output():

    return {
        "schema_version": "1.0",
        "system_id": "sp500_cycle",
        "system_name": "SP500_CYCLE_ATLAS",
        "generated_at": "2026-09-17T22:00:00+00:00",
        "status": "WARNING",

        "decision": {
            "signal": "HOLD",
            "confidence": 0.92,
            "summary": "Mercado em alta com valuation elevado.",
            "operational_regime": "YELLOW_EXPENSIVE_BULL",
            "new_contribution_equity": 0.60,
            "new_contribution_reserve": 0.40,
        },

        "metrics": {
            "operational_regime": "YELLOW_EXPENSIVE_BULL",
        },

        "risk": {
            "level": "HIGH",
            "score": None,
            "alerts": [
                "Valuation historicamente elevado."
            ],
        },

        "data_quality": {
            "score": 78.0,
            "missing_fields": [],
            "warnings": [],
        },

        "audit": {
            "audit_status": "CONFIRMED_WITH_WARNINGS",
            "engine_consistency_score": 92.0,
            "data_quality_score": 78.0,
            "ai_dissent": False,
        },
    }


# ============================================================
# COPIAULTIMOROB
# ============================================================

def build_global_output():

    return {
        "schema_version": "1.0",
        "system_id": "global_portfolio",
        "system_name": "COPIAULTIMOROB",
        "generated_at": "2026-09-17T22:00:00+00:00",
        "status": "WARNING",

        "decision": {
            "signal": "NEUTRO",
            "confidence": 0.0,
            "summary": "Risco operacional elevado.",
        },

        "metrics": {
            "macro_regime": "NEUTRO",
            "final_verdict": "REPROVADO_OPERACIONALMENTE",
            "committee_action": "BLOQUEAR_NOVAS_COMPRAS",
            "integrated_risk_level": "CRITICO",
            "survival_status": "REPROVADO_OPERACIONALMENTE",
            "survival_kill_switch": True,
            "stress_level": "CRITICO",
            "risk_budget_level": "CRITICO",
        },

        "risk": {
            "level": "CRITICO",
            "score": 100.0,
            "alerts": [
                "Survival Kill Switch ativo.",
                "Risco de ruína: ALTO",
            ],
        },

        "data_quality": {
            "score": None,
            "missing_fields": [],
            "warnings": [],
        },

        "audit": {
            "ai_audit_status": "CONFIRMADO_COM_ALERTAS",
            "ai_audit_score": 90.0,
            "nvidia_audit_status": "CONFIRMED_WITH_WARNINGS",
            "nvidia_audit_score": 90.0,
        },
    }


# ============================================================
# TESTE — SÍNTESE PRINCIPAL
# ============================================================

def test_build_synthesis():

    sp500 = build_sp500_output()
    global_portfolio = build_global_output()

    result = build_synthesis(
        sp500,
        global_portfolio,
    )

    assert result["synthesis_version"] == "1.0"

    assert result["systems_analyzed"] == [
        "SP500_CYCLE_ATLAS",
        "COPIAULTIMOROB",
    ]

    print("OK - sistemas identificados")


# ============================================================
# TESTE — PRESERVAÇÃO DAS DECISÕES
# ============================================================

def test_preserves_source_decisions():

    result = build_synthesis(
        build_sp500_output(),
        build_global_output(),
    )

    assert (
        result["source_decisions"]
        ["SP500_CYCLE_ATLAS"]
        ["signal"]
        == "HOLD"
    )

    assert (
        result["source_decisions"]
        ["SP500_CYCLE_ATLAS"]
        ["new_contribution_equity"]
        == 0.60
    )

    assert (
        result["source_decisions"]
        ["SP500_CYCLE_ATLAS"]
        ["new_contribution_reserve"]
        == 0.40
    )

    assert (
        result["source_decisions"]
        ["COPIAULTIMOROB"]
        ["signal"]
        == "NEUTRO"
    )

    assert (
        result["source_decisions"]
        ["COPIAULTIMOROB"]
        ["final_verdict"]
        == "REPROVADO_OPERACIONALMENTE"
    )

    assert (
        result["source_decisions"]
        ["COPIAULTIMOROB"]
        ["committee_action"]
        == "BLOQUEAR_NOVAS_COMPRAS"
    )

    print("OK - decisões originais preservadas")


# ============================================================
# TESTE — DIVERGÊNCIA
# ============================================================

def test_detects_divergence():

    result = build_synthesis(
        build_sp500_output(),
        build_global_output(),
    )

    assert (
        result["comparison"]["sp500_stance"]
        == "RISK_SEEKING"
    )

    assert (
        result["comparison"]["global_stance"]
        == "DEFENSIVE"
    )

    assert (
        result["comparison"]["relationship"]
        == "DIVERGENCE"
    )

    print("OK - divergência detectada")


# ============================================================
# TESTE — RISCO
# ============================================================

def test_consolidates_risk():

    result = build_synthesis(
        build_sp500_output(),
        build_global_output(),
    )

    assert (
        result["risk"]["sp500_risk_level"]
        == "HIGH"
    )

    assert (
        result["risk"]["global_risk_level"]
        == "CRITICO"
    )

    assert (
        result["risk"]["global_kill_switch"]
        is True
    )

    assert len(
        result["risk"]["alerts"]
    ) > 0

    print("OK - riscos consolidados")


# ============================================================
# TESTE — AUDITORIAS
# ============================================================

def test_preserves_audits():

    result = build_synthesis(
        build_sp500_output(),
        build_global_output(),
    )

    assert (
        result["audit"]["sp500"]
        ["engine_consistency_score"]
        == 92.0
    )

    assert (
        result["audit"]["sp500"]
        ["data_quality_score"]
        == 78.0
    )

    assert (
        result["audit"]["copiaultimorob"]
        ["ai_audit_score"]
        == 90.0
    )

    assert (
        result["audit"]["copiaultimorob"]
        ["nvidia_audit_score"]
        == 90.0
    )

    print("OK - auditorias preservadas")


# ============================================================
# TESTE — POLÍTICA DE SEGURANÇA
# ============================================================

def test_policy():

    result = build_synthesis(
        build_sp500_output(),
        build_global_output(),
    )

    policy = result["policy"]

    assert policy["signals_preserved"] is True

    assert (
        policy["indicators_recalculated"]
        is False
    )

    assert (
        policy["source_decisions_overridden"]
        is False
    )

    assert (
        policy["broker_execution_allowed"]
        is False
    )

    assert (
        policy["human_decision_required"]
        is True
    )

    print("OK - política de segurança preservada")


# ============================================================
# TESTE — INTERFACE GENÉRICA
# ============================================================

def test_generic_interface():

    outputs = [
        build_global_output(),
        build_sp500_output(),
    ]

    result = synthesize_outputs(
        outputs
    )

    assert (
        result["comparison"]["relationship"]
        == "DIVERGENCE"
    )

    print("OK - interface genérica funcionando")


# ============================================================
# TESTE — SISTEMA AUSENTE
# ============================================================

def test_missing_system():

    outputs = [
        build_sp500_output(),
    ]

    try:

        synthesize_outputs(
            outputs
        )

    except SynthesisError:

        print(
            "OK - ausência de sistema detectada"
        )

        return

    raise AssertionError(
        "A síntese deveria rejeitar "
        "a ausência do COPIAULTIMOROB."
    )


# ============================================================
# EXECUÇÃO
# ============================================================

def run_all_tests():

    print("=" * 70)
    print("INVESTMENT CIO AGENT")
    print("TESTE — SYNTHESIS AGENT")
    print("=" * 70)

    test_build_synthesis()

    test_preserves_source_decisions()

    test_detects_divergence()

    test_consolidates_risk()

    test_preserves_audits()

    test_policy()

    test_generic_interface()

    test_missing_system()

    print("=" * 70)
    print(
        "TODOS OS TESTES DO SYNTHESIS AGENT PASSARAM"
    )
    print("=" * 70)


if __name__ == "__main__":

    run_all_tests()
