# ============================================================
# INVESTMENT CIO AGENT
# tests/test_synthesis_agent.py
# ============================================================
#
# Teste oficial da camada de síntese V2.
#
# Verifica:
# 1. Preservação da síntese SP500 + COPIAULTIMOROB.
# 2. Identificação de divergência macro/risco.
# 3. Consolidação dos riscos.
# 4. Preservação das auditorias.
# 5. Registro e reconhecimento dos 7 motores.
# 6. Separação por camadas funcionais.
# 7. Preservação de sinais, oportunidades e ordem da fonte.
# 8. Sistemas de seleção/scanner não viram votos macro.
# 9. Política de não recálculo/não execução.
# 10. Compatibilidade da interface genérica.
#
# ============================================================

from agents.synthesis_agent import (
    build_synthesis,
    synthesize_outputs,
    SynthesisError,
)


# ============================================================
# BUILDERS — MOTORES BASE
# ============================================================

def build_sp500_output():
    return {
        "schema_version": "1.0",
        "system_id": "sp500_cycle",
        "system_name": "SP500_CYCLE_ATLAS",
        "generated_at": "2026-09-18T22:00:00+00:00",
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
                "Valuation historicamente elevado.",
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


def build_global_output():
    return {
        "schema_version": "1.0",
        "system_id": "global_portfolio",
        "system_name": "COPIAULTIMOROB",
        "generated_at": "2026-09-18T22:00:00+00:00",
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
# BUILDERS — SELEÇÃO DE ATIVOS
# ============================================================

def build_us_equities_output():
    return {
        "schema_version": "1.0",
        "system_id": "us_equities",
        "system_name": "US Equities",
        "generated_at": "2026-09-18T22:00:00+00:00",
        "status": "OK",
        "decision": {
            "signal": "PORTFOLIO_WITH_ASSET_SIGNALS",
            "confidence": None,
            "summary": "Carteira americana com sinais por ativo.",
        },
        "metrics": {
            "stocks": 15,
            "sectors": 3,
        },
        "risk": {
            "level": None,
            "score": None,
            "alerts": [],
        },
        "data_quality": {
            "score": None,
            "missing_fields": [],
            "warnings": [],
        },
        "positions": [
            {
                "ticker": "AAA",
                "entry_signal": "ENTRADA FORTE",
                "stock_weight": 0.10,
            },
            {
                "ticker": "BBB",
                "entry_signal": "AGUARDAR",
                "stock_weight": 0.10,
            },
        ],
        "opportunities": [],
        "audit": {},
    }


def build_b3_output():
    return {
        "schema_version": "1.0",
        "system_id": "b3_equities",
        "system_name": "B3 Equities",
        "generated_at": "2026-09-18T22:00:00+00:00",
        "status": "OK",
        "decision": {
            "signal": "PORTFOLIO_WITH_ASSET_SIGNALS",
            "confidence": None,
            "summary": "Carteira B3 com sinais por ativo.",
        },
        "metrics": {
            "stocks": 12,
            "sectors": 4,
        },
        "risk": {
            "level": None,
            "score": None,
            "alerts": [],
        },
        "data_quality": {
            "score": None,
            "missing_fields": [],
            "warnings": [],
        },
        "positions": [
            {
                "ticker": "B3A",
                "signal": "COMPRA",
                "weight": 0.08,
            },
            {
                "ticker": "B3B",
                "signal": "AGUARDAR",
                "weight": 0.08,
            },
        ],
        "opportunities": [],
        "audit": {},
    }


def build_fii_output():
    return {
        "schema_version": "1.0",
        "system_id": "fii",
        "system_name": "FII Institutional Scanner",
        "generated_at": "2026-09-18T22:00:00+00:00",
        "status": "OK",
        "decision": {
            "signal": "STRATEGIC_PORTFOLIO_WITH_EXECUTION",
            "confidence": None,
            "summary": "Carteira estratégica de FIIs.",
        },
        "metrics": {
            "portfolio_count": 10,
            "ranking_count": 29,
        },
        "risk": {
            "level": None,
            "score": None,
            "alerts": [],
        },
        "data_quality": {
            "score": None,
            "missing_fields": [],
            "warnings": [],
        },
        "positions": [
            {
                "ticker": "GTWR11",
                "final_status": "COMPRAR AGORA",
                "peso_estrategico": 0.10,
            },
            {
                "ticker": "MXRF11",
                "final_status": "RESERVA ESTRATÉGICA",
                "peso_estrategico": 0.10,
            },
        ],
        "opportunities": [],
        "audit": {},
    }


# ============================================================
# BUILDERS — SCANNERS DE OPORTUNIDADES
# ============================================================

def build_ai_infrastructure_output():
    return {
        "schema_version": "1.0",
        "system_id": "ai_infrastructure",
        "system_name": "AI Infrastructure Scanner",
        "generated_at": "2026-09-18T22:00:00+00:00",
        "status": "OK",
        "decision": {
            "signal": "OPPORTUNITY_SCANNER",
            "confidence": None,
            "summary": "Scanner de infraestrutura de IA.",
        },
        "metrics": {
            "companies": 49,
            "watchlist": 20,
        },
        "risk": {
            "level": None,
            "score": None,
            "alerts": [],
        },
        "data_quality": {
            "score": None,
            "missing_fields": [],
            "warnings": [],
        },
        "positions": [],
        "opportunities": [
            {
                "ticker": "PANW",
                "signal_status": "OBSERVAÇÃO PRIORITÁRIA",
                "source_rank": 1,
            },
            {
                "ticker": "MSFT",
                "signal_status": "AGUARDAR PULLBACK",
                "source_rank": 2,
            },
        ],
        "audit": {},
    }


def build_growth_output():
    return {
        "schema_version": "1.0",
        "system_id": "growth",
        "system_name": "Growth Opportunity Engine",
        "generated_at": "2026-09-18T22:00:00+00:00",
        "status": "OK",
        "decision": {
            "signal": "OPPORTUNITY_SET_WITH_ENTRY_SIGNALS",
            "confidence": None,
            "summary": "Oportunidades de crescimento com sinais de entrada.",
        },
        "metrics": {
            "strategy_rows": 42,
            "pullback_zone": 9,
        },
        "risk": {
            "level": None,
            "score": None,
            "alerts": [],
        },
        "data_quality": {
            "score": None,
            "missing_fields": [],
            "warnings": [],
        },
        "positions": [],
        "opportunities": [
            {
                "ticker": "HOOD",
                "signal": "ENTRADA_FORTE",
                "source_rank": 1,
            },
            {
                "ticker": "UBER",
                "signal": "ENTRADA_FORTE",
                "source_rank": 2,
            },
            {
                "ticker": "XYZ",
                "signal": "AGUARDAR",
                "source_rank": 3,
            },
        ],
        "audit": {},
    }


def build_all_outputs():
    return [
        build_sp500_output(),
        build_global_output(),
        build_us_equities_output(),
        build_b3_output(),
        build_fii_output(),
        build_ai_infrastructure_output(),
        build_growth_output(),
    ]


# ============================================================
# TESTES — BASE SP500 + COPIAULTIMOROB
# ============================================================

def test_build_synthesis():
    result = build_synthesis(
        build_sp500_output(),
        build_global_output(),
    )

    assert result["synthesis_version"] == "2.0"
    assert result["systems_analyzed"] == [
        "SP500_CYCLE_ATLAS",
        "COPIAULTIMOROB",
    ]

    print("OK - síntese base identificada")


def test_preserves_source_decisions():
    result = build_synthesis(
        build_sp500_output(),
        build_global_output(),
    )

    assert (
        result["source_decisions"]["SP500_CYCLE_ATLAS"]["signal"]
        == "HOLD"
    )
    assert (
        result["source_decisions"]["SP500_CYCLE_ATLAS"]
        ["new_contribution_equity"]
        == 0.60
    )
    assert (
        result["source_decisions"]["SP500_CYCLE_ATLAS"]
        ["new_contribution_reserve"]
        == 0.40
    )
    assert (
        result["source_decisions"]["COPIAULTIMOROB"]["signal"]
        == "NEUTRO"
    )
    assert (
        result["source_decisions"]["COPIAULTIMOROB"]["final_verdict"]
        == "REPROVADO_OPERACIONALMENTE"
    )
    assert (
        result["source_decisions"]["COPIAULTIMOROB"]["committee_action"]
        == "BLOQUEAR_NOVAS_COMPRAS"
    )

    print("OK - decisões originais preservadas")


def test_detects_divergence():
    result = build_synthesis(
        build_sp500_output(),
        build_global_output(),
    )

    assert result["comparison"]["sp500_stance"] == "RISK_SEEKING"
    assert result["comparison"]["global_stance"] == "DEFENSIVE"
    assert result["comparison"]["relationship"] == "DIVERGENCE"

    print("OK - divergência macro/risco detectada")


def test_consolidates_base_risk():
    result = build_synthesis(
        build_sp500_output(),
        build_global_output(),
    )

    assert result["risk"]["sp500_risk_level"] == "HIGH"
    assert result["risk"]["global_risk_level"] == "CRITICO"
    assert result["risk"]["global_kill_switch"] is True
    assert len(result["risk"]["alerts"]) > 0

    print("OK - riscos base consolidados")


def test_preserves_audits():
    result = build_synthesis(
        build_sp500_output(),
        build_global_output(),
    )

    assert (
        result["audit"]["sp500"]["engine_consistency_score"]
        == 92.0
    )
    assert (
        result["audit"]["sp500"]["data_quality_score"]
        == 78.0
    )
    assert (
        result["audit"]["copiaultimorob"]["ai_audit_score"]
        == 90.0
    )
    assert (
        result["audit"]["copiaultimorob"]["nvidia_audit_score"]
        == 90.0
    )

    print("OK - auditorias preservadas")


def test_base_policy():
    result = build_synthesis(
        build_sp500_output(),
        build_global_output(),
    )

    policy = result["policy"]

    assert policy["signals_preserved"] is True
    assert policy["indicators_recalculated"] is False
    assert policy["source_decisions_overridden"] is False
    assert policy["broker_execution_allowed"] is False
    assert policy["human_decision_required"] is True

    print("OK - política base preservada")


# ============================================================
# TESTES — SÍNTESE V2 DOS SETE MOTORES
# ============================================================

def test_seven_system_registry():
    result = synthesize_outputs(
        build_all_outputs()
    )

    registry = result["systems_registry"]

    assert registry["expected_count"] == 7
    assert registry["received_count"] == 7
    assert registry["all_seven_present"] is True
    assert registry["systems_missing"] == []
    assert registry["unknown_systems"] == []

    assert registry["systems_present"] == [
        "sp500_cycle",
        "global_portfolio",
        "us_equities",
        "b3_equities",
        "fii",
        "ai_infrastructure",
        "growth",
    ]

    print("OK - registro dos sete motores")


def test_seven_systems_analyzed():
    result = synthesize_outputs(
        build_all_outputs()
    )

    assert len(result["systems_analyzed"]) == 7

    assert "SP500_CYCLE_ATLAS" in result["systems_analyzed"]
    assert "COPIAULTIMOROB" in result["systems_analyzed"]
    assert "US Equities" in result["systems_analyzed"]
    assert "B3 Equities" in result["systems_analyzed"]
    assert "FII Institutional Scanner" in result["systems_analyzed"]
    assert "AI Infrastructure Scanner" in result["systems_analyzed"]
    assert "Growth Opportunity Engine" in result["systems_analyzed"]

    print("OK - sete motores analisados")


def test_functional_layers():
    result = synthesize_outputs(
        build_all_outputs()
    )

    layers = result["layers"]

    assert len(layers["REGIME"]) == 1
    assert len(layers["GLOBAL_RISK"]) == 1
    assert len(layers["ASSET_SELECTION"]) == 3
    assert len(layers["OPPORTUNITY_SCANNER"]) == 2

    assert (
        layers["REGIME"][0]["system_id"]
        == "sp500_cycle"
    )
    assert (
        layers["GLOBAL_RISK"][0]["system_id"]
        == "global_portfolio"
    )

    selection_ids = [
        item["system_id"]
        for item in layers["ASSET_SELECTION"]
    ]

    assert selection_ids == [
        "us_equities",
        "b3_equities",
        "fii",
    ]

    scanner_ids = [
        item["system_id"]
        for item in layers["OPPORTUNITY_SCANNER"]
    ]

    assert scanner_ids == [
        "ai_infrastructure",
        "growth",
    ]

    print("OK - camadas funcionais corretas")


def test_selection_not_used_as_macro_vote():
    result = synthesize_outputs(
        build_all_outputs()
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

    policy = result["policy"]

    assert (
        policy["selection_systems_used_as_macro_votes"]
        is False
    )
    assert (
        policy["opportunity_systems_used_as_macro_votes"]
        is False
    )

    print("OK - seleção/scanners não viram votos macro")


def test_preserves_us_positions_order():
    result = synthesize_outputs(
        build_all_outputs()
    )

    us = result["layers"]["ASSET_SELECTION"][0]

    assert [
        item["ticker"]
        for item in us["positions"]
    ] == ["AAA", "BBB"]

    assert (
        us["positions"][0]["entry_signal"]
        == "ENTRADA FORTE"
    )
    assert (
        us["positions"][1]["entry_signal"]
        == "AGUARDAR"
    )

    print("OK - US Equities preservado")


def test_preserves_b3_positions():
    result = synthesize_outputs(
        build_all_outputs()
    )

    b3 = result["layers"]["ASSET_SELECTION"][1]

    assert [
        item["ticker"]
        for item in b3["positions"]
    ] == ["B3A", "B3B"]

    assert b3["positions"][0]["signal"] == "COMPRA"
    assert b3["positions"][1]["signal"] == "AGUARDAR"

    print("OK - B3 Equities preservado")


def test_preserves_fii_reserved_semantics():
    result = synthesize_outputs(
        build_all_outputs()
    )

    fii = result["layers"]["ASSET_SELECTION"][2]

    assert fii["positions"][0]["final_status"] == "COMPRAR AGORA"
    assert (
        fii["positions"][1]["final_status"]
        == "RESERVA ESTRATÉGICA"
    )

    print("OK - FII e reserva estratégica preservados")


def test_preserves_ai_infrastructure_order():
    result = synthesize_outputs(
        build_all_outputs()
    )

    ai = result["layers"]["OPPORTUNITY_SCANNER"][0]

    assert [
        item["ticker"]
        for item in ai["opportunities"]
    ] == ["PANW", "MSFT"]

    assert ai["opportunities"][0]["source_rank"] == 1
    assert ai["opportunities"][1]["source_rank"] == 2

    print("OK - AI Infrastructure preservado")


def test_preserves_growth_order_and_wait():
    result = synthesize_outputs(
        build_all_outputs()
    )

    growth = result["layers"]["OPPORTUNITY_SCANNER"][1]

    assert [
        item["ticker"]
        for item in growth["opportunities"]
    ] == ["HOOD", "UBER", "XYZ"]

    assert [
        item["signal"]
        for item in growth["opportunities"]
    ] == [
        "ENTRADA_FORTE",
        "ENTRADA_FORTE",
        "AGUARDAR",
    ]

    print("OK - Growth e AGUARDAR preservados")


def test_evidence_layers():
    result = synthesize_outputs(
        build_all_outputs()
    )

    evidence = result["evidence"]

    assert len(evidence["asset_selection"]) == 3
    assert len(evidence["opportunity_scanners"]) == 2

    print("OK - evidências organizadas")


def test_v2_policy():
    result = synthesize_outputs(
        build_all_outputs()
    )

    policy = result["policy"]

    assert policy["seven_system_registry_enabled"] is True
    assert policy["source_order_preserved"] is True
    assert policy["source_signals_preserved"] is True
    assert policy["new_scores_created"] is False
    assert policy["indicators_recalculated"] is False
    assert policy["source_decisions_overridden"] is False
    assert policy["broker_execution_allowed"] is False
    assert policy["human_decision_required"] is True

    print("OK - política V2 preservada")


def test_v2_version():
    result = synthesize_outputs(
        build_all_outputs()
    )

    assert result["synthesis_version"] == "2.0"

    print("OK - versão 2.0 confirmada")


# ============================================================
# TESTES — COMPATIBILIDADE E PROTEÇÕES
# ============================================================

def test_generic_interface_two_base_systems():
    outputs = [
        build_global_output(),
        build_sp500_output(),
    ]

    result = synthesize_outputs(outputs)

    assert (
        result["comparison"]["relationship"]
        == "DIVERGENCE"
    )

    assert (
        result["systems_registry"]["received_count"]
        == 2
    )

    assert (
        result["systems_registry"]["all_seven_present"]
        is False
    )

    print("OK - compatibilidade com dois motores base")


def test_missing_global_system():
    outputs = [
        build_sp500_output(),
    ]

    try:
        synthesize_outputs(outputs)
    except SynthesisError:
        print("OK - ausência do COPIAULTIMOROB detectada")
        return

    raise AssertionError(
        "A síntese deveria rejeitar a ausência "
        "do COPIAULTIMOROB."
    )


def test_missing_sp500_system():
    outputs = [
        build_global_output(),
    ]

    try:
        synthesize_outputs(outputs)
    except SynthesisError:
        print("OK - ausência do SP500 detectada")
        return

    raise AssertionError(
        "A síntese deveria rejeitar a ausência "
        "do SP500_CYCLE_ATLAS."
    )


def test_duplicate_system():
    outputs = build_all_outputs()
    outputs.append(
        build_growth_output()
    )

    try:
        synthesize_outputs(outputs)
    except SynthesisError:
        print("OK - sistema duplicado detectado")
        return

    raise AssertionError(
        "A síntese deveria rejeitar "
        "sistema duplicado."
    )


def test_unknown_system_is_reported():
    outputs = build_all_outputs()

    unknown = {
        "schema_version": "1.0",
        "system_id": "unknown_engine",
        "system_name": "UNKNOWN_ENGINE",
        "generated_at": "2026-09-18T22:00:00+00:00",
        "status": "OK",
        "decision": {
            "signal": "TEST",
            "confidence": None,
            "summary": None,
        },
        "metrics": {},
        "risk": {
            "level": None,
            "score": None,
            "alerts": [],
        },
        "data_quality": {
            "score": None,
            "missing_fields": [],
            "warnings": [],
        },
    }

    outputs.append(unknown)

    result = synthesize_outputs(outputs)

    assert "UNKNOWN_ENGINE" in (
        result["systems_registry"]["unknown_systems"]
    )

    assert result["systems_registry"]["received_count"] == 7

    print("OK - sistema desconhecido reportado sem contaminar síntese")


# ============================================================
# EXECUÇÃO
# ============================================================

def run_all_tests():
    print("=" * 70)
    print("INVESTMENT CIO AGENT")
    print("TESTE — SYNTHESIS AGENT V2")
    print("=" * 70)

    test_build_synthesis()
    test_preserves_source_decisions()
    test_detects_divergence()
    test_consolidates_base_risk()
    test_preserves_audits()
    test_base_policy()

    test_seven_system_registry()
    test_seven_systems_analyzed()
    test_functional_layers()
    test_selection_not_used_as_macro_vote()
    test_preserves_us_positions_order()
    test_preserves_b3_positions()
    test_preserves_fii_reserved_semantics()
    test_preserves_ai_infrastructure_order()
    test_preserves_growth_order_and_wait()
    test_evidence_layers()
    test_v2_policy()
    test_v2_version()

    test_generic_interface_two_base_systems()
    test_missing_global_system()
    test_missing_sp500_system()
    test_duplicate_system()
    test_unknown_system_is_reported()

    print("=" * 70)
    print("SYNTHESIS AGENT V2 — 23 TESTES OK")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
