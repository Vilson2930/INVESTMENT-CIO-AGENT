# ============================================================
# INVESTMENT CIO AGENT
# tests/test_cio_ai_agent.py
# ============================================================

from copy import deepcopy
from types import SimpleNamespace

from agents.cio_ai_agent import (
    CIO_AI_VERSION,
    DEFAULT_MODEL,
    OFFICIAL_SYSTEMS,
    SYSTEM_PROMPT,
    CIOAIInputError,
    CIOAIResponseError,
    CIOAISemanticValidationError,
    validate_orchestrator_context,
    build_ai_context,
    build_ai_prompt,
    validate_ai_analysis_semantics,
    run_cio_ai,
    analyze_cio_context,
)


# ============================================================
# CLIENTE NVIDIA SIMULADO
# ============================================================

class FakeCompletions:

    def __init__(
        self,
        content=None,
        raise_error=False,
        contents=None,
    ):
        self.content = content
        self.raise_error = raise_error
        self.contents = list(contents) if contents is not None else None
        self.last_call = None
        self.calls = []

    def create(self, **kwargs):

        self.last_call = deepcopy(kwargs)
        self.calls.append(deepcopy(kwargs))

        if self.raise_error:
            raise RuntimeError("NVIDIA indisponível")

        if self.contents is not None:
            if not self.contents:
                raise RuntimeError(
                    "Sem resposta simulada NVIDIA disponível."
                )
            response_content = self.contents.pop(0)
        else:
            response_content = self.content

        if isinstance(response_content, Exception):
            raise response_content

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=response_content
                    )
                )
            ]
        )


class FakeChat:

    def __init__(self, completions):
        self.completions = completions


class FakeNVIDIAClient:

    def __init__(
        self,
        content="ANÁLISE CIO SIMULADA",
        raise_error=False,
        contents=None,
    ):
        self.completions = FakeCompletions(
            content=content,
            raise_error=raise_error,
            contents=contents,
        )

        self.chat = FakeChat(
            self.completions
        )


# ============================================================
# FIXTURE DO ORCHESTRATOR
# ============================================================

def build_orchestrator_fixture():

    return {
        "orchestrator_version": "1.0",

        "status": "WARNING",

        "summary": {
            "systems_received": 7,
            "systems_recognized": 7,
            "global_constraint_state": "HARD_RESTRICTION",
            "hard_block": True,
        },

        "system_inventory": {
            "recognized_systems": [
                "sp500_cycle",
                "global_portfolio",
                "us_equities",
                "b3_equities",
                "fii",
                "ai_infrastructure",
                "growth",
            ]
        },

        "governance": {
            "human_decision_required": True,
            "broker_execution_allowed": False,
        },

        "synthesis": {
            "synthesis_version": "2.0",

            "status": "WARNING",

            "system_registry": {
                "sp500_cycle": {
                    "role": "REGIME"
                },

                "global_portfolio": {
                    "role": "GLOBAL_RISK"
                },

                "us_equities": {
                    "role": "ASSET_SELECTION"
                },

                "b3_equities": {
                    "role": "ASSET_SELECTION"
                },

                "fii": {
                    "role": "ASSET_SELECTION"
                },

                "ai_infrastructure": {
                    "role": "OPPORTUNITY_SCANNER"
                },

                "growth": {
                    "role": "OPPORTUNITY_SCANNER"
                },
            },

            "system_layers": {
                "regime": [
                    "sp500_cycle"
                ],

                "global_risk": [
                    "global_portfolio"
                ],

                "asset_selection": [
                    "us_equities",
                    "b3_equities",
                    "fii",
                ],

                "opportunity_scanners": [
                    "ai_infrastructure",
                    "growth",
                ],
            },

            "macro_risk_relationship": {
                "state": "DIVERGENCE",

                "regime_signal": "RISK_SEEKING",

                "risk_signal": "DEFENSIVE",
            },

            "source_signals": {
                "sp500_cycle": "RISK_SEEKING",

                "global_portfolio": "DEFENSIVE",

                "us_equities": [
                    "ENTRADA",
                    "AGUARDAR",
                ],

                "b3_equities": [
                    "ENTRADA"
                ],

                "fii": [
                    "RESERVA ESTRATÉGICA"
                ],

                "ai_infrastructure": [
                    "ENTRADA"
                ],

                "growth": [
                    "AGUARDAR"
                ],
            },

            "policy": {
                "source_order_preserved": True,
                "source_signals_preserved": True,
                "new_scores_created": False,
            },
        },

        "risk": {
            "risk_agent_version": "1.0",

            "status": "WARNING",

            "global_risk": {
                "global_risk_level": "CRITICAL",
                "global_survival_status": "REPROVADO",
                "global_kill_switch": True,
            },

            "global_constraint": {
                "state": "HARD_RESTRICTION",

                "hard_block": True,

                "global_kill_switch": True,

                "global_risk_level": "CRITICAL",

                "global_survival_status": "REPROVADO",

                "restriction_codes": [
                    "GLOBAL_KILL_SWITCH_ACTIVE"
                ],

                "restriction_count": 1,

                "source": "RISK_AGENT",

                "source_signals_changed": False,

                "source_decisions_overridden": False,
            },

            "restrictions": [
                {
                    "code": "GLOBAL_KILL_SWITCH_ACTIVE",
                    "severity": "CRITICAL",
                }
            ],

            "restriction_codes": [
                "GLOBAL_KILL_SWITCH_ACTIVE"
            ],

            "risk_opportunity_context": {
                "opportunities_present": True,
                "risk_restriction_present": True,
            },

            "source_signals": {
                "sp500_cycle": "RISK_SEEKING",
                "global_portfolio": "DEFENSIVE",
            },

            "policy": {
                "source_signals_preserved": True,
                "indicators_recalculated": False,
                "new_quantitative_score_created": False,
                "broker_execution_allowed": False,
                "human_decision_required": True,
            },
        },

        "decision": {
            "decision_agent_version": "1.0",

            "status": "WARNING",

            "operational_context": {
                "state": "RESTRICTED"
            },

            "source_signals": {
                "sp500_cycle": "RISK_SEEKING",

                "global_portfolio": "DEFENSIVE",

                "growth": [
                    "AGUARDAR"
                ],

                "ai_infrastructure": [
                    "ENTRADA"
                ],
            },

            "policy": {
                "source_signals_preserved": True,
                "source_decisions_overridden": False,
                "broker_execution_allowed": False,
                "human_decision_required": True,
            },
        },

        "executive_report": {
            "executive_report_version": "1.0",

            "status": "WARNING",

            "executive_summary": (
                "Ambiente com oportunidades específicas "
                "e restrição global de risco."
            ),

            "policy": {
                "source_signals_preserved": True,
                "broker_execution_allowed": False,
                "human_decision_required": True,
            },
        },

        "policy": {
            "source_signals_preserved": True,
            "source_order_preserved": True,
            "broker_execution_allowed": False,
            "human_decision_required": True,
        },
    }


