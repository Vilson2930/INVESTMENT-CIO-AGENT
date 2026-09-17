from adapters.copiaultimorob_adapter import build_copiaultimorob_agent_output
from agents.validator import validate_agent_output


def build_realistic_payload():
    """
    Payload representativo de uma execução real do COPIAULTIMOROB.

    O objetivo deste teste é verificar se o adaptador:
    1. identifica corretamente o sistema;
    2. preserva a decisão original do robô;
    3. transporta os principais indicadores de risco;
    4. não altera o sinal quantitativo;
    5. produz saída compatível com o schema universal do CIO Agent.
    """

    return {
        "source_system": "COPIAULTIMOROB",
        "export_version": "1.0",
        "generated_at": "2026-09-17T22:00:00+00:00",

        "macro": {
            "regime": "NEUTRO",
            "sinal_operacional": "NEUTRO",
            "macro_conviction": 0.0,
            "confidence_score": 0.0,
        },

        "portfolio": {
            "total_value": 100000.0,
            "gross_turnover_final": 0.0,
            "turnover_status": "OK",
            "kill_switch": False,
        },

        "allocation": {
            "allocation_alignment_score": 0.0,
            "allocation_alignment_level": "DESALINHADO",
            "total_model_drift_pct": 0.0,
            "top_gap_asset": "N/D",
            "top_gap_abs_pct": 0.0,
        },

        "survival": {
            "survival_status": "REPROVADO_OPERACIONALMENTE",
            "ruin_risk": "ALTO",
            "survival_kill_switch": True,
        },

        "stress": {
            "stress_level": "CRITICO",
            "stress_score": 100.0,
            "max_drawdown_pct": -50.0,
            "forced_selling_any": True,
        },

        "risk_budget": {
            "risk_budget_level": "CRITICO",
            "risk_budget_score": 100.0,
            "top_risk_asset": "BTC",
            "max_risk_contribution_pct": 50.0,
        },

        "liquidity": {
            "liquidity_level": "OK",
            "liquidity_score": 100.0,
            "aggregate_haircut_pct": 0.0,
        },

        "counterparty": {
            "counterparty_level": "OK",
            "counterparty_score": 100.0,
            "largest_counterparty": "N/D",
        },

        "governance": {
            "integrated_risk_level": "CRITICO",
            "committee_action": "BLOQUEAR_NOVAS_COMPRAS",
            "final_verdict": "REPROVADO_OPERACIONALMENTE",
        },

        "ai_audit": {
            "ai_audit_status": "CONFIRMADO_COM_ALERTAS",
            "ai_audit_score": 90.0,
            "root_cause": "RISCO_OPERACIONAL_ELEVADO",
        },

        "nvidia_audit": {
            "openai_audit_status": "CONFIRMED_WITH_WARNINGS",
            "audit_verdict": "CONSISTENT_WITH_WARNINGS",
            "audit_score": 90.0,
            "audit_confidence": 0.90,
            "severity": "HIGH",
            "root_cause": "RISK_CONCENTRATION",
            "final_opinion": (
                "O engine permanece internamente consistente, "
                "mas apresenta alertas relevantes de risco."
            ),
        },
    }


def test_adapter_identity():
    payload = build_realistic_payload()

    output = build_copiaultimorob_agent_output(payload)

    assert output["system_id"] == "global_portfolio"
    assert output["system_name"] == "COPIAULTIMOROB"

    print("OK - identidade do COPIAULTIMOROB preservada")


def test_adapter_preserves_original_signal():
    payload = build_realistic_payload()

    output = build_copiaultimorob_agent_output(payload)

    assert output["decision"]["signal"] == "NEUTRO"

    print("OK - sinal original NEUTRO preservado")


def test_adapter_preserves_final_verdict():
    payload = build_realistic_payload()

    output = build_copiaultimorob_agent_output(payload)

    assert (
        output["metrics"]["final_verdict"]
        == "REPROVADO_OPERACIONALMENTE"
    )

    print("OK - veredito operacional preservado")


