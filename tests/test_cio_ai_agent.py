# ============================================================
# CIO INTEGRATION ENGINE
# tests/test_cio_ai_agent.py
# Arquitetura V2.0 — Functional Integration
# ============================================================

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

import agents.cio_ai_agent as cio
from agents.cio_ai_agent import (
    CIO_AI_VERSION,
    CIO_AI_BUILD,
    DEFAULT_MODEL,
    OFFICIAL_SYSTEMS,
    RELATION_MAP,
    SYSTEM_PROMPT,
    REPORT_SECTIONS,
    CIOAIInputError,
    CIOAIResponseError,
    CIOAIStructuralValidationError,
    normalize_system_outputs,
    build_functional_context,
    build_ai_prompt,
    validate_report_structure,
    run_cio_ai,
    analyze_cio_context,
)


def assert_test(condition, name):
    if not condition:
        raise AssertionError(name)
    print(f"CIO V2 — {name}: OK")


def build_system_fixture():
    """Fixture mínima: preserva a especialização dos sete sistemas."""
    return {
        "systems": {
            "sp500_cycle": {
                "system_id": "sp500_cycle",
                "regime": "RISK_SEEKING",
                "valuation": "ELEVATED",
            },
            "global_portfolio": {
                "system_id": "global_portfolio",
                "risk_level": "CRITICAL",
                "stance": "DEFENSIVE",
            },
            "us_equities": {
                "system_id": "us_equities",
                "signals": [
                    {"ticker": "NVDA", "signal": "ENTRADA"},
                    {"ticker": "MSFT", "signal": "AGUARDAR"},
                ],
            },
            "ai_infrastructure": {
                "system_id": "ai_infrastructure",
                "signals": [
                    {"ticker": "NVDA", "signal": "WATCHLIST"},
                    {"ticker": "ANET", "signal": "WATCHLIST"},
                ],
            },
            "growth": {
                "system_id": "growth",
                "signals": [
                    {"ticker": "NVDA", "signal": "ENTRADA_FORTE"},
                    {"ticker": "META", "signal": "AGUARDAR"},
                ],
            },
            "b3_equities": {
                "system_id": "b3_equities",
                "signals": [
                    {"ticker": "WEGE3", "signal": "COMPRA"},
                ],
            },
            "fii": {
                "system_id": "fii",
                "signals": [
                    {"ticker": "KNCR11", "signal": "SELECIONADO"},
                ],
            },
        },
        "governance": {
            "global_kill_switch": True,
            "hard_block": True,
            "broker_execution_allowed": False,
            "human_decision_required": True,
        },
    }


def build_valid_report():
    return """1. CENÁRIO E REGIME
O SP500_CYCLE_ATLAS registra RISK_SEEKING e valuation ELEVATED.

2. RISCO DA CARTEIRA
O COPIAULTIMOROB registra risk_level CRITICAL e stance DEFENSIVE.

3. MICRO EUA
Os sistemas micro dos EUA apresentam sinais específicos. NVDA aparece explicitamente em mais de um sistema, com rótulos preservados.

4. MICRO BRASIL
B3 e FII apresentam evidências próprias de classes de ativos diferentes no mercado brasileiro.

5. INTEGRAÇÃO ENTRE CAMADAS
O regime RISK_SEEKING coexiste com risco CRITICAL e com evidências micro específicas nos EUA e no Brasil. Essas relações são tratadas como contexto e coexistência, não como causalidade.

6. CONCLUSÃO CIO INTEGRADA
A leitura conjunta caracteriza um cenário heterogêneo: o pano de fundo de mercado, a condição de risco da carteira e as evidências micro não formam um voto único. Há coexistência entre regime de busca por risco, risco de carteira crítico e sinais micro específicos, sem transformar essa combinação em recomendação operacional.

7. GOVERNANÇA E RASTREABILIDADE
O contexto registra global_kill_switch true, hard_block true, broker_execution_allowed false e human_decision_required true. Os fatos de governança são reportados separadamente da conclusão de cenário.
"""


