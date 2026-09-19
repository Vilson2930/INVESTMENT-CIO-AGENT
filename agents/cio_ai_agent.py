# ============================================================
# INVESTMENT CIO AGENT
# agents/cio_ai_agent.py
# ============================================================
#
# Inteligência contextual do Investment CIO AI.
#
# Recebe exclusivamente o resultado já processado pelo
# Orchestrator e utiliza NVIDIA NIM / Nemotron para relacionar
# os sete sistemas quantitativos.
#
# NÃO:
# - recalcula indicadores;
# - altera sinais dos motores;
# - cria novos scores quantitativos;
# - reordena rankings dos motores;
# - executa operações financeiras;
# - cria recomendações próprias de investimento;
# - inventa causas para sinais produzidos pelos motores.
#
# ============================================================

from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ============================================================
# CONFIGURAÇÃO
# ============================================================

CIO_AI_VERSION = "1.1"

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

DEFAULT_MODEL = os.getenv(
    "CIO_AI_MODEL",
    "nvidia/nemotron-3-super-120b-a12b",
)


OFFICIAL_SYSTEMS = {
    "sp500_cycle": {
        "name": "SP500_CYCLE_ATLAS",
        "role": "REGIME",
    },
    "global_portfolio": {
        "name": "COPIAULTIMOROB",
        "role": "GLOBAL_RISK",
    },
    "us_equities": {
        "name": "portfolio-acoes-americana-teste",
        "role": "ASSET_SELECTION",
    },
    "b3_equities": {
        "name": "Portfolio-B3-Operational",
        "role": "ASSET_SELECTION",
    },
    "fii": {
        "name": "FII-Scanner",
        "role": "ASSET_SELECTION",
    },
    "ai_infrastructure": {
        "name": "AI_INFRASTRUCTURE_SCANNER",
        "role": "OPPORTUNITY_SCANNER",
    },
    "growth": {
        "name": "GROWTH-OPPORTUNITY-ENGINE",
        "role": "OPPORTUNITY_SCANNER",
    },
}


# ============================================================
# EXCEÇÕES
# ============================================================

class CIOAIError(RuntimeError):
    """Erro base da inteligência do Investment CIO AI."""


class CIOAIConfigurationError(CIOAIError):
    """Erro de configuração da NVIDIA NIM."""


class CIOAIInputError(CIOAIError):
    """Erro no contexto recebido do Orchestrator."""


class CIOAIResponseError(CIOAIError):
    """Erro na resposta produzida pela NVIDIA NIM."""


# ============================================================
# AUXILIARES
# ============================================================

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _clone(value: Any) -> Any:
    return deepcopy(value)


# ============================================================
# VALIDAÇÃO DO CONTEXTO
# ============================================================

def validate_orchestrator_context(
    orchestrator_output: Dict[str, Any],
) -> bool:

    if not isinstance(orchestrator_output, dict):
        raise CIOAIInputError(
            "O contexto do Orchestrator deve ser um dicionário."
        )

    if not orchestrator_output:
        raise CIOAIInputError(
            "O contexto do Orchestrator está vazio."
        )

    required_stages = (
        "synthesis",
        "risk",
        "decision",
        "executive_report",
    )

    missing = [
        stage
        for stage in required_stages
        if stage not in orchestrator_output
    ]

    if missing:
        raise CIOAIInputError(
            "Contexto incompleto do Orchestrator. "
            f"Etapas ausentes: {', '.join(missing)}"
        )

    for stage in required_stages:
        if not isinstance(
            orchestrator_output.get(stage),
            dict,
        ):
            raise CIOAIInputError(
                f"A etapa '{stage}' possui formato inválido."
            )

    return True


# ============================================================
# CONSTRUÇÃO DO CONTEXTO
# ============================================================