# ============================================================
# AUXILIAR
# ============================================================

def assert_test(condition, name):

    if not condition:
        raise AssertionError(name)

    print(f"CIO AI — {name}: OK")


# ============================================================
# TESTES
# ============================================================

def run_tests():

    print("=" * 70)
    print("INVESTMENT CIO AGENT")
    print("TESTE — CIO AI AGENT V1.5 / NVIDIA NIM")
    print("=" * 70)

    fixture = build_orchestrator_fixture()

    original_fixture = deepcopy(fixture)

    # 1
    assert_test(
        CIO_AI_VERSION == "1.5",
        "IDENTIFICAÇÃO V1.5",
    )

    # 2
    assert_test(
        "nemotron-3-super-120b-a12b"
        in DEFAULT_MODEL,
        "MODELO NVIDIA",
    )

    # 3
    assert_test(
        len(OFFICIAL_SYSTEMS) == 7,
        "7 SISTEMAS OFICIAIS",
    )

    # 4
    assert_test(
        validate_orchestrator_context(fixture) is True,
        "CONTEXTO DO ORCHESTRATOR",
    )

    # 5
    context = build_ai_context(fixture)

    assert_test(
        isinstance(context, dict),
        "CONTEXTO DA IA",
    )

    # 6
    assert_test(
        context["synthesis"]
        == fixture["synthesis"],
        "SYNTHESIS PRESERVADO",
    )

    # 7
    assert_test(
        context["risk"]["global_risk"]
        == fixture["risk"]["global_risk"],
        "RISCO GLOBAL PRESERVADO",
    )

    # 8
    assert_test(
        context["risk"]
        ["global_constraint"]
        ["global_kill_switch"] is True,
        "KILL SWITCH PRESERVADO",
    )

    # 9
    assert_test(
        context["risk"]
        ["global_constraint"]
        ["hard_block"] is True,
        "HARD BLOCK PRESERVADO",
    )

    # 10
    assert_test(
        context["risk"]["restriction_codes"]
        == ["GLOBAL_KILL_SWITCH_ACTIVE"],
        "RESTRIÇÕES PRESERVADAS",
    )

    # 11
    assert_test(
        context["synthesis"]
        ["macro_risk_relationship"]
        ["state"] == "DIVERGENCE",
        "DIVERGÊNCIA PRESERVADA",
    )

    # 12
    assert_test(
        context["synthesis"]
        ["source_signals"]
        ["growth"] == ["AGUARDAR"],
        "GROWTH PRESERVADO",
    )

    # 13
    assert_test(
        context["synthesis"]
        ["source_signals"]
        ["ai_infrastructure"]
        == ["ENTRADA"],
        "AI INFRASTRUCTURE PRESERVADO",
    )

    # 14
    assert_test(
        context["synthesis"]
        ["source_signals"]
        ["fii"]
        == ["RESERVA ESTRATÉGICA"],
        "FII PRESERVADO",
    )

    # 15
    assert_test(
        context["mandatory_policy"]
        ["broker_execution_allowed"] is False
        and
        context["mandatory_policy"]
        ["human_decision_required"] is True,
        "POLÍTICA DE SEGURANÇA",
    )

    # 16
    prompt = build_ai_prompt(context)

    assert_test(
        "RISCO X OPORTUNIDADE" in prompt
        and
        "MACRO X MICRO" in prompt
        and
        "SELEÇÃO X TIMING" in prompt
        and
        "RASTREABILIDADE" in prompt,
        "PROMPT RELACIONAL",
    )

    # 17
    fake_client = FakeNVIDIAClient(
        content=(
            "Análise integrada simulada dos sete sistemas."
        )
    )

    result = run_cio_ai(
        fixture,
        client=fake_client,
    )

    assert_test(
        result["status"] == "OK",
        "EXECUÇÃO NVIDIA SIMULADA",
    )

    # 18
    assert_test(
        result["provider"] == "NVIDIA_NIM",
        "PROVEDOR NVIDIA",
    )

    # 19
    call = fake_client.completions.last_call

    assert_test(
        call["model"] == DEFAULT_MODEL,
        "MODELO ENVIADO À NVIDIA",
    )

    # 20
    assert_test(
        len(call["messages"]) == 2
        and
        call["messages"][0]["role"] == "system"
        and
        call["messages"][1]["role"] == "user",
        "MENSAGENS DA IA",
    )

    # 21
    assert_test(
        result["analysis"]
        == "Análise integrada simulada dos sete sistemas.",
        "ANÁLISE RETORNADA",
    )

    # 22
    assert_test(
        result["context_summary"]
        ["hard_block"] is True,
        "HARD BLOCK NO RESULTADO",
    )

    # 23
    assert_test(
        result["context_summary"]
        ["global_kill_switch"] is True,
        "KILL SWITCH NO RESULTADO",
    )

    # 24
    assert_test(
        result["policy"]
        ["indicators_recalculated"] is False
        and
        result["policy"]
        ["new_quantitative_scores_created"] is False,
        "SEM RECÁLCULO OU NOVO SCORE",
    )

    # 25
    assert_test(
        result["policy"]
        ["source_decisions_overridden"] is False,
        "DECISÕES NÃO SOBRESCRITAS",
    )

    # 26
    assert_test(
        result["policy"]
        ["broker_execution_allowed"] is False,
        "SEM EXECUÇÃO EM CORRETORA",
    )

    # 27
    assert_test(
        result["policy"]
        ["human_decision_required"] is True,
        "DECISÃO HUMANA OBRIGATÓRIA",
    )

    # 28
    assert_test(
        fixture == original_fixture,
        "INPUT NÃO ALTERADO",
    )

    # 29
    second_client = FakeNVIDIAClient(
        content="Segunda análise simulada."
    )

    second_result = analyze_cio_context(
        fixture,
        client=second_client,
    )

    assert_test(
        second_result["status"] == "OK",
        "INTERFACE ALTERNATIVA",
    )

    # 30
    try:
        validate_orchestrator_context({})
        raise AssertionError(
            "Contexto vazio deveria falhar."
        )
    except CIOAIInputError:
        pass

    assert_test(
        True,
        "PROTEÇÃO CONTEXTO VAZIO",
    )

    # 31
    try:
        validate_orchestrator_context([])
        raise AssertionError(
            "Tipo inválido deveria falhar."
        )
    except CIOAIInputError:
        pass

    assert_test(
        True,
        "PROTEÇÃO TIPO INVÁLIDO",
    )

    # 32
    invalid_fixture = deepcopy(fixture)
    del invalid_fixture["risk"]

    try:
        validate_orchestrator_context(
            invalid_fixture
        )
        raise AssertionError(
            "Etapa ausente deveria falhar."
        )
    except CIOAIInputError:
        pass

    assert_test(
        True,
        "PROTEÇÃO ETAPA AUSENTE",
    )

    # 33
    empty_client = FakeNVIDIAClient(
        content="   "
    )

    try:
        run_cio_ai(
            fixture,
            client=empty_client,
        )
        raise AssertionError(
            "Resposta vazia deveria falhar."
        )
    except CIOAIResponseError:
        pass

    assert_test(
        True,
        "PROTEÇÃO RESPOSTA VAZIA",
    )

    # 34
    error_client = FakeNVIDIAClient(
        raise_error=True
    )

    try:
        run_cio_ai(
            fixture,
            client=error_client,
        )
        raise AssertionError(
            "Erro NVIDIA deveria ser tratado."
        )
    except CIOAIResponseError:
        pass

    assert_test(
        True,
        "TRATAMENTO ERRO NVIDIA",
    )

    # ========================================================
    # GOVERNANÇA SEMÂNTICA V1.1 — PRESERVADA
    # ========================================================

    # 35
    assert_test(
        context["mandatory_policy"]
        ["ai_must_not_create_investment_recommendations"]
        is True,
        "IA NÃO CRIA RECOMENDAÇÃO",
    )

    # 36
    assert_test(
        context["mandatory_policy"]
        ["ai_must_not_create_action_rules"]
        is True,
        "IA NÃO CRIA REGRA OPERACIONAL",
    )

    # 37
    assert_test(
        context["mandatory_policy"]
        ["ai_must_not_invent_signal_causes"]
        is True,
        "IA NÃO INVENTA CAUSA DE SINAL",
    )

    # 38
    assert_test(
        context["mandatory_policy"]
        ["ai_must_not_invent_cross_system_relationships"]
        is True,
        "IA NÃO INVENTA RELAÇÃO ENTRE SISTEMAS",
    )

    # 39
    assert_test(
        context["mandatory_policy"]
        ["explicit_evidence_required_for_causal_claims"]
        is True,
        "CAUSALIDADE EXIGE EVIDÊNCIA",
    )

    # 40
    assert_test(
        context["mandatory_policy"]
        ["source_actions_must_be_attributed"]
        is True,
        "AÇÃO DE ORIGEM EXIGE ATRIBUIÇÃO",
    )

    system_prompt_lower = SYSTEM_PROMPT.lower()

    # 41
    assert_test(
        "não crie recomendações próprias de investimento"
        in system_prompt_lower
        and
        "não funciona"
        in system_prompt_lower
        and
        "oitavo motor"
        in system_prompt_lower,
        "PROMPT PROÍBE RECOMENDAÇÃO PRÓPRIA",
    )

    # 42
    assert_test(
        "não invente a causa de um sinal"
        in system_prompt_lower
        and
        "evidência explícita"
        in system_prompt_lower,
        "PROMPT PROÍBE CAUSA INVENTADA",
    )

    # 43
    assert_test(
        "uma relação entre dois sistemas"
        in system_prompt_lower
        and
        "efetivamente presentes no contexto"
        in system_prompt_lower,
        "RELAÇÕES EXIGEM EVIDÊNCIA",
    )

    # 44
    assert_test(
        "mesmo ticker"
        in system_prompt_lower
        and
        "respectivos sistemas"
        in system_prompt_lower,
        "CRUZAMENTO DE TICKER EXIGE EVIDÊNCIA",
    )

    # 45
    assert_test(
        "não generalize a partir de poucos ativos"
        in system_prompt_lower,
        "SEM GENERALIZAÇÃO INDEVIDA",
    )

    # 46
    assert_test(
        "fato de origem:" in system_prompt_lower
        and
        "relação:" in system_prompt_lower
        and
        "interpretação:" in system_prompt_lower,
        "SEPARAÇÃO FATO RELAÇÃO INTERPRETAÇÃO",
    )

    # 47
    assert_test(
        "não use linguagem prescritiva própria"
        in system_prompt_lower
        and
        '"a recomendação é"'
        in system_prompt_lower
        and
        '"preserve capital"'
        in system_prompt_lower,
        "SEM LINGUAGEM PRESCRITIVA PRÓPRIA",
    )

    # 48
    assert_test(
        "não transforme kill switch, hard block"
        in system_prompt_lower
        and
        "recomendação nova criada por você"
        in system_prompt_lower,
        "HARD BLOCK NÃO GERA RECOMENDAÇÃO DA IA",
    )

    # 49
    assert_test(
        "coexistência"
        in system_prompt_lower
        and
        "não resolva essa tensão criando uma decisão própria"
        in system_prompt_lower,
        "RISCO E OPORTUNIDADE SEM DECISÃO INVENTADA",
    )

    # 50
    assert_test(
        "não fornece evidência"
        in system_prompt_lower
        and
        "causa específica"
        in system_prompt_lower,
        "AUSÊNCIA DE EVIDÊNCIA DECLARADA",
    )

    # 51
    assert_test(
        "a síntese cio é uma síntese interpretativa"
        in system_prompt_lower
        and
        "novo sinal"
        in system_prompt_lower
        and
        "novo score"
        in system_prompt_lower,
        "SÍNTESE CIO SOMENTE INTERPRETATIVA",
    )

    prompt_lower = prompt.lower()

    # 52
    assert_test(
        "não crie uma recomendação própria de investimento"
        in prompt_lower
        and
        "a síntese não pode:"
        in prompt_lower,
        "USER PROMPT SEM RECOMENDAÇÃO PRÓPRIA",
    )

    # 53
    assert_test(
        "não atribua um motivo ao timing"
        in prompt_lower
        and
        "não fornece"
        in prompt_lower
        and
        "causa específica"
        in prompt_lower,
        "USER PROMPT SEM CAUSA DE TIMING INVENTADA",
    )

    # 54
    assert_test(
        "kill switch e hard block devem ser apresentados exatamente"
        in prompt_lower
        and
        "não crie consequências operacionais adicionais"
        in prompt_lower,
        "USER PROMPT PRESERVA GOVERNANÇA",
    )

    # 55
    assert_test(
        result["policy"]
        ["ai_created_investment_recommendation"]
        is False,
        "RESULTADO SEM RECOMENDAÇÃO DA IA",
    )

    # 56
    assert_test(
        result["policy"]
        ["ai_created_action_rule"]
        is False,
        "RESULTADO SEM REGRA DE AÇÃO",
    )

    # 57
    assert_test(
        result["policy"]
        ["causal_claims_require_explicit_evidence"]
        is True,
        "RESULTADO EXIGE EVIDÊNCIA CAUSAL",
    )

    # 58
    sent_system_prompt = (
        call["messages"][0]["content"].lower()
    )

    sent_user_prompt = (
        call["messages"][1]["content"].lower()
    )

    assert_test(
        "não crie recomendações próprias de investimento"
        in sent_system_prompt
        and
        "não invente a causa de um sinal"
        in sent_system_prompt
        and
        "não crie uma recomendação própria de investimento"
        in sent_user_prompt,
        "NVIDIA RECEBE GOVERNANÇA V1.1",
    )

    # ========================================================
    # NOVOS TESTES — GOVERNANÇA SEMÂNTICA V1.2
    # ========================================================

    # 59
    assert_test(
        context["mandatory_policy"]
        ["convergence_requires_comparable_evidence"]
        is True,
        "CONVERGÊNCIA EXIGE EVIDÊNCIA COMPARÁVEL",
    )

    # 60
    assert_test(
        context["mandatory_policy"]
        ["same_ticker_convergence_requires_same_ticker"]
        is True,
        "CONVERGÊNCIA POR TICKER EXIGE MESMO TICKER",
    )

    # 61
    assert_test(
        context["mandatory_policy"]
        ["do_not_generalize_causes_across_assets"]
        is True,
        "CAUSA NÃO PASSA ENTRE ATIVOS",
    )

    # 62
    assert_test(
        context["mandatory_policy"]
        ["do_not_generalize_conditions_across_signals"]
        is True,
        "CONDIÇÃO NÃO PASSA ENTRE SINAIS",
    )

    # 63
    assert_test(
        context["mandatory_policy"]
        ["summary_must_preserve_evidence_scope"]
        is True,
        "SÍNTESE PRESERVA ESCOPO DA EVIDÊNCIA",
    )

    # 64
    assert_test(
        "convergência exige evidência comparável"
        in system_prompt_lower
        and
        "simples existência de sinais positivos"
        in system_prompt_lower,
        "PROMPT DIFERENCIA CONVERGÊNCIA DE SINAIS POSITIVOS",
    )

    # 65
    assert_test(
        "coexistência de evidências positivas"
        in system_prompt_lower
        and
        "não confunda coexistência com convergência"
        in system_prompt_lower,
        "PROMPT DIFERENCIA COEXISTÊNCIA DE CONVERGÊNCIA",
    )

    # 66
    assert_test(
        "não transfira causas entre ativos"
        in system_prompt_lower
        and
        "não pode ser utilizado para"
        in system_prompt_lower,
        "PROMPT PROÍBE TRANSFERÊNCIA CAUSAL ENTRE ATIVOS",
    )

    # 67
    assert_test(
        "não transfira causas entre grupos de sinais"
        in system_prompt_lower
        and
        "não autoriza afirmar que todos os ativos"
        in system_prompt_lower,
        "PROMPT PROÍBE GENERALIZAÇÃO ENTRE SINAIS",
    )

    # 68
    assert_test(
        "não condicione sinais já positivos sem evidência"
        in system_prompt_lower
        and
        "entrada ou entrada forte"
        in system_prompt_lower,
        "ENTRADA POSITIVA NÃO RECEBE CONDIÇÃO INVENTADA",
    )

    # 69
    assert_test(
        "toda causalidade deve preservar seu escopo"
        in system_prompt_lower
        and
        "exatamente àquele ativo ou sinal"
        in system_prompt_lower,
        "CAUSALIDADE PRESERVA ESCOPO",
    )

    # 70
    assert_test(
        "a síntese cio não pode ampliar o escopo da evidência"
        in system_prompt_lower
        and
        "não transforme subconjuntos em totalidade"
        in system_prompt_lower,
        "SÍNTESE NÃO AMPLIA EVIDÊNCIA",
    )

    # 71
    assert_test(
        "antes de declarar convergência"
        in system_prompt_lower
        and
        "se a comparação for por ticker, é o mesmo ticker?"
        in system_prompt_lower,
        "CHECKLIST DE CONVERGÊNCIA",
    )

    # 72
    assert_test(
        "antes de apresentar uma causa"
        in system_prompt_lower
        and
        "não foi transportada de outro ativo?"
        in system_prompt_lower,
        "CHECKLIST DE CAUSALIDADE",
    )

    # 73
    assert_test(
        "não transforme coexistência em convergência"
        in prompt_lower
        and
        "mesmo ticker deve aparecer"
        in prompt_lower,
        "USER PROMPT PROTEGE CONVERGÊNCIA",
    )

    # 74
    assert_test(
        "não transporte causas entre ativos"
        in prompt_lower
        and
        "uma condição associada a um ticker não pode ser transferida"
        in prompt_lower,
        "USER PROMPT PROTEGE CAUSALIDADE POR ATIVO",
    )

    # 75
    assert_test(
        "10. síntese cio" in prompt_lower
        and
        '"summary_must_preserve_evidence_scope": true'
        in prompt_lower,
        "USER PROMPT PROTEGE ESCOPO DA SÍNTESE",
    )

    # 76
    assert_test(
        "não diga que entrada ou entrada forte depende de confirmação"
        in prompt_lower
        and
        "explicitamente informado"
        in prompt_lower,
        "USER PROMPT NÃO CONDICIONA ENTRADA SEM EVIDÊNCIA",
    )

    # 77
    assert_test(
        result["policy"]
        ["convergence_requires_comparable_evidence"]
        is True,
        "RESULTADO EXIGE CONVERGÊNCIA COMPARÁVEL",
    )

    # 78
    assert_test(
        result["policy"]
        ["causal_scope_must_be_preserved"]
        is True,
        "RESULTADO PRESERVA ESCOPO CAUSAL",
    )

    # 79
    assert_test(
        result["policy"]
        ["cross_asset_causal_generalization_allowed"]
        is False,
        "RESULTADO PROÍBE GENERALIZAÇÃO ENTRE ATIVOS",
    )

    # 80
    assert_test(
        result["policy"]
        ["summary_evidence_scope_preserved"]
        is True,
        "RESULTADO PRESERVA ESCOPO NA SÍNTESE",
    )

    # 81
    assert_test(
        "convergência exige evidência comparável"
        in sent_system_prompt
        and
        "não transfira causas entre ativos"
        in sent_system_prompt
        and
        "a síntese cio não pode ampliar o escopo da evidência"
        in sent_system_prompt,
        "NVIDIA RECEBE GOVERNANÇA SISTÊMICA V1.2",
    )

    # 82
    assert_test(
        "não transforme coexistência em convergência"
        in sent_user_prompt
        and
        "não transporte causas entre ativos"
        in sent_user_prompt
        and
        "a síntese não pode ampliar o escopo das evidências"
        in sent_user_prompt,
        "NVIDIA RECEBE GOVERNANÇA OPERACIONAL V1.2",
    )

    # ========================================================
    # NOVOS TESTES — GOVERNANÇA SEMÂNTICA V1.3
    # ========================================================

    # 83
    assert_test(
        context["mandatory_policy"]["status_label_does_not_imply_cause"] is True,
        "STATUS NÃO IMPLICA CAUSA",
    )

    # 84
    assert_test(
        context["mandatory_policy"]["quantifiers_require_explicit_evidence"] is True,
        "QUANTIFICADORES EXIGEM EVIDÊNCIA",
    )

    # 85
    assert_test(
        context["mandatory_policy"]["methodology_does_not_imply_signal_cause"] is True,
        "METODOLOGIA NÃO IMPLICA CAUSA DO SINAL",
    )

    # 86
    assert_test(
        context["mandatory_policy"]["methodology_does_not_imply_future_signal_change"] is True,
        "METODOLOGIA NÃO IMPLICA MUDANÇA FUTURA",
    )

    # 87
    assert_test(
        context["mandatory_policy"]["do_not_infer_condition_from_status_name"] is True
        and context["mandatory_policy"]["do_not_create_group_statistics"] is True,
        "SEM INFERÊNCIA DE STATUS OU ESTATÍSTICA INVENTADA",
    )

    # 88
    assert_test(
        "o nome ou rótulo de um status não prova sua causa" in system_prompt_lower
        and "não derive causa a partir da semântica do status" in system_prompt_lower,
        "PROMPT PROÍBE CAUSA DERIVADA DO STATUS",
    )

    # 89
    assert_test(
        "quantificadores exigem evidência explícita" in system_prompt_lower
        and "não crie estatística ou distribuição implícita" in system_prompt_lower,
        "PROMPT PROÍBE QUANTIFICADOR SEM EVIDÊNCIA",
    )

    # 90
    assert_test(
        "metodologia não é causa automática do sinal" in system_prompt_lower
        and "não use a arquitetura do motor para completar lacunas" in system_prompt_lower,
        "PROMPT SEPARA METODOLOGIA DE CAUSALIDADE",
    )

    # 91
    assert_test(
        "não preveja o que fará um sinal mudar" in system_prompt_lower
        and "mudança futura de sinal" in system_prompt_lower,
        "PROMPT PROÍBE PREVISÃO DE MUDANÇA DE SINAL",
    )

    # 92
    assert_test(
        "preserve a diferença entre rótulo e explicação" in system_prompt_lower
        and "preserve a diferença entre lista e estatística" in system_prompt_lower,
        "PROMPT PRESERVA RÓTULO E LISTA",
    )

    # 93
    assert_test(
        "não transforme o nome de um status em causa" in prompt_lower
        and "não transforme metodologia do sistema em causa do sinal" in prompt_lower
        and "não use quantificadores sem evidência explícita" in prompt_lower,
        "USER PROMPT RECEBE TRAVAS V1.3",
    )

    # 94
    assert_test(
        result["policy"]["status_label_implies_cause"] is False
        and result["policy"]["quantifiers_require_explicit_evidence"] is True,
        "RESULTADO PROÍBE CAUSA POR STATUS E QUANTIFICADOR LIVRE",
    )

    # 95
    assert_test(
        result["policy"]["methodology_implies_signal_cause"] is False
        and result["policy"]["methodology_implies_future_signal_change"] is False,
        "RESULTADO PROÍBE CAUSALIDADE POR METODOLOGIA",
    )

    # 96
    assert_test(
        result["policy"]["group_statistics_may_be_invented"] is False,
        "RESULTADO PROÍBE ESTATÍSTICA DE GRUPO INVENTADA",
    )

    # 97
    assert_test(
        "o nome ou rótulo de um status não prova sua causa" in sent_system_prompt
        and "quantificadores exigem evidência explícita" in sent_system_prompt
        and "metodologia não é causa automática do sinal" in sent_system_prompt
        and "não transforme o nome de um status em causa" in sent_user_prompt
        and "não use quantificadores sem evidência explícita" in sent_user_prompt,
        "NVIDIA RECEBE GOVERNANÇA V1.3",
    )

    # ========================================================
    # NOVOS TESTES — GOVERNANÇA SEMÂNTICA V1.4
    # ========================================================

    # 98
    assert_test(
        context["mandatory_policy"]["methodology_is_not_timing"] is True,
        "METODOLOGIA OU ARQUITETURA NÃO É TIMING",
    )

    # 99
    assert_test(
        context["mandatory_policy"]["restrictions_do_not_imply_operational_consequences"] is True,
        "RESTRIÇÃO NÃO IMPLICA CONSEQUÊNCIA OPERACIONAL",
    )

    # 100
    assert_test(
        context["mandatory_policy"]["descriptive_analysis_must_not_become_prescriptive"] is True
        and context["mandatory_policy"]["prescriptive_language_requires_explicit_source_attribution"] is True,
        "DESCRIÇÃO NÃO VIRA PRESCRIÇÃO",
    )

    # 101
    assert_test(
        "metodologia ou arquitetura não é timing" in system_prompt_lower
        and "não o transforme em \"método de timing\"" in system_prompt_lower,
        "PROMPT SEPARA METODOLOGIA DE TIMING",
    )

    # 102
    assert_test(
        "restrição não implica consequência operacional nova" in system_prompt_lower
        and "limita exposição" in system_prompt_lower
        and "salvo quando essa consequência estiver explicitamente registrada" in system_prompt_lower,
        "PROMPT PROÍBE CONSEQUÊNCIA OPERACIONAL INVENTADA",
    )

    # 103
    assert_test(
        "descrição não pode virar prescrição" in system_prompt_lower
        and "prescriptive_language_requires_explicit_source_attribution" not in system_prompt_lower
        and "devem ser respeitadas" in system_prompt_lower,
        "PROMPT PROÍBE PRESCRIÇÃO PRÓPRIA",
    )

    # 104
    assert_test(
        "não transforme metodologia ou arquitetura em timing" in prompt_lower
        and "não transforme restrição em consequência operacional não fornecida" in prompt_lower
        and "não transforme descrição em prescrição" in prompt_lower,
        "USER PROMPT RECEBE TRAVAS V1.4",
    )

    # 105
    assert_test(
        result["policy"]["methodology_implies_timing"] is False
        and result["policy"]["restrictions_imply_operational_consequences"] is False,
        "RESULTADO SEPARA TIMING E CONSEQUÊNCIA OPERACIONAL",
    )

    # 106
    assert_test(
        result["policy"]["ai_created_prescriptive_language_without_source"] is False
        and result["policy"]["prescriptive_language_requires_source_attribution"] is True,
        "RESULTADO PROÍBE PRESCRIÇÃO SEM FONTE",
    )

    # 107
    assert_test(
        "metodologia ou arquitetura não é timing" in sent_system_prompt
        and "restrição não implica consequência operacional nova" in sent_system_prompt
        and "descrição não pode virar prescrição" in sent_system_prompt
        and "não transforme metodologia ou arquitetura em timing" in sent_user_prompt
        and "não transforme restrição em consequência operacional não fornecida" in sent_user_prompt
        and "não transforme descrição em prescrição" in sent_user_prompt,
        "NVIDIA RECEBE GOVERNANÇA V1.4",
    )

    # ========================================================
    # NOVOS TESTES — BARREIRA DE FIDELIDADE SEMÂNTICA V1.5
    # ========================================================

    # 108
    assert_test(
        context["mandatory_policy"]["semantic_fidelity_barrier_enabled"] is True
        and context["mandatory_policy"]["semantic_violations_must_fail_safe"] is True
        and context["mandatory_policy"]["semantic_validation_must_not_change_source_data"] is True,
        "BARREIRA DE FIDELIDADE V1.5 ATIVA",
    )

    # 109
    valid_semantic_result = validate_ai_analysis_semantics(
        (
            "Há sinais específicos produzidos pelos sistemas e há "
            "restrições globais ativas. Os fatos coexistem. "
            "A decisão final permanece humana."
        ),
        context,
    )

    assert_test(
        valid_semantic_result["status"] == "PASS"
        and valid_semantic_result["violations"] == []
        and valid_semantic_result["fail_safe"] is True,
        "RELATÓRIO DESCRITIVO CONFORME PASSA",
    )

    # 110
    try:
        validate_ai_analysis_semantics(
            "Há predominantemente sinais de espera no conjunto.",
            context,
        )
        raise AssertionError(
            "Quantificador distributivo sem evidência deveria ser bloqueado."
        )
    except CIOAISemanticValidationError:
        pass

    assert_test(
        True,
        "QUANTIFICADOR SEM EVIDÊNCIA É BLOQUEADO",
    )

    # 111
    try:
        validate_ai_analysis_semantics(
            "O Kill Switch impede qualquer exposição adicional.",
            context,
        )
        raise AssertionError(
            "Consequência operacional inventada deveria ser bloqueada."
        )
    except CIOAISemanticValidationError:
        pass

    assert_test(
        True,
        "CONSEQUÊNCIA OPERACIONAL INVENTADA É BLOQUEADA",
    )

    # 112
    try:
        validate_ai_analysis_semantics(
            "A situação exige cautela.",
            context,
        )
        raise AssertionError(
            "Prescrição sem fonte deveria ser bloqueada."
        )
    except CIOAISemanticValidationError:
        pass

    assert_test(
        True,
        "PRESCRIÇÃO SEM FONTE É BLOQUEADA",
    )

    # 113
    context_with_explicit_consequence = deepcopy(context)
    context_with_explicit_consequence["risk"]["restrictions"].append(
        {
            "code": "SOURCE_EXPLICIT_OPERATIONAL_RULE",
            "severity": "CRITICAL",
            "source": "TEST_SOURCE",
            "description": (
                "O Kill Switch impede qualquer exposição adicional."
            ),
        }
    )

    explicit_consequence_result = validate_ai_analysis_semantics(
        (
            "Segundo TEST_SOURCE, o Kill Switch impede qualquer "
            "exposição adicional."
        ),
        context_with_explicit_consequence,
    )

    assert_test(
        explicit_consequence_result["status"] == "PASS",
        "CONSEQUÊNCIA EXPLÍCITA NA FONTE É PERMITIDA",
    )

    # 114
    semantic_fixture = deepcopy(fixture)
    semantic_fixture_before = deepcopy(semantic_fixture)

    validate_ai_analysis_semantics(
        "Os sistemas apresentam sinais distintos. A decisão final permanece humana.",
        build_ai_context(semantic_fixture),
    )

    assert_test(
        semantic_fixture == semantic_fixture_before,
        "VALIDADOR SEMÂNTICO NÃO ALTERA ORCHESTRATOR",
    )

    # 115
    assert_test(
        result["semantic_validation"]["status"] == "PASS"
        and result["policy"]["semantic_fidelity_barrier_enabled"] is True
        and result["policy"]["semantic_validation_passed"] is True
        and result["policy"]["semantic_violations_accepted"] is False
        and result["policy"]["semantic_fail_safe_enabled"] is True,
        "RESULTADO EXPÕE BARREIRA SEMÂNTICA APROVADA",
    )

    # 116
    blocked_client = FakeNVIDIAClient(
        contents=[
            "O Kill Switch impede qualquer exposição adicional.",
            "O Kill Switch impede qualquer exposição adicional.",
        ]
    )

    try:
        run_cio_ai(
            fixture,
            client=blocked_client,
        )
        raise AssertionError(
            "run_cio_ai deveria rejeitar a segunda resposta "
            "semanticamente inválida."
        )
    except CIOAISemanticValidationError:
        pass

    assert_test(
        len(blocked_client.completions.calls) == 2,
        "RUN CIO AI APLICA FAIL-SAFE APÓS UMA AUTOCORREÇÃO",
    )

    # 117
    assert_test(
        CIOAISemanticValidationError.__mro__[1] is CIOAIResponseError,
        "ERRO SEMÂNTICO INTEGRA HIERARQUIA DE RESPOSTA",
    )

    # ========================================================
    # NOVOS TESTES — AUTOCORREÇÃO SEMÂNTICA CONTROLADA V1.5
    # ========================================================

    # 118
    correction_client = FakeNVIDIAClient(
        contents=[
            "O Kill Switch impede qualquer exposição adicional.",
            (
                "Há uma restrição global de risco registrada no contexto. "
                "A decisão final permanece humana."
            ),
        ]
    )

    corrected_result = run_cio_ai(
        fixture,
        client=correction_client,
    )

    assert_test(
        corrected_result["status"] == "OK"
        and corrected_result["semantic_validation"]["status"] == "PASS"
        and corrected_result["semantic_validation"]["retry_used"] is True
        and corrected_result["policy"]["semantic_auto_correction_used"] is True,
        "AUTOCORREÇÃO SEMÂNTICA RECUPERA RESPOSTA INVÁLIDA",
    )

    # 119
    assert_test(
        len(correction_client.completions.calls) == 2,
        "AUTOCORREÇÃO USA EXATAMENTE UMA SEGUNDA CHAMADA",
    )

    # 120
    correction_call = correction_client.completions.calls[1]
    correction_user_prompt = (
        correction_call["messages"][1]["content"].lower()
    )

    assert_test(
        "classes de violação detectadas:" in correction_user_prompt
        and "unsupported_operational_consequence"
        in correction_user_prompt
        and "não altere sinais" in correction_user_prompt
        and "não altere scores" in correction_user_prompt
        and "não altere rankings" in correction_user_prompt,
        "PROMPT DE AUTOCORREÇÃO PRESERVA DADOS E SINAIS",
    )

    # 121
    assert_test(
        corrected_result["analysis"]
        == (
            "Há uma restrição global de risco registrada no contexto. "
            "A decisão final permanece humana."
        ),
        "RESULTADO PUBLICA SOMENTE ANÁLISE CORRIGIDA E VALIDADA",
    )

    # 122
    no_retry_client = FakeNVIDIAClient(
        content=(
            "Os sistemas apresentam sinais distintos. "
            "A decisão final permanece humana."
        )
    )

    no_retry_result = run_cio_ai(
        fixture,
        client=no_retry_client,
    )

    assert_test(
        len(no_retry_client.completions.calls) == 1
        and no_retry_result["semantic_validation"]["retry_used"] is False
        and no_retry_result["policy"]["semantic_auto_correction_used"] is False,
        "RESPOSTA CONFORME NÃO ACIONA AUTOCORREÇÃO",
    )

    # 123
    assert_test(
        corrected_result["semantic_validation"]["max_semantic_retries"] == 1
        and corrected_result["semantic_validation"]["first_rejection_recorded"] is True
        and corrected_result["policy"]["semantic_auto_correction_enabled"] is True
        and corrected_result["policy"]["semantic_auto_correction_max_retries"] == 1,
        "AUTOCORREÇÃO LIMITADA A UMA TENTATIVA",
    )

    # 124
    assert_test(
        "a redação rejeitada não é fornecida"
        in correction_user_prompt
        and "reconstrua a análise integral do zero"
        in correction_user_prompt
        and "contexto estruturado original"
        in correction_user_prompt,
        "AUTOCORREÇÃO RECONSTRÓI SEM REENVIAR RESPOSTA REJEITADA",
    )

    # 125
    detected_classes_block = (
        correction_user_prompt
        .split("classes de violação detectadas:", 1)[1]
        .strip()
        .split("\n\n", 1)[0]
    )

    assert_test(
        detected_classes_block.strip()
        == "- unsupported_operational_consequence",
        "AUTOCORREÇÃO RECEBE SOMENTE CLASSE REAL DA VIOLAÇÃO",
    )

    # 126
    assert_test(
        "formulação estritamente descritiva"
        in correction_user_prompt
        and "menor alcance"
        in correction_user_prompt
        and "use exclusivamente o contexto estruturado original"
        in correction_user_prompt,
        "AUTOCORREÇÃO ORIENTA REDUÇÃO DO ALCANCE SEMÂNTICO",
    )

    # ========================================================
    # TESTES DE PRODUÇÃO — RECONSTRUÇÃO SEM CONTAMINAÇÃO
    # ========================================================

    # 127
    production_client = FakeNVIDIAClient(
        contents=[
            (
                "A maioria dos sinais exige cautela. "
                "A restrição limita exposição e impede entrada. "
                "O cenário deve ser considerado."
            ),
            (
                "Há sinais distintos registrados no contexto. "
                "Há uma restrição global registrada. "
                "A decisão final permanece humana."
            ),
        ]
    )

    production_result = run_cio_ai(
        fixture,
        client=production_client,
    )

    production_call = production_client.completions.calls[1]
    production_system_prompt = (
        production_call["messages"][0]["content"].lower()
    )
    production_prompt = (
        production_call["messages"][1]["content"].lower()
    )

    assert_test(
        "unsupported_distributive_quantifier" in production_prompt
        and "unsupported_operational_consequence" in production_prompt
        and "unsupported_prescriptive_language" in production_prompt,
        "AUTOCORREÇÃO RECEBE AS CLASSES DAS VIOLAÇÕES REAIS",
    )

    # 128
    rejected_production_text = (
        "a maioria dos sinais exige cautela. "
        "a restrição limita exposição e impede entrada. "
        "o cenário deve ser considerado."
    )

    assert_test(
        rejected_production_text not in production_prompt
        and "a maioria dos sinais exige cautela" not in production_prompt
        and "o cenário deve ser considerado" not in production_prompt,
        "RESPOSTA REJEITADA NÃO É REINJETADA NO PROMPT",
    )

    # 129
    assert_test(
        "limita exposição" not in production_prompt
        and "impede entrada" not in production_prompt
        and "limita exposição" not in production_system_prompt
        and "impede entrada" not in production_system_prompt,
        "DETALHES LITERAIS DA VIOLAÇÃO NÃO SÃO REINJETADOS",
    )

    # 130
    assert_test(
        "a redação rejeitada não é fornecida" in production_prompt
        and "reconstrua a análise integral do zero" in production_prompt
        and "contexto estruturado original" in production_prompt,
        "PROMPT EXPLICITA RECONSTRUÇÃO SEM TEXTO REJEITADO",
    )

    # 131
    assert_test(
        production_result["status"] == "OK"
        and production_result["semantic_validation"]["status"] == "PASS"
        and production_result["semantic_validation"]["retry_used"] is True
        and len(production_client.completions.calls) == 2,
        "RECONSTRUÇÃO SEM CONTAMINAÇÃO RECUPERA CASO DE PRODUÇÃO",
    )

    # 132
    try:
        validate_ai_analysis_semantics(
            (
                'A expressão "a maioria" seria não suportada; '
                "por isso não foi utilizada como conclusão."
            ),
            context,
        )
        raise AssertionError(
            "Metacomentário com quantificador proibido deveria ser bloqueado."
        )
    except CIOAISemanticValidationError:
        pass

    assert_test(
        True,
        "BARREIRA CONTINUA BLOQUEANDO METACOMENTÁRIO INVÁLIDO",
    )

    # 133
    prescriptive_client = FakeNVIDIAClient(
        contents=[
            "O cenário deve ser considerado.",
            (
                "Há um cenário registrado no contexto. "
                "A decisão final permanece humana."
            ),
        ]
    )

    prescriptive_result = run_cio_ai(
        fixture,
        client=prescriptive_client,
    )

    prescriptive_prompt = (
        prescriptive_client.completions.calls[1]
        ["messages"][1]["content"].lower()
    )

    assert_test(
        "unsupported_prescriptive_language" in prescriptive_prompt
        and "o cenário deve ser considerado" not in prescriptive_prompt
        and prescriptive_result["semantic_validation"]["status"] == "PASS",
        "PRESCRIÇÃO É CORRIGIDA SEM REINJETAR FRASE REJEITADA",
    )

    # 134
    assert_test(
        "a resposta deve conter somente a nova análise final"
        in production_prompt
        and "não explique o processo de correção"
        in production_prompt
        and "rejeição ou validação" in production_prompt,
        "AUTOCORREÇÃO PROÍBE METACOMENTÁRIO SOBRE REPARO",
    )

    # 135
    assert_test(
        "contexto estruturado original:" in production_prompt
        and '"sp500_cycle"' in production_prompt
        and '"global_portfolio"' in production_prompt,
        "AUTOCORREÇÃO REUTILIZA CONTEXTO ORIGINAL DOS SISTEMAS",
    )

    # 136
    contamination_client = FakeNVIDIAClient(
        contents=[
            (
                "A maioria dos sinais limita exposição e impede entrada. "
                "O cenário deve ser considerado."
            ),
            (
                "Os sistemas registram sinais distintos. "
                "Há restrições registradas no contexto. "
                "A decisão final permanece humana."
            ),
        ]
    )

    contamination_result = run_cio_ai(
        fixture,
        client=contamination_client,
    )

    contamination_call = contamination_client.completions.calls[1]
    contamination_system_prompt = (
        contamination_call["messages"][0]["content"].lower()
    )
    contamination_prompt = (
        contamination_call["messages"][1]["content"].lower()
    )

    assert_test(
        contamination_result["semantic_validation"]["status"] == "PASS"
        and "a maioria dos sinais limita exposição e impede entrada"
        not in contamination_prompt
        and "o cenário deve ser considerado" not in contamination_prompt
        and "limita exposição" not in contamination_system_prompt
        and "impede entrada" not in contamination_system_prompt,
        "CASO COMBINADO É RECONSTRUÍDO SEM CONTAMINAÇÃO TEXTUAL",
    )

    # 137
    assert_test(
        len(contamination_client.completions.calls) == 2
        and contamination_result["semantic_validation"]["retry_used"] is True
        and contamination_result["policy"]["semantic_auto_correction_used"] is True,
        "RECONSTRUÇÃO MANTÉM EXATAMENTE UMA AUTOCORREÇÃO SEMÂNTICA",
    )

    # ========================================================
    # TESTES DE RESILIÊNCIA NVIDIA — HTTP 503
    # ========================================================

    class Fake503Error(Exception):
        status_code = 503

    import agents.cio_ai_agent as cio_ai_module

    original_sleep = cio_ai_module.time.sleep
    sleep_calls = []
    cio_ai_module.time.sleep = lambda seconds: sleep_calls.append(seconds)

    try:
        # 138 — um 503 e depois sucesso
        retry_once_client = FakeNVIDIAClient(
            contents=[
                Fake503Error("Service temporarily overloaded"),
                (
                    "Os sistemas apresentam sinais distintos. "
                    "A decisão final permanece humana."
                ),
            ]
        )

        retry_once_result = run_cio_ai(
            fixture,
            client=retry_once_client,
        )

        assert_test(
            retry_once_result["status"] == "OK"
            and len(retry_once_client.completions.calls) == 2
            and sleep_calls == [10],
            "NVIDIA 503 RECUPERA NA SEGUNDA TENTATIVA",
        )

        # 139 — dois 503 e depois sucesso
        sleep_calls.clear()
        retry_twice_client = FakeNVIDIAClient(
            contents=[
                Fake503Error("Service Unavailable"),
                Fake503Error("error code: 503"),
                (
                    "Os sistemas apresentam sinais distintos. "
                    "A decisão final permanece humana."
                ),
            ]
        )

        retry_twice_result = run_cio_ai(
            fixture,
            client=retry_twice_client,
        )

        assert_test(
            retry_twice_result["status"] == "OK"
            and len(retry_twice_client.completions.calls) == 3
            and sleep_calls == [10, 30],
            "NVIDIA 503 RECUPERA NA TERCEIRA TENTATIVA",
        )

        # 140 — três 503: fail-safe
        sleep_calls.clear()
        retry_fail_client = FakeNVIDIAClient(
            contents=[
                Fake503Error("Service Unavailable"),
                Fake503Error("Service temporarily overloaded"),
                Fake503Error("error code: 503"),
            ]
        )

        try:
            run_cio_ai(
                fixture,
                client=retry_fail_client,
            )
            raise AssertionError(
                "Três erros 503 deveriam encerrar em fail-safe."
            )
        except CIOAIResponseError:
            pass

        assert_test(
            len(retry_fail_client.completions.calls) == 3
            and sleep_calls == [10, 30],
            "NVIDIA 503 PERSISTENTE FALHA APÓS TRÊS TENTATIVAS",
        )

        # 141 — erro não 503: não repetir
        sleep_calls.clear()
        non_503_client = FakeNVIDIAClient(
            contents=[
                RuntimeError("erro permanente de autenticação")
            ]
        )

        try:
            run_cio_ai(
                fixture,
                client=non_503_client,
            )
            raise AssertionError(
                "Erro não 503 deveria falhar sem retry técnico."
            )
        except CIOAIResponseError:
            pass

        assert_test(
            len(non_503_client.completions.calls) == 1
            and sleep_calls == [],
            "ERRO NVIDIA NÃO 503 NÃO É REPETIDO",
        )

        # 142 — 503 durante a única autocorreção semântica
        sleep_calls.clear()
        semantic_503_client = FakeNVIDIAClient(
            contents=[
                "O cenário deve ser considerado.",
                Fake503Error("Service temporarily overloaded"),
                (
                    "Há um cenário registrado no contexto. "
                    "A decisão final permanece humana."
                ),
            ]
        )

        semantic_503_result = run_cio_ai(
            fixture,
            client=semantic_503_client,
        )

        assert_test(
            semantic_503_result["status"] == "OK"
            and semantic_503_result["semantic_validation"]["retry_used"] is True
            and len(semantic_503_client.completions.calls) == 3
            and sleep_calls == [10],
            "503 NA AUTOCORREÇÃO PRESERVA UMA ÚNICA TENTATIVA SEMÂNTICA",
        )

    finally:
        cio_ai_module.time.sleep = original_sleep

    # ========================================================
    # RESULTADO FINAL
    # ========================================================

    print("=" * 70)
    print(
        "CIO AI AGENT V1.5 — 142 TESTES OK"
    )
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