def test_adapter_survival_risk():
    payload = build_realistic_payload()

    output = build_copiaultimorob_agent_output(payload)

    assert (
        output["metrics"]["survival_status"]
        == "REPROVADO_OPERACIONALMENTE"
    )

    assert output["metrics"]["survival_kill_switch"] is True

    print("OK - survival risk preservado")


def test_adapter_stress():
    payload = build_realistic_payload()

    output = build_copiaultimorob_agent_output(payload)

    assert output["metrics"]["stress_level"] == "CRITICO"
    assert output["metrics"]["forced_selling_any"] is True

    print("OK - stress engine preservado")


def test_adapter_risk_budget():
    payload = build_realistic_payload()

    output = build_copiaultimorob_agent_output(payload)

    assert output["metrics"]["risk_budget_level"] == "CRITICO"
    assert output["metrics"]["top_risk_asset"] == "BTC"

    print("OK - risk budget preservado")


def test_adapter_governance():
    payload = build_realistic_payload()

    output = build_copiaultimorob_agent_output(payload)

    assert output["risk"]["level"] == "CRITICO"

    assert (
        output["metrics"]["committee_action"]
        == "BLOQUEAR_NOVAS_COMPRAS"
    )

    print("OK - governança preservada")


def test_adapter_ai_audit():
    payload = build_realistic_payload()

    output = build_copiaultimorob_agent_output(payload)

    assert (
        output["audit"]["ai_audit_status"]
        == "CONFIRMADO_COM_ALERTAS"
    )

    assert output["audit"]["ai_audit_score"] == 90.0

    print("OK - auditoria interna preservada")


def test_adapter_nvidia_audit():
    payload = build_realistic_payload()

    output = build_copiaultimorob_agent_output(payload)

    assert (
        output["audit"]["nvidia_audit_status"]
        == "CONFIRMED_WITH_WARNINGS"
    )

    assert output["audit"]["nvidia_audit_score"] == 90.0

    print("OK - auditoria NVIDIA preservada")


def test_adapter_schema():
    payload = build_realistic_payload()

    output = build_copiaultimorob_agent_output(payload)

    validation = validate_agent_output(output)

    assert validation["valid"] is True, validation["errors"]

    print("OK - output compatível com schema universal")


def test_incomplete_payload():
    payload = {
        "source_system": "COPIAULTIMOROB",
        "export_version": "1.0",
        "generated_at": "2026-09-17T22:00:00+00:00",
        "macro": {
            "sinal_operacional": "NEUTRO",
        },
    }

    output = build_copiaultimorob_agent_output(payload)

    validation = validate_agent_output(output)

    assert validation["valid"] is True
    assert output["status"] in {
        "WARNING",
        "DATA_INSUFFICIENT",
    }

    print("OK - payload incompleto tratado com segurança")


def test_wrong_source_system():
    payload = build_realistic_payload()

    payload["source_system"] = "SISTEMA_ERRADO"

    try:
        build_copiaultimorob_agent_output(payload)

    except ValueError:
        print("OK - sistema incorreto rejeitado")
        return

    raise AssertionError(
        "O adaptador deveria rejeitar source_system incorreto."
    )


def run_all_tests():
    print("=" * 70)
    print("INVESTMENT CIO AGENT")
    print("TESTE — COPIAULTIMOROB ADAPTER")
    print("=" * 70)

    test_adapter_identity()
    test_adapter_preserves_original_signal()
    test_adapter_preserves_final_verdict()
    test_adapter_survival_risk()
    test_adapter_stress()
    test_adapter_risk_budget()
    test_adapter_governance()
    test_adapter_ai_audit()
    test_adapter_nvidia_audit()
    test_adapter_schema()
    test_incomplete_payload()
    test_wrong_source_system()

    print("=" * 70)
    print("TODOS OS TESTES DO COPIAULTIMOROB PASSARAM")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