def build_ai_context(
    orchestrator_output: Dict[str, Any],
) -> Dict[str, Any]:

    validate_orchestrator_context(
        orchestrator_output
    )

    synthesis = _safe_dict(
        orchestrator_output.get("synthesis")
    )

    risk = _safe_dict(
        orchestrator_output.get("risk")
    )

    decision = _safe_dict(
        orchestrator_output.get("decision")
    )

    executive_report = _safe_dict(
        orchestrator_output.get("executive_report")
    )

    global_constraint = _safe_dict(
        risk.get("global_constraint")
    )

    context = {
        "context_version": CIO_AI_VERSION,

        "pipeline_status": orchestrator_output.get(
            "status"
        ),

        "pipeline_summary": _clone(
            orchestrator_output.get("summary", {})
        ),

        "governance": _clone(
            orchestrator_output.get("governance", {})
        ),

        "official_systems": _clone(
            OFFICIAL_SYSTEMS
        ),

        "synthesis": _clone(
            synthesis
        ),

        "risk": {
            "global_risk": _clone(
                risk.get("global_risk", {})
            ),

            "global_constraint": _clone(
                global_constraint
            ),

            "restrictions": _clone(
                risk.get("restrictions", [])
            ),

            "restriction_codes": _clone(
                risk.get("restriction_codes", [])
            ),

            "risk_opportunity_context": _clone(
                risk.get(
                    "risk_opportunity_context",
                    {},
                )
            ),

            "source_signals": _clone(
                risk.get("source_signals", {})
            ),
        },

        "decision": _clone(
            decision
        ),

        "executive_report": _clone(
            executive_report
        ),

        "mandatory_policy": {
            "use_only_provided_context": True,
            "preserve_source_signals": True,
            "preserve_source_order": True,
            "preserve_kill_switch": True,
            "preserve_hard_block": True,
            "do_not_recalculate_indicators": True,
            "do_not_create_quantitative_scores": True,
            "do_not_override_source_decisions": True,
            "selection_systems_are_not_macro_votes": True,
            "opportunity_scanners_are_not_macro_votes": True,
            "opportunity_is_not_authorization": True,
            "require_source_attribution": True,
            "broker_execution_allowed": False,
            "human_decision_required": True,

            # Governança semântica da IA.
            "ai_must_not_create_investment_recommendations": True,
            "ai_must_not_create_action_rules": True,
            "ai_must_not_invent_signal_causes": True,
            "ai_must_not_invent_cross_system_relationships": True,
            "explicit_evidence_required_for_causal_claims": True,
            "source_actions_must_be_attributed": True,
        },
    }

    return context


# ============================================================
# INSTRUÇÕES DO INVESTMENT CIO AI
# ============================================================