class FakeCompletions:
    def __init__(self, contents):
        self.contents = list(contents)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        if not self.contents:
            raise RuntimeError("Sem resposta simulada.")
        item = self.contents.pop(0)
        if isinstance(item, Exception):
            raise item
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=item)
                )
            ]
        )


class FakeClient:
    def __init__(self, *contents):
        self.completions = FakeCompletions(contents)
        self.chat = SimpleNamespace(completions=self.completions)


class Fake503Error(Exception):
    status_code = 503


def run_tests():
    print("=" * 72)
    print("CIO INTEGRATION ENGINE — TESTES V2.0")
    print("=" * 72)

    fixture = build_system_fixture()
    original = deepcopy(fixture)

    # --------------------------------------------------------
    # IDENTIDADE E ESCOPO
    # --------------------------------------------------------
    assert_test(CIO_AI_VERSION == "2.0", "VERSÃO 2.0")
    assert_test(
        CIO_AI_BUILD == "2.0-FUNCTIONAL-INTEGRATION",
        "BUILD FUNCTIONAL INTEGRATION",
    )
    assert_test(
        "nemotron-3-super-120b-a12b" in DEFAULT_MODEL,
        "MODELO NVIDIA NEMOTRON",
    )
    assert_test(len(OFFICIAL_SYSTEMS) == 7, "SETE SISTEMAS OFICIAIS")
    assert_test(
        set(REPORT_SECTIONS) == {
            "1. CENÁRIO E REGIME",
            "2. RISCO DA CARTEIRA",
            "3. MICRO EUA",
            "4. MICRO BRASIL",
            "5. INTEGRAÇÃO ENTRE CAMADAS",
            "6. CONCLUSÃO CIO INTEGRADA",
            "7. GOVERNANÇA E RASTREABILIDADE",
        },
        "SETE SEÇÕES FUNCIONAIS",
    )

    # --------------------------------------------------------
    # MAPA FUNCIONAL
    # --------------------------------------------------------
    assert_test(
        OFFICIAL_SYSTEMS["sp500_cycle"]["layer"] == "SCENARIO"
        and OFFICIAL_SYSTEMS["sp500_cycle"]["role"] == "REGIME",
        "ATLAS É CAMADA DE CENÁRIO",
    )
    assert_test(
        OFFICIAL_SYSTEMS["global_portfolio"]["layer"] == "RISK"
        and OFFICIAL_SYSTEMS["global_portfolio"]["role"] == "PORTFOLIO_RISK",
        "COPIAULTIMOROB É CAMADA DE RISCO",
    )
    assert_test(
        {
            sid for sid, meta in OFFICIAL_SYSTEMS.items()
            if meta["layer"] == "MICRO_US"
        } == {"us_equities", "ai_infrastructure", "growth"},
        "MICRO EUA CONTÉM TRÊS ESPECIALISTAS",
    )
    assert_test(
        {
            sid for sid, meta in OFFICIAL_SYSTEMS.items()
            if meta["layer"] == "MICRO_BR"
        } == {"b3_equities", "fii"},
        "MICRO BRASIL CONTÉM B3 E FII",
    )
    assert_test(
        OFFICIAL_SYSTEMS["fii"]["region"] == "BR",
        "FII É BRASIL",
    )

    # --------------------------------------------------------
    # RELAÇÕES AUTORIZADAS
    # --------------------------------------------------------
    assert_test(
        RELATION_MAP["regime_x_risk"]["systems"]
        == ["sp500_cycle", "global_portfolio"],
        "REGIME X RISCO É RELAÇÃO ESTRUTURAL",
    )
    assert_test(
        set(RELATION_MAP["us_micro"]["systems"])
        == {"us_equities", "ai_infrastructure", "growth"},
        "RELAÇÃO MICRO EUA",
    )
    assert_test(
        set(RELATION_MAP["brazil_micro"]["systems"])
        == {"b3_equities", "fii"},
        "RELAÇÃO REGIONAL BRASIL",
    )
    assert_test(
        all(
            relation["causality_allowed"] is False
            for relation in RELATION_MAP.values()
        ),
        "MAPA NÃO AUTORIZA CAUSALIDADE INVENTADA",
    )

    # --------------------------------------------------------
    # NORMALIZAÇÃO E PRESERVAÇÃO
    # --------------------------------------------------------
    normalized = normalize_system_outputs(fixture)
    assert_test(
        set(normalized) == set(OFFICIAL_SYSTEMS),
        "NORMALIZA OS SETE SISTEMAS",
    )
    assert_test(
        normalized["us_equities"]
        == fixture["systems"]["us_equities"],
        "PAYLOAD DE ORIGEM PRESERVADO",
    )
    assert_test(fixture == original, "NORMALIZAÇÃO NÃO ALTERA INPUT")

    direct_fixture = deepcopy(fixture["systems"])
    direct_normalized = normalize_system_outputs(direct_fixture)
    assert_test(
        set(direct_normalized) == set(OFFICIAL_SYSTEMS),
        "ACEITA CONTRATO DIRETO DURANTE MIGRAÇÃO",
    )

    nested_legacy = {
        "legacy": {
            "items": list(deepcopy(fixture["systems"]).values())
        }
    }
    legacy_normalized = normalize_system_outputs(nested_legacy)
    assert_test(
        set(legacy_normalized) == set(OFFICIAL_SYSTEMS),
        "ACEITA PAYLOAD LEGADO COM SYSTEM_ID",
    )

    try:
        normalize_system_outputs({})
        raise AssertionError("Entrada vazia deveria falhar.")
    except CIOAIInputError:
        pass
    assert_test(True, "BLOQUEIA ENTRADA VAZIA")

    incomplete = deepcopy(fixture)
    del incomplete["systems"]["fii"]
    try:
        normalize_system_outputs(incomplete)
        raise AssertionError("Entrada com seis sistemas deveria falhar.")
    except CIOAIInputError as exc:
        missing_fii = "fii" in str(exc)
    assert_test(missing_fii, "BLOQUEIA SISTEMA AUSENTE")

    # --------------------------------------------------------
    # CONTEXTO FUNCIONAL
    # --------------------------------------------------------
    context = build_functional_context(fixture)
    assert_test(
        context["architecture"] == "FUNCTIONAL_INTEGRATION",
        "ARQUITETURA FUNCIONAL NO CONTEXTO",
    )
    assert_test(
        context["layers"]["SCENARIO"] == ["sp500_cycle"]
        and context["layers"]["RISK"] == ["global_portfolio"],
        "CAMADAS MACRO/RISCO CORRETAS",
    )
    assert_test(
        context["layers"]["MICRO_US"]
        == ["us_equities", "ai_infrastructure", "growth"],
        "CAMADA MICRO EUA CORRETA",
    )
    assert_test(
        context["layers"]["MICRO_BR"] == ["b3_equities", "fii"],
        "CAMADA MICRO BRASIL CORRETA",
    )
    assert_test(
        context["source_data"] == fixture["systems"],
        "FATOS DOS ROBÔS PRESERVADOS NO CONTEXTO",
    )
    assert_test(
        context["governance"] == fixture["governance"],
        "GOVERNANÇA PRESERVADA",
    )
    assert_test(
        context["rules"]["systems_are_not_equal_votes"] is True
        and context["rules"]["different_roles_must_not_be_forced_into_consensus"] is True,
        "ROBÔS NÃO SÃO VOTOS EQUIVALENTES",
    )
    assert_test(
        context["rules"]["cross_layer_inference_is_allowed"] is True,
        "INFERÊNCIA ENTRE CAMADAS É PERMITIDA",
    )
    assert_test(
        context["rules"]["new_quantitative_signal_is_forbidden"] is True
        and context["rules"]["new_score_is_forbidden"] is True
        and context["rules"]["investment_recommendation_is_forbidden"] is True,
        "SEM NOVO SINAL SCORE OU RECOMENDAÇÃO",
    )

    # --------------------------------------------------------
    # PROMPT: OBJETIVO NOVO
    # --------------------------------------------------------
    prompt = build_ai_prompt(context)
    prompt_lower = prompt.lower()
    system_lower = SYSTEM_PROMPT.lower()

    assert_test(
        "não são sete votos equivalentes" in system_lower,
        "PROMPT PROÍBE VOTAÇÃO ENTRE ROBÔS",
    )
    assert_test(
        "integrar dimensões funcionais" in system_lower,
        "PROMPT MANDA INTEGRAR DIMENSÕES",
    )
    assert_test(
        "mesmo ticker" in system_lower,
        "COMPARAÇÃO DIRETA EXIGE DIMENSÃO COMUM",
    )
    assert_test(
        "coexistência" in system_lower
        and "causalidade" in system_lower,
        "PROMPT DIFERENCIA COEXISTÊNCIA E CAUSALIDADE",
    )
    assert_test(
        "governança" in system_lower
        and "separada da conclusão de cenário" in system_lower,
        "GOVERNANÇA SEPARADA DA CONCLUSÃO",
    )
    assert_test(
        "não resuma os sete robôs em sequência" in prompt_lower,
        "PROMPT NÃO ACEITA RESUMO SEQUENCIAL",
    )
    assert_test(
        "use o relation_map" in prompt_lower,
        "PROMPT USA MAPA DE RELAÇÕES",
    )
    assert_test(
        "qual é a leitura integrada do cenário de investimento"
        in prompt_lower,
        "PROMPT EXIGE LEITURA CIO ÚNICA",
    )
    assert_test(
        prompt.find("6. CONCLUSÃO CIO INTEGRADA")
        < prompt.find("7. GOVERNANÇA E RASTREABILIDADE"),
        "CONCLUSÃO VEM ANTES DA GOVERNANÇA",
    )

    # --------------------------------------------------------
    # VALIDAÇÃO ESTRUTURAL
    # --------------------------------------------------------
    report = build_valid_report()
    structural = validate_report_structure(report)
    assert_test(
        structural["status"] == "PASS"
        and structural["sections_found"] == 7
        and structural["integrated_conclusion_present"] is True,
        "RELATÓRIO V2 VÁLIDO PASSA",
    )

    missing_conclusion = report.replace(
        "6. CONCLUSÃO CIO INTEGRADA",
        "6. OUTRA SEÇÃO",
    )
    try:
        validate_report_structure(missing_conclusion)
        raise AssertionError("Conclusão obrigatória ausente deveria falhar.")
    except CIOAIStructuralValidationError:
        pass
    assert_test(True, "CONCLUSÃO CIO É OBRIGATÓRIA")

    empty_conclusion = report.replace(
        """6. CONCLUSÃO CIO INTEGRADA
A leitura conjunta caracteriza um cenário heterogêneo: o pano de fundo de mercado, a condição de risco da carteira e as evidências micro não formam um voto único. Há coexistência entre regime de busca por risco, risco de carteira crítico e sinais micro específicos, sem transformar essa combinação em recomendação operacional.

7. GOVERNANÇA E RASTREABILIDADE""",
        """6. CONCLUSÃO CIO INTEGRADA

7. GOVERNANÇA E RASTREABILIDADE""",
    )
    try:
        validate_report_structure(empty_conclusion)
        raise AssertionError("Conclusão vazia deveria falhar.")
    except CIOAIStructuralValidationError:
        pass
    assert_test(True, "CONCLUSÃO CIO VAZIA É BLOQUEADA")

    wrong_order = report.replace(
        "5. INTEGRAÇÃO ENTRE CAMADAS",
        "TEMP_SECTION",
    ).replace(
        "6. CONCLUSÃO CIO INTEGRADA",
        "5. INTEGRAÇÃO ENTRE CAMADAS",
    ).replace(
        "TEMP_SECTION",
        "6. CONCLUSÃO CIO INTEGRADA",
    )
    try:
        validate_report_structure(wrong_order)
        raise AssertionError("Ordem incorreta deveria falhar.")
    except CIOAIStructuralValidationError:
        pass
    assert_test(True, "ORDEM FUNCIONAL É OBRIGATÓRIA")

    # --------------------------------------------------------
    # EXECUÇÃO NVIDIA SIMULADA
    # --------------------------------------------------------
    fake_client = FakeClient(report)
    with patch.object(cio, "_build_nvidia_client", return_value=fake_client):
        result = run_cio_ai(fixture)

    assert_test(result["status"] == "OK", "EXECUÇÃO SIMULADA OK")
    assert_test(
        result["architecture"] == "FUNCTIONAL_INTEGRATION",
        "RESULTADO IDENTIFICA NOVA ARQUITETURA",
    )
    assert_test(
        result["systems_count"] == 7,
        "RESULTADO REGISTRA SETE SISTEMAS",
    )
    assert_test(
        result["source_data_changed"] is False,
        "RESULTADO DECLARA FONTE NÃO ALTERADA",
    )
    assert_test(
        result["structural_validation"]["status"] == "PASS",
        "VALIDAÇÃO ESTRUTURAL EXPOSTA",
    )
    assert_test(
        fake_client.completions.calls[0]["model"] == DEFAULT_MODEL,
        "MODELO CORRETO ENVIADO À NVIDIA",
    )
    assert_test(
        len(fake_client.completions.calls[0]["messages"]) == 2
        and fake_client.completions.calls[0]["messages"][0]["role"] == "system"
        and fake_client.completions.calls[0]["messages"][1]["role"] == "user",
        "SYSTEM E USER PROMPTS ENVIADOS",
    )
    assert_test(fixture == original, "EXECUÇÃO NÃO ALTERA INPUT")

    alias_client = FakeClient(report)
    with patch.object(cio, "_build_nvidia_client", return_value=alias_client):
        alias_result = analyze_cio_context(fixture)
    assert_test(alias_result["status"] == "OK", "INTERFACE ALTERNATIVA FUNCIONA")

    # --------------------------------------------------------
    # RESILIÊNCIA NVIDIA
    # --------------------------------------------------------
    retry_client = FakeClient(
        Fake503Error("503 Service Unavailable"),
        report,
    )
    sleep_calls = []
    with patch.object(cio, "_build_nvidia_client", return_value=retry_client), \
         patch.object(cio.time, "sleep", side_effect=lambda seconds: sleep_calls.append(seconds)):
        retry_result = run_cio_ai(fixture)

    assert_test(
        retry_result["status"] == "OK"
        and len(retry_client.completions.calls) == 2
        and sleep_calls == [1],
        "503 TRANSITÓRIO RECUPERA",
    )

    fail_client = FakeClient(RuntimeError("401 unauthorized"))
    with patch.object(cio, "_build_nvidia_client", return_value=fail_client):
        try:
            run_cio_ai(fixture)
            raise AssertionError("Erro não transitório deveria falhar.")
        except CIOAIResponseError:
            pass
    assert_test(
        len(fail_client.completions.calls) == 1,
        "ERRO NÃO 503 NÃO É REPETIDO",
    )

    # --------------------------------------------------------
    # TESTES DE OBJETIVO — O QUE ESTA V2 PRECISA GARANTIR
    # --------------------------------------------------------
    assert_test(
        "systems_are_not_equal_votes" in prompt
        and '"systems_are_not_equal_votes": true' in prompt_lower,
        "NVIDIA RECEBE REGRA DE NÃO VOTAÇÃO",
    )
    assert_test(
        '"cross_layer_inference_is_allowed": true' in prompt_lower,
        "NVIDIA RECEBE AUTORIZAÇÃO DE INFERÊNCIA ANALÍTICA",
    )
    assert_test(
        '"coexistence_is_not_causality": true' in prompt_lower,
        "NVIDIA RECEBE LIMITE DE CAUSALIDADE",
    )
    assert_test(
        '"governance_is_reported_after_scenario_conclusion": true' in prompt_lower,
        "NVIDIA RECEBE SEPARAÇÃO DA GOVERNANÇA",
    )

    print("=" * 72)
    print("CIO INTEGRATION ENGINE V2.0 — TODOS OS TESTES OK")
    print("=" * 72)


if __name__ == "__main__":
    run_tests()
