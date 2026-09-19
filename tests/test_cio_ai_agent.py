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
    validate_orchestrator_context,
    build_ai_context,
    build_ai_prompt,
    run_cio_ai,
    analyze_cio_context,
)


# ============================================================
# CLIENTE NVIDIA SIMULADO
# ============================================================

class FakeCompletions:

    def __init__(self, content=None, raise_error=False):
        self.content = content
        self.raise_error = raise_error
        self.last_call = None

    def create(self, **kwargs):

        self.last_call = deepcopy(kwargs)

        if self.raise_error:
            raise RuntimeError("NVIDIA indisponível")

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=self.content
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
    ):
        self.completions = FakeCompletions(
            content=content,
            raise_error=raise_error,
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
    print("TESTE — CIO AI AGENT V1.3 / NVIDIA NIM")
    print("=" * 70)

    fixture = build_orchestrator_fixture()

    original_fixture = deepcopy(fixture)

    # 1
    assert_test(
        CIO_AI_VERSION == "1.3",
        "IDENTIFICAÇÃO V1.3",
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
        "a síntese não pode ampliar o escopo das evidências"
        in prompt_lower
        and
        "não use a causa de um subconjunto para explicar todo o conjunto"
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
    # RESULTADO FINAL
    # ========================================================

    print("=" * 70)
    print(
        "CIO AI AGENT V1.3 — 97 TESTES OK"
    )
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