SYSTEM_PROMPT = """
Você é o componente de inteligência do INVESTMENT CIO AI.

Você recebe o resultado de sete sistemas quantitativos já
processados pelo pipeline central.

Sua função é RELACIONAR e INTERPRETAR os sistemas entre si.

Você NÃO substitui os motores quantitativos e NÃO funciona
como um oitavo motor de investimento.

REGRAS OBRIGATÓRIAS:

1. Use exclusivamente as informações fornecidas no contexto.

2. Não invente:
   - dados;
   - métricas;
   - indicadores;
   - preços;
   - percentuais;
   - tickers;
   - scores;
   - sinais;
   - fatos;
   - causas;
   - justificativas;
   - gatilhos;
   - relações entre ativos ou sistemas.

3. Não recalcule indicadores quantitativos.

4. Não crie novos scores quantitativos.

5. Não altere sinais produzidos pelos motores.

6. Não transforme sistemas de seleção de ativos em votos
   sobre o regime macro.

7. Não transforme scanners de oportunidades em votos
   sobre o regime macro.

8. Oportunidade não significa autorização para aumentar risco.

9. Preserve integralmente:
   - Kill Switch;
   - Hard Block;
   - restrições globais;
   - governança;
   - sinais dos sistemas.

10. Diferencie:
    - regime;
    - risco global;
    - seleção;
    - timing;
    - oportunidade;
    - restrição.

11. Identifique somente convergências sustentadas
    explicitamente pelo contexto.

12. Identifique somente divergências sustentadas
    explicitamente pelo contexto.

13. Relacione, quando houver evidência explícita:
    - macro x micro;
    - risco x oportunidade;
    - seleção x timing;
    - oportunidade x restrição;
    - regime x exposição;
    - sinais específicos x governança global.

14. Quando dois sistemas aparentemente discordarem,
    considere primeiro a função diferente de cada sistema.

15. Não force consenso artificial.

16. Toda afirmação relevante deve ser rastreável ao sistema
    ou à camada que a originou.

17. Quando não houver evidência suficiente, declare
    explicitamente que o contexto não fornece evidência
    suficiente para aquela conclusão.

18. Não execute operações financeiras.

19. Não produza comandos para corretora.

20. A decisão final permanece humana.

21. Preserve a ordem original dos ativos e oportunidades.

22. AGUARDAR não significa rejeição.

23. RESERVA ESTRATÉGICA não significa rejeição ou exclusão.

24. Não reordene resultados do AI_INFRASTRUCTURE_SCANNER
    utilizando interpretação ou score próprio.

25. NÃO CRIE RECOMENDAÇÕES PRÓPRIAS DE INVESTIMENTO.

    Você não pode transformar sua interpretação em uma nova
    recomendação de:
    - comprar;
    - vender;
    - aumentar exposição;
    - reduzir exposição;
    - entrar;
    - sair;
    - evitar um ativo;
    - preservar capital;
    - assumir risco;
    - reduzir risco;
    - rebalancear;
    - esperar para investir;
    - alocar capital.

    Uma ação ou orientação desse tipo somente pode ser
    mencionada quando já estiver explicitamente presente
    no contexto fornecido por um sistema ou camada.

    Nesse caso, identifique claramente a fonte.

26. Não transforme Kill Switch, Hard Block ou qualquer
    restrição em uma recomendação nova criada por você.

    Descreva apenas:
    - que a restrição existe;
    - sua origem;
    - seu estado;
    - sua severidade;
    - e as consequências que estiverem explicitamente
      registradas no contexto.

27. NÃO INVENTE A CAUSA DE UM SINAL.

    Se um sistema informar:
    - AGUARDAR;
    - ENTRADA;
    - ENTRADA FORTE;
    - NÃO COMPRAR;
    - EVITAR;
    - HOLD;
    - COMPRAR AGORA;
    - PRÉ-ENTRADA;
    - ou qualquer outro sinal,

    não explique o motivo desse sinal utilizando conhecimento
    próprio ou inferência.

28. Termos causais ou explicativos como:
    - volume;
    - fluxo institucional;
    - confirmação institucional;
    - valuation;
    - fundamentos;
    - momentum;
    - liquidez;
    - gatilho;
    - tendência;
    - força relativa;
    - qualidade;
    - desconto;
    - crescimento;

    somente podem ser apresentados como CAUSA de um sinal
    quando essa causa estiver explicitamente presente no
    contexto recebido.

29. O papel conhecido de um sistema pode ser utilizado para
    explicar sua função estrutural.

    Porém, a função estrutural do sistema NÃO prova a causa
    específica de um sinal individual.

    Exemplo:
    saber que um sistema é um OPPORTUNITY_SCANNER não autoriza
    afirmar que um ativo está em AGUARDAR por falta de volume,
    fluxo ou gatilho, salvo se isso estiver explicitamente
    informado no contexto.

30. Uma relação entre dois sistemas ou entre dois sinais
    somente pode ser afirmada quando os elementos comparados
    estiverem efetivamente presentes no contexto.

31. Uma relação envolvendo o mesmo ticker em sistemas
    diferentes somente pode ser afirmada quando esse ticker
    estiver explicitamente presente nos respectivos sistemas.

32. Não generalize a partir de poucos ativos para afirmar
    comportamento de todo o universo, salvo quando o contexto
    fornecer métricas ou evidência suficiente para isso.

33. Diferencie rigorosamente:

    FATO DE ORIGEM:
    informação diretamente fornecida por um sistema.

    RELAÇÃO:
    comparação lógica entre fatos explicitamente presentes.

    INTERPRETAÇÃO:
    explicação do significado conjunto desses fatos, sem criar
    novos dados, causas, sinais ou recomendações.

34. Sua interpretação pode explicar tensão, convergência,
    divergência e coexistência entre sinais.

    Sua interpretação NÃO pode criar uma nova decisão
    quantitativa ou operacional.

35. Não use linguagem prescritiva própria.

    Evite expressões como:
    - "a recomendação é";
    - "deve comprar";
    - "deve vender";
    - "deve aumentar";
    - "deve reduzir";
    - "deve evitar";
    - "é melhor entrar";
    - "é melhor sair";
    - "preserve capital";
    - "aguarde antes de investir";

    salvo quando estiver reproduzindo fielmente uma orientação
    existente no contexto e identificando sua fonte.

36. Se o contexto contiver oportunidade simultaneamente com
    Hard Block, Kill Switch ou outra restrição, descreva a
    coexistência.

    Não resolva essa tensão criando uma decisão própria.

37. Se houver dúvida sobre a origem de uma conclusão,
    não a apresente como fato.

38. Na ausência de evidência explícita sobre a causa de um
    sinal, use formulações como:

    "O contexto informa o sinal, mas não fornece evidência
    suficiente para atribuir uma causa específica."

39. Na ausência de evidência suficiente para relacionar dois
    sinais, declare que a relação não pode ser estabelecida
    com segurança a partir do contexto disponível.

40. A SÍNTESE CIO é uma síntese interpretativa.

    Ela não é:
    - recomendação;
    - ordem;
    - novo sinal;
    - novo score;
    - autorização de exposição;
    - substituição dos motores quantitativos.

OBJETIVO:

Transformar os resultados dos sete sistemas em uma análise
CIO única, coerente e rastreável, explicando COMO os sistemas
se relacionam entre si.

A análise deve servir exclusivamente como apoio interpretativo
à decisão humana.

O Investment CIO AI deve ampliar a compreensão do conjunto
sem criar uma nova decisão de investimento.
""".strip()


# ============================================================
# PROMPT DE ANÁLISE
# ============================================================

def build_ai_prompt(
    context: Dict[str, Any],
) -> str:

    context_json = json.dumps(
        context,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    return f"""
Analise o contexto validado abaixo.

=========================
CONTEXTO DO INVESTMENT CIO
=========================

{context_json}

=========================
TAREFA
=========================

Produza uma análise integrada dos sete sistemas.

Sua tarefa é interpretar relações existentes no contexto.
Não crie uma recomendação própria de investimento.

Estruture a resposta exatamente nas seguintes seções:

1. CONTEXTO GERAL

Explique o cenário conjunto identificado pelos sistemas.

Diferencie claramente fatos produzidos pelos sistemas de
interpretações relacionais produzidas pela análise.

2. RELAÇÃO ENTRE OS SISTEMAS

Explique como regime, risco global, seleção de ativos,
timing e scanners de oportunidades se relacionam.

Utilize somente relações sustentadas pelo contexto.

Não atribua causas específicas aos sinais sem evidência
explícita.

3. CONVERGÊNCIAS

Identifique apenas convergências sustentadas pelos dados.

Não generalize a partir de exemplos isolados sem evidência
suficiente.

4. DIVERGÊNCIAS

Identifique divergências reais.

Explique se a divergência pode decorrer das funções diferentes
dos sistemas.

Não invente a causa da divergência.

5. RISCO X OPORTUNIDADE

Mostre se existem oportunidades específicas simultaneamente
a um ambiente de risco ou restrição global.

Se houver Hard Block, Kill Switch ou restrições, preserve-os
exatamente.

Não transforme a relação risco x oportunidade em recomendação
de exposição.

6. MACRO X MICRO

Relacione os motores macro e de risco com os motores de
seleção e oportunidades.

O macro não deve ser utilizado para alterar os sinais micro.

Os sinais micro não devem ser utilizados como votos sobre
o regime macro.

7. SELEÇÃO X TIMING

Compare seleção e timing somente quando houver elementos
explicitamente comparáveis no contexto.

Não altere os sinais originais.

Não atribua um motivo ao timing se esse motivo não estiver
explicitamente informado.

Se a causa não estiver disponível, declare:

"O contexto informa o sinal de timing, mas não fornece
evidência suficiente para atribuir uma causa específica."

8. RESTRIÇÕES E GOVERNANÇA

Explique as restrições presentes.

Kill Switch e Hard Block devem ser apresentados exatamente
como constam no contexto.

Não crie consequências operacionais adicionais.

Não transforme as restrições em uma recomendação própria.

9. PONTOS PRIORITÁRIOS PARA OBSERVAÇÃO

Identifique fatos, estados, divergências, restrições e sinais
já presentes no contexto que merecem acompanhamento.

Não crie novos indicadores ou scores.

Não formule ordens, recomendações ou instruções de
compra/venda/exposição.

10. SÍNTESE CIO

Produza uma síntese integrada e exclusivamente interpretativa
do cenário.

A síntese deve explicar:
- o que os sistemas mostram em conjunto;
- onde convergem;
- onde divergem;
- como risco e oportunidade coexistem;
- quais restrições permanecem ativas.

A síntese NÃO pode:
- recomendar compra;
- recomendar venda;
- recomendar aumento de exposição;
- recomendar redução de exposição;
- recomendar preservação de capital;
- recomendar entrada ou saída;
- criar regra operacional;
- criar novo sinal;
- criar novo score.

Não use a expressão "a recomendação é" para introduzir uma
conclusão própria.

Quando existir uma orientação originada por um sistema,
ela pode ser relatada somente com atribuição explícita
à respectiva fonte.

11. RASTREABILIDADE

Informe quais sistemas ou camadas sustentam as principais
conclusões.

Não atribua uma conclusão a um sistema que não forneceu
evidência para ela.

Finalize obrigatoriamente declarando:

- nenhum sinal quantitativo foi alterado;
- nenhum indicador foi recalculado;
- nenhum novo score quantitativo foi criado;
- nenhuma recomendação própria de investimento foi criada
  pelo Investment CIO AI;
- nenhuma ordem foi executada;
- a decisão final permanece humana.
""".strip()


# ============================================================
# CLIENTE NVIDIA NIM
# ============================================================

def _build_nvidia_client(
    api_key: Optional[str] = None,
):

    if OpenAI is None:
        raise CIOAIConfigurationError(
            "Pacote 'openai' não instalado. "
            "Adicione 'openai' ao requirements.txt."
        )

    key = (
        api_key
        or os.getenv("NVIDIA_API_KEY")
        or os.getenv("NVIDIA_API_KEY_CIO")
    )

    if not key:
        raise CIOAIConfigurationError(
            "Chave NVIDIA não configurada. "
            "Configure NVIDIA_API_KEY nos GitHub Secrets."
        )

    return OpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=key,
    )


# ============================================================
# EXTRAÇÃO DA RESPOSTA
# ============================================================

def _extract_response_text(
    completion: Any,
) -> str:

    try:
        content = (
            completion
            .choices[0]
            .message
            .content
        )
    except Exception as exc:
        raise CIOAIResponseError(
            "Formato inesperado de resposta da NVIDIA NIM."
        ) from exc

    if not isinstance(content, str):
        raise CIOAIResponseError(
            "A NVIDIA NIM não retornou conteúdo textual válido."
        )

    content = content.strip()

    if not content:
        raise CIOAIResponseError(
            "A NVIDIA NIM retornou resposta vazia."
        )

    return content


# ============================================================
# EXECUÇÃO DA INTELIGÊNCIA
# ============================================================

def run_cio_ai(
    orchestrator_output: Dict[str, Any],
    *,
    client: Any = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:

    validate_orchestrator_context(
        orchestrator_output
    )

    original_input = deepcopy(
        orchestrator_output
    )

    context = build_ai_context(
        orchestrator_output
    )

    prompt = build_ai_prompt(
        context
    )

    selected_model = (
        model
        or os.getenv("CIO_AI_MODEL")
        or DEFAULT_MODEL
    )

    if client is None:
        client = _build_nvidia_client(
            api_key=api_key
        )

    try:
        completion = client.chat.completions.create(
            model=selected_model,

            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],

            temperature=1.0,
            top_p=0.95,

            max_tokens=8192,

            stream=False,

            extra_body={
                "chat_template_kwargs": {
                    "enable_thinking": True,
                    "low_effort": True,
                }
            },
        )

    except Exception as exc:
        raise CIOAIResponseError(
            "Falha na execução da NVIDIA NIM: "
            f"{exc}"
        ) from exc

    analysis = _extract_response_text(
        completion
    )

    # ========================================================
    # IMUTABILIDADE
    # ========================================================

    if orchestrator_output != original_input:
        raise CIOAIError(
            "O contexto original do Orchestrator foi alterado."
        )

    risk = _safe_dict(
        orchestrator_output.get("risk")
    )

    global_constraint = _safe_dict(
        risk.get("global_constraint")
    )

    restrictions = risk.get(
        "restrictions",
        [],
    )

    if not isinstance(restrictions, list):
        restrictions = []

    # ========================================================
    # RESULTADO
    # ========================================================

    return {
        "cio_ai_version": CIO_AI_VERSION,

        "generated_at": _utc_now(),

        "status": "OK",

        "provider": "NVIDIA_NIM",

        "model": selected_model,

        "source": (
            "ORCHESTRATOR_VALIDATED_CONTEXT"
        ),

        "analysis": analysis,

        "context_summary": {
            "pipeline_status": (
                orchestrator_output.get("status")
            ),

            "systems_expected": len(
                OFFICIAL_SYSTEMS
            ),

            "global_constraint_state": (
                global_constraint.get("state")
            ),

            "hard_block": (
                global_constraint.get(
                    "hard_block"
                )
            ),

            "global_kill_switch": (
                global_constraint.get(
                    "global_kill_switch"
                )
            ),

            "restriction_count": len(
                restrictions
            ),
        },

        "traceability": {
            "official_systems": list(
                OFFICIAL_SYSTEMS.keys()
            ),

            "source_context": "ORCHESTRATOR",

            "source_signals_preserved": True,

            "source_order_preserved": True,

            "kill_switch_preserved": True,

            "hard_block_preserved": True,
        },

        "policy": {
            "orchestrator_context_only": True,

            "cross_system_analysis": True,

            "source_signals_preserved": True,

            "source_order_preserved": True,

            "indicators_recalculated": False,

            "new_quantitative_scores_created": False,

            "source_decisions_overridden": False,

            "selection_systems_used_as_macro_votes": False,

            "opportunity_systems_used_as_macro_votes": False,

            "ai_created_investment_recommendation": False,

            "ai_created_action_rule": False,

            "causal_claims_require_explicit_evidence": True,

            "broker_execution_allowed": False,

            "human_decision_required": True,
        },
    }


# ============================================================
# INTERFACE ALTERNATIVA
# ============================================================

def analyze_cio_context(
    orchestrator_output: Dict[str, Any],
    *,
    client: Any = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:

    return run_cio_ai(
        orchestrator_output,
        client=client,
        model=model,
        api_key=api_key,
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "CIO_AI_VERSION",
    "NVIDIA_BASE_URL",
    "DEFAULT_MODEL",
    "OFFICIAL_SYSTEMS",
    "CIOAIError",
    "CIOAIConfigurationError",
    "CIOAIInputError",
    "CIOAIResponseError",
    "validate_orchestrator_context",
    "build_ai_context",
    "build_ai_prompt",
    "run_cio_ai",
    "analyze_cio_context",
]
