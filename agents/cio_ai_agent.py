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
# - inventa causas para sinais produzidos pelos motores;
# - generaliza causas entre ativos;
# - declara convergência sem evidência comparável;
# - infere causa a partir do nome de um status;
# - cria quantificadores sem evidência explícita;
# - transforma metodologia do motor em causa de sinal;
# - transforma metodologia/arquitetura em timing;
# - transforma restrição em consequência operacional não fornecida;
# - cria linguagem prescritiva sem atribuição explícita à fonte.
#
# ============================================================

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
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

CIO_AI_VERSION = "1.5"

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


class CIOAISemanticValidationError(CIOAIResponseError):
    """Resposta da IA rejeitada pela barreira de fidelidade semântica."""


class CIOAIStructuralValidationError(CIOAIResponseError):
    """Resposta da IA rejeitada pela barreira estrutural do relatório CIO."""


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

            "ai_must_not_create_investment_recommendations": True,
            "ai_must_not_create_action_rules": True,
            "ai_must_not_invent_signal_causes": True,
            "ai_must_not_invent_cross_system_relationships": True,
            "explicit_evidence_required_for_causal_claims": True,
            "source_actions_must_be_attributed": True,

            # V1.2 — proteção contra extrapolação semântica.
            "convergence_requires_comparable_evidence": True,
            "same_ticker_convergence_requires_same_ticker": True,
            "do_not_generalize_causes_across_assets": True,
            "do_not_generalize_conditions_across_signals": True,
            "summary_must_preserve_evidence_scope": True,

            # V1.3 — proteção contra inferência semântica residual.
            "status_label_does_not_imply_cause": True,
            "quantifiers_require_explicit_evidence": True,
            "methodology_does_not_imply_signal_cause": True,
            "methodology_does_not_imply_future_signal_change": True,
            "do_not_infer_condition_from_status_name": True,
            "do_not_create_group_statistics": True,

            # V1.4 — proteção contra prescrição e confusão metodologia/timing.
            "methodology_is_not_timing": True,
            "restrictions_do_not_imply_operational_consequences": True,
            "descriptive_analysis_must_not_become_prescriptive": True,
            "prescriptive_language_requires_explicit_source_attribution": True,

            # V1.5 — enforcement pós-Nemotron.
            "semantic_fidelity_barrier_enabled": True,
            "semantic_violations_must_fail_safe": True,
            "semantic_validation_must_not_change_source_data": True,
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
    contexto recebido PARA AQUELE MESMO SINAL OU ATIVO.

29. O papel conhecido de um sistema pode ser utilizado para
    explicar sua função estrutural.

    Porém, a função estrutural do sistema NÃO prova a causa
    específica de um sinal individual.

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

41. CONVERGÊNCIA EXIGE EVIDÊNCIA COMPARÁVEL.

    A simples existência de sinais positivos em sistemas
    diferentes NÃO constitui convergência entre esses sistemas.

    Exemplo:
    se o Sistema A apresenta ENTRADA para o ticker X e o
    Sistema B apresenta ENTRADA para o ticker Y, isso NÃO
    constitui convergência por ativo entre A e B.

    Para declarar convergência por ticker, o MESMO ticker
    precisa aparecer nos sistemas comparados e os respectivos
    sinais precisam estar explicitamente presentes no contexto.

    Se os sistemas apenas apresentam sinais positivos para
    ativos diferentes, descreva isso como coexistência de
    sinais positivos, e NÃO como convergência por ticker.

42. NÃO TRANSFIRA CAUSAS ENTRE ATIVOS.

    Uma causa, condição, justificativa ou gatilho explicitamente
    informado para um ticker não pode ser utilizado para
    explicar o sinal de outro ticker.

    Exemplo:
    se o ticker X possui "aguardar confirmação de volume",
    isso não autoriza afirmar que o ticker Y está em AGUARDAR
    por falta de volume.

43. NÃO TRANSFIRA CAUSAS ENTRE GRUPOS DE SINAIS.

    A existência de alguns ativos aguardando:
    - volume;
    - gatilho;
    - confirmação institucional;
    - pullback;
    - rompimento;

    NÃO autoriza afirmar que todos os ativos em AGUARDAR,
    PRÉ-ENTRADA, NÃO COMPRAR ou qualquer outra categoria
    possuem a mesma causa.

44. NÃO CONDICIONE SINAIS JÁ POSITIVOS SEM EVIDÊNCIA.

    Se um ativo possui ENTRADA ou ENTRADA FORTE, não diga que
    essa entrada ainda depende de gatilho, confirmação, volume,
    pullback ou outra condição, salvo quando essa condição
    estiver explicitamente vinculada ao mesmo ativo no contexto.

45. NÃO CONFUNDA COEXISTÊNCIA COM CONVERGÊNCIA.

    Sistemas diferentes podem simultaneamente apresentar
    oportunidades ou sinais positivos em ativos distintos.

    Isso é coexistência de evidências positivas.

    Somente chame de convergência entre sistemas quando houver
    uma dimensão explicitamente comparável e evidência
    suficiente no contexto.

46. TODA CAUSALIDADE DEVE PRESERVAR SEU ESCOPO.

    Quando o contexto fornecer uma causa para um ativo ou
    sinal específico, mantenha a causalidade limitada
    exatamente àquele ativo ou sinal.

    Não amplie:
    "alguns ativos aguardam confirmação de volume"

    para:
    "as oportunidades aguardam confirmação de volume".

47. A SÍNTESE CIO NÃO PODE AMPLIAR O ESCOPO DA EVIDÊNCIA.

    A seção de síntese está sujeita às mesmas regras de
    evidência das demais seções.

    Uma causa válida em uma seção detalhada não pode ser
    generalizada na síntese.

    Na síntese:
    - preserve a granularidade dos fatos;
    - preserve a origem dos fatos;
    - preserve o universo ao qual cada fato se aplica;
    - não transforme exemplos em regra geral;
    - não transforme subconjuntos em totalidade.

48. Quando houver sinais com causas explícitas e sinais sem
    causas explícitas no mesmo sistema ou conjunto, separe-os.

    Exemplo de formulação permitida:

    "Alguns sinais possuem condições explicitamente informadas
    no contexto. Para os demais sinais, o contexto não fornece
    evidência suficiente para atribuir uma causa específica."

49. Antes de declarar CONVERGÊNCIA, verifique mentalmente:

    A) Qual é a dimensão comparada?
    B) Os dois fatos estão explicitamente no contexto?
    C) Se a comparação for por ticker, é o mesmo ticker?
    D) Os sinais são realmente comparáveis?

    Se qualquer resposta não puder ser confirmada pelo
    contexto, não declare convergência.

50. Antes de apresentar uma CAUSA, verifique mentalmente:

    A) A causa aparece explicitamente no contexto?
    B) Está vinculada ao mesmo ticker ou sinal?
    C) Não foi transportada de outro ativo?
    D) Não foi generalizada de um subconjunto?

    Se qualquer resposta não puder ser confirmada,
    não apresente a causa como explicação.

51. O NOME OU RÓTULO DE UM STATUS NÃO PROVA SUA CAUSA.

    Trate o status exatamente como informação de origem.

    Exemplos:

    "PRÉ-ENTRADA — AGUARDAR GATILHO"

    permite afirmar somente que o sistema informou
    PRÉ-ENTRADA e/ou AGUARDAR GATILHO, conforme estiver
    estruturado no contexto.

    Esse rótulo NÃO autoriza inferir automaticamente:
    - falta de volume;
    - ausência de fluxo institucional;
    - necessidade de confirmação institucional;
    - pullback;
    - rompimento;
    - momentum insuficiente;
    - valuation inadequado;
    - fundamentos insuficientes;
    - ou qualquer outra causa.

    Uma causa adicional somente pode ser mencionada quando
    estiver explicitamente associada ao mesmo ativo ou sinal
    no contexto.

52. NÃO DERIVE CAUSA A PARTIR DA SEMÂNTICA DO STATUS.

    Palavras existentes dentro do próprio status podem ser
    reproduzidas como parte literal do status.

    Porém, não converta essas palavras em uma explicação causal
    mais ampla.

    Exemplo:

    STATUS:
    "AGUARDAR GATILHO"

    Permitido:
    "O sistema classifica o ativo como AGUARDAR GATILHO."

    Não permitido sem evidência adicional:
    "O ativo aguarda aumento de volume para confirmar o gatilho."

53. QUANTIFICADORES EXIGEM EVIDÊNCIA EXPLÍCITA.

    Não use afirmações quantitativas ou distributivas como:
    - todos;
    - todas;
    - a maioria;
    - maior parte;
    - predominantemente;
    - principalmente;
    - geralmente;
    - em geral;
    - quase todos;
    - quase todas;
    - grande parte;

    para descrever causas, condições, justificativas,
    características ou comportamentos de um conjunto,
    salvo quando essa proporção estiver explicitamente
    demonstrada pelo contexto.

54. NÃO CRIE ESTATÍSTICA OU DISTRIBUIÇÃO IMPLÍCITA.

    Não transforme uma lista de ativos em afirmações como:
    - "a maioria aguarda confirmação";
    - "predominam sinais condicionais";
    - "geralmente falta volume";
    - "grande parte depende de gatilho";

    salvo quando o contexto fornecer contagem, proporção,
    classificação agregada ou evidência equivalente que
    sustente exatamente essa afirmação.

    Se não houver essa evidência, descreva individualmente
    os fatos relevantes ou utilize formulação neutra como:

    "Há ativos com condições explicitamente registradas no
    contexto."

55. METODOLOGIA NÃO É CAUSA AUTOMÁTICA DO SINAL.

    Termos que descrevem arquitetura ou metodologia de um
    sistema, incluindo:
    - Financial Strength;
    - Growth;
    - Valuation;
    - Momentum;
    - fundamentos;
    - desconto;
    - qualidade;
    - ranking;
    - score interno;
    - filtro;
    - peneira;

    podem ser usados para explicar COMO o sistema é estruturado
    quando essa informação estiver no contexto.

    Eles NÃO podem ser apresentados automaticamente como a
    causa específica de:
    - ENTRADA;
    - ENTRADA FORTE;
    - AGUARDAR;
    - NÃO COMPRAR;
    - EVITAR;
    - PRÉ-ENTRADA;
    - mudança futura de sinal;
    - ou qualquer decisão individual de um ticker.

56. NÃO PREVEJA O QUE FARÁ UM SINAL MUDAR.

    Não afirme que um ativo mudará de:
    - AGUARDAR para ENTRADA;
    - PRÉ-ENTRADA para ENTRADA;
    - NÃO COMPRAR para COMPRAR;
    - ou qualquer outro estado;

    quando ocorrer:
    - melhora de fundamentos;
    - melhora de valuation;
    - aumento de volume;
    - confirmação institucional;
    - pullback;
    - rompimento;
    - mudança de momentum;
    - ou outra condição;

    salvo quando essa relação condicional estiver explicitamente
    registrada no contexto para o mesmo ativo ou sinal.

57. NÃO USE A ARQUITETURA DO MOTOR PARA COMPLETAR LACUNAS.

    Saber que um sistema utiliza Financial Strength, Growth,
    Valuation, Momentum ou qualquer outro critério não autoriza
    concluir que esse critério explica o sinal atual de um
    ticker específico.

    Quando o contexto informar apenas:
    - metodologia do sistema; e
    - sinal do ativo;

    sem fornecer a ligação causal entre ambos, mantenha as
    duas informações separadas.

58. PRESERVE A DIFERENÇA ENTRE RÓTULO E EXPLICAÇÃO.

    RÓTULO:
    é o texto ou categoria produzido pelo sistema.

    EXPLICAÇÃO:
    é a causa explicitamente fornecida pelo contexto.

    Nunca transforme automaticamente um rótulo em explicação.

59. PRESERVE A DIFERENÇA ENTRE LISTA E ESTATÍSTICA.

    Uma lista de ativos não é, por si só, uma estatística.

    Não produza:
    - maioria;
    - minoria;
    - predominância;
    - proporção;
    - frequência;
    - percentual;

    a partir da lista, salvo quando o contexto já fornecer
    explicitamente essa agregação ou quando a tarefa exigir
    apenas repetir uma contagem explicitamente fornecida.

60. REGRA FINAL DE SEGURANÇA SEMÂNTICA.

    Antes de escrever qualquer frase explicativa, causal,
    quantitativa ou distributiva, verifique:

    A) A informação está explicitamente no contexto?
    B) Está vinculada ao mesmo ativo, sinal ou conjunto?
    C) O status está sendo preservado como status?
    D) A metodologia está sendo preservada como metodologia?
    E) Existe evidência para qualquer palavra como "maioria",
       "todos", "principalmente" ou equivalente?
    F) A frase preserva exatamente o escopo da evidência?

    Se qualquer resposta necessária não puder ser confirmada,
    use uma formulação estritamente descritiva e não causal.

61. METODOLOGIA OU ARQUITETURA NÃO É TIMING.

    Critérios, pesos, fórmulas, arquitetura, metodologia, ranking,
    filtros ou composição do motor não podem ser chamados de:
    - método de timing;
    - condição de timing;
    - gatilho de timing;
    - causa do timing;
    - explicação do timing;

    salvo quando o contexto declarar explicitamente essa função.

    Exemplo:
    "10% Valuation + 80% Desconto + 10% Fundamentos"
    deve permanecer descrito como metodologia ou arquitetura quando
    essa for sua natureza no contexto.

    Não o transforme em "método de timing" apenas porque aparece
    próximo de um sinal como AGUARDAR.

62. RESTRIÇÃO NÃO IMPLICA CONSEQUÊNCIA OPERACIONAL NOVA.

    Kill Switch, Hard Block, risco crítico, liquidez frágil,
    governança ou qualquer outra restrição devem ser descritos
    exatamente conforme o contexto.

    Não conclua, por inferência própria, que uma restrição:
    - limita exposição;
    - reduz exposição;
    - impede entrada;
    - exige saída;
    - exige espera;
    - exige preservação de capital;
    - exige rebalanceamento;
    - ou produz qualquer outra consequência operacional;

    salvo quando essa consequência estiver explicitamente registrada
    no contexto e atribuída à respectiva fonte.

63. DESCRIÇÃO NÃO PODE VIRAR PRESCRIÇÃO.

    O Investment CIO AI deve descrever estados, sinais, tensões,
    restrições e relações sem criar obrigação para a decisão humana.

    Não use formulações próprias como:
    - "deve ser respeitado";
    - "devem ser respeitadas";
    - "deve ser considerado";
    - "deve ser considerada";
    - "deve limitar";
    - "deve reduzir";
    - "deve aumentar";
    - "exige cautela";
    - "exige acompanhamento";

    quando essas formulações criarem orientação, obrigação ou
    consequência não explicitamente fornecida pela fonte.

    Quando houver orientação prescritiva explicitamente presente no
    contexto, ela somente pode ser reproduzida com atribuição clara
    ao sistema ou camada de origem.

OBJETIVO:

Transformar os resultados dos sete sistemas em uma análise
CIO única, coerente e rastreável, explicando COMO os sistemas
se relacionam entre si.

A análise deve servir exclusivamente como apoio interpretativo
à decisão humana.

O Investment CIO AI deve ampliar a compreensão do conjunto
sem criar uma nova decisão de investimento, sem ampliar
o escopo das evidências recebidas e sem preencher lacunas
causais ou quantitativas por inferência.
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

REGRA DE ESCOPO:

Cada afirmação causal deve permanecer vinculada exatamente
ao ativo, sinal, sistema ou subconjunto para o qual existe
evidência explícita.

Não transporte causas entre ativos.
Não transporte causas entre sinais.
Não transforme exemplos em regra geral.
Não transforme coexistência em convergência.
Não transforme o nome de um status em causa.
Não transforme metodologia do sistema em causa do sinal.
Não transforme metodologia ou arquitetura em timing.
Não transforme restrição em consequência operacional não fornecida.
Não transforme descrição em prescrição.
Não use linguagem prescritiva própria sem atribuição explícita à fonte.
Não use quantificadores sem evidência explícita.

Estruture a resposta exatamente nas seguintes seções:

1. CONTEXTO GERAL

Explique o cenário conjunto identificado pelos sistemas.

Diferencie claramente fatos produzidos pelos sistemas de
interpretações relacionais produzidas pela análise.

Não afirme que todas as oportunidades ou todos os sinais
dependem de uma condição quando essa condição estiver
documentada apenas para parte deles.

Não utilize "maioria", "principalmente", "geralmente",
"predominantemente" ou equivalentes para causas ou condições
sem evidência explícita dessa distribuição no contexto.

2. RELAÇÃO ENTRE OS SISTEMAS

Explique como regime, risco global, seleção de ativos,
timing e scanners de oportunidades se relacionam.

Utilize somente relações sustentadas pelo contexto.

Não atribua causas específicas aos sinais sem evidência
explícita para o mesmo ativo ou sinal.

A metodologia de um sistema pode ser descrita como
metodologia, mas não como causa automática de um sinal.

3. CONVERGÊNCIAS

Identifique apenas convergências sustentadas por elementos
explicitamente comparáveis.

IMPORTANTE:

A existência de ENTRADA ou ENTRADA FORTE em ativos diferentes
de sistemas diferentes NÃO constitui, por si só, convergência
entre os sistemas.

Para convergência por ticker:
- o mesmo ticker deve aparecer nos sistemas comparados;
- os sinais comparados devem estar explicitamente presentes.

Se houver apenas sinais positivos em ativos diferentes,
descreva como coexistência de sinais positivos, não como
convergência por ticker.

Não generalize a partir de exemplos isolados.

4. DIVERGÊNCIAS

Identifique divergências reais e sustentadas pelo contexto.

Explique se a divergência pode decorrer das funções diferentes
dos sistemas somente quando essa relação funcional estiver
sustentada pelo contexto.

Não invente a causa da divergência.

5. RISCO X OPORTUNIDADE

Mostre se existem oportunidades específicas simultaneamente
a um ambiente de risco ou restrição global.

Se houver Hard Block, Kill Switch ou restrições, preserve-os
exatamente.

Não transforme a relação risco x oportunidade em recomendação
de exposição.

Não afirme que todas as oportunidades possuem condições
pendentes apenas porque algumas possuem.

Não transforme uma lista de oportunidades em uma estatística
ou distribuição que o contexto não forneceu.

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
explicitamente informado para o mesmo ativo ou sinal.

Uma condição associada a um ticker não pode ser transferida
para outro ticker.

Metodologia, arquitetura, pesos, critérios, filtros ou composição
do motor não constituem timing e não podem ser chamados de
"método de timing", "condição de timing" ou equivalente, salvo
quando o próprio contexto declarar explicitamente essa função.

IMPORTANTE:

O nome do status não deve ser usado para inferir uma causa.

Se o status for "PRÉ-ENTRADA — AGUARDAR GATILHO", preserve
esse status literalmente.

Não conclua que existe:
- falta de volume;
- necessidade de confirmação institucional;
- pullback;
- rompimento;
- mudança de fundamentos;
- mudança de valuation;

salvo quando a condição estiver explicitamente vinculada
ao mesmo ticker no contexto.

Se a causa não estiver disponível, declare:

"O contexto informa o sinal de timing, mas não fornece
evidência suficiente para atribuir uma causa específica."

8. RESTRIÇÕES E GOVERNANÇA

Explique as restrições presentes.

Kill Switch e Hard Block devem ser apresentados exatamente
como constam no contexto.

Não crie consequências operacionais adicionais.

Não diga que uma restrição "limita exposição", "reduz exposição",
"impede entrada", "exige espera" ou produz outra consequência
operacional, salvo quando essa consequência estiver explicitamente
registrada no contexto e atribuída à fonte.

Não transforme as restrições em uma recomendação própria.

Não use "deve ser respeitada", "devem ser respeitadas" ou
formulações equivalentes como orientação própria do CIO AI.

9. PONTOS PRIORITÁRIOS PARA OBSERVAÇÃO

Identifique fatos, estados, divergências, restrições e sinais
já presentes no contexto como pontos descritivos de observação.

Não diga que um fato "exige acompanhamento", "exige cautela" ou
impõe outra obrigação, salvo quando essa orientação estiver
explicitamente presente no contexto e atribuída à fonte.

Ao mencionar condições como volume, gatilho, pullback,
rompimento ou confirmação institucional, limite a afirmação
somente aos ativos para os quais essa condição estiver
explicitamente presente.

Não diga que "todos", "a maioria", "grande parte",
"principalmente", "geralmente" ou "predominantemente"
dependem de determinada condição sem evidência explícita
dessa distribuição.

Não afirme que Financial Strength, Growth, Valuation,
Momentum ou outra metodologia determinará a mudança futura
de um sinal, salvo quando essa relação estiver explicitamente
presente para o mesmo ativo.

Não crie novos indicadores ou scores.

Não formule ordens, recomendações ou instruções de
compra/venda/exposição.

10. SÍNTESE CIO

Produza uma síntese integrada e exclusivamente interpretativa
do cenário.

A síntese deve explicar:
- o que os sistemas mostram em conjunto;
- onde existem convergências comprovadas;
- onde existem divergências comprovadas;
- onde há apenas coexistência de sinais;
- como risco e oportunidade coexistem;
- quais restrições permanecem ativas.

REGRA CRÍTICA DA SÍNTESE:

A síntese NÃO pode ampliar o escopo das evidências.

Se apenas alguns ativos possuem gatilho, volume, pullback,
rompimento ou confirmação explicitamente pendentes, diga
apenas que existem ativos com essas condições explicitamente
registradas.

Não converta isso em:
- "a maioria";
- "todos";
- "principalmente";
- "predominantemente";
- "geralmente";
- "em geral";
- "grande parte";

sem evidência quantitativa ou distributiva explícita.

Não diga que ENTRADA ou ENTRADA FORTE depende de confirmação
adicional salvo quando isso estiver explicitamente informado
para o mesmo ativo.

Não use a causa de um ativo para explicar outro ativo.

Não use a causa de um subconjunto para explicar todo o
conjunto.

Não transforme o nome de um status em explicação causal.

Não transforme a metodologia de um sistema em explicação
causal de um ticker específico.

Não transforme metodologia ou arquitetura em timing.

Não transforme restrições em consequências operacionais não
explicitamente fornecidas pelo contexto.

Não transforme a síntese descritiva em prescrição. Evite "deve",
"devem", "exige" ou equivalentes quando criarem orientação própria.

Não preveja quais fatores farão um sinal mudar de categoria,
salvo quando essa relação estiver explicitamente registrada
no contexto.

A síntese NÃO pode:
- recomendar compra;
- recomendar venda;
- recomendar aumento de exposição;
- recomendar redução de exposição;
- recomendar preservação de capital;
- recomendar entrada ou saída;
- criar regra operacional;
- criar novo sinal;
- criar novo score;
- criar estatística não fornecida pelo contexto.

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

Quando uma causa estiver associada apenas a determinados
ativos, preserve essa granularidade também na rastreabilidade.

Quando uma afirmação quantitativa ou distributiva estiver
presente, identifique a evidência do contexto que sustenta
essa afirmação.

Finalize obrigatoriamente declarando:

- nenhum sinal quantitativo foi alterado;
- nenhum indicador foi recalculado;
- nenhum novo score quantitativo foi criado;
- nenhuma recomendação própria de investimento foi criada
  pelo Investment CIO AI;
- nenhuma causalidade foi generalizada além da evidência
  explicitamente fornecida;
- nenhuma convergência foi declarada sem evidência comparável;
- nenhum status foi transformado automaticamente em causa;
- nenhuma metodologia foi transformada automaticamente em
  causa de sinal individual;
- nenhum quantificador causal ou distributivo foi criado sem
  evidência explícita;
- nenhuma metodologia ou arquitetura foi transformada em timing
  sem evidência explícita;
- nenhuma restrição foi transformada em consequência operacional
  não fornecida pelo contexto;
- nenhuma linguagem prescritiva própria foi criada sem atribuição
  explícita à fonte;
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
# BARREIRA ESTRUTURAL DO RELATÓRIO CIO — V1.5
# ============================================================

REQUIRED_REPORT_SECTIONS = (
    "CONTEXTO GERAL",
    "RELAÇÃO ENTRE OS SISTEMAS",
    "CONVERGÊNCIAS",
    "DIVERGÊNCIAS",
    "RISCO X OPORTUNIDADE",
    "MACRO X MICRO",
    "SELEÇÃO X TIMING",
    "RESTRIÇÕES E GOVERNANÇA",
    "PONTOS PRIORITÁRIOS PARA OBSERVAÇÃO",
    "SÍNTESE CIO",
    "RASTREABILIDADE",
)


def _normalize_report_heading(value: Any) -> str:
    """Normaliza títulos somente para validação estrutural."""
    normalized = _normalize_semantic_text(value)
    normalized = re.sub(r"^[#*\s]+", "", normalized)
    normalized = re.sub(r"^\d+\s*[\.\)\-:]\s*", "", normalized)
    normalized = re.sub(r"[*#:\s]+$", "", normalized)
    return normalized.strip()


def validate_ai_analysis_structure(
    analysis: str,
) -> Dict[str, Any]:
    """
    Barreira estrutural pós-Nemotron.

    Rejeita:
    - resposta vazia;
    - reprodução direta de JSON/contexto em vez de relatório;
    - relatório sem as 11 seções obrigatórias;
    - seções fora da ordem exigida.

    A exigência das 11 seções também funciona como fail-safe contra
    respostas truncadas antes da conclusão do relatório.
    """
    if not isinstance(analysis, str) or not analysis.strip():
        raise CIOAIStructuralValidationError(
            "STRUCTURAL_EMPTY_RESPONSE: relatório CIO vazio ou inválido."
        )

    stripped = analysis.strip()
    normalized = _normalize_semantic_text(stripped)

    # A resposta final deve ser relatório textual, não dump do contexto.
    json_like_start = bool(
        re.match(r"^\s*(?:```(?:json)?\s*)?[\{\[]", stripped, re.IGNORECASE)
    )
    context_dump_markers = (
        '"context_version"',
        '"pipeline_status"',
        '"official_systems"',
        '"mandatory_policy"',
        '"synthesis"',
        '"executive_report"',
    )
    dump_marker_count = sum(
        marker in normalized
        for marker in context_dump_markers
    )

    if json_like_start or dump_marker_count >= 4:
        raise CIOAIStructuralValidationError(
            "STRUCTURAL_CONTEXT_DUMP: a resposta reproduz o contexto "
            "estruturado em vez de produzir o relatório CIO."
        )

    # Localiza os 11 títulos como linhas independentes, tolerando
    # numeração e Markdown, mas não simples menções no corpo do texto.
    lines = stripped.splitlines()
    found_positions = []

    for required in REQUIRED_REPORT_SECTIONS:
        required_normalized = _normalize_semantic_text(required)
        position = None

        for index, line in enumerate(lines):
            if _normalize_report_heading(line) == required_normalized:
                position = index
                break

        if position is None:
            raise CIOAIStructuralValidationError(
                "STRUCTURAL_MISSING_SECTION: seção obrigatória ausente: "
                f"{required}"
            )

        found_positions.append(position)

    if found_positions != sorted(found_positions):
        raise CIOAIStructuralValidationError(
            "STRUCTURAL_SECTION_ORDER: as 11 seções obrigatórias "
            "não estão na ordem definida pelo Investment CIO AI."
        )

    # Cada seção deve possuir conteúdo antes do próximo título.
    for idx, start in enumerate(found_positions):
        end = (
            found_positions[idx + 1]
            if idx + 1 < len(found_positions)
            else len(lines)
        )
        body = "\n".join(lines[start + 1:end]).strip()
        if not body:
            raise CIOAIStructuralValidationError(
                "STRUCTURAL_EMPTY_SECTION: seção sem conteúdo: "
                f"{REQUIRED_REPORT_SECTIONS[idx]}"
            )

    return {
        "status": "PASS",
        "barrier_version": CIO_AI_VERSION,
        "required_sections": len(REQUIRED_REPORT_SECTIONS),
        "sections_found": len(found_positions),
        "context_dump_detected": False,
        "fail_safe": True,
    }


# ============================================================
# BARREIRA DE FIDELIDADE SEMÂNTICA — V1.5
# ============================================================

def _normalize_semantic_text(value: Any) -> str:
    """
    Normaliza texto apenas para comparação semântica defensiva.
    Não altera o relatório nem o contexto original.
    """
    if value is None:
        return ""

    text = str(value).lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _context_semantic_corpus(
    context: Dict[str, Any],
) -> str:
    """
    Cria um corpus somente para verificar se uma formulação operacional
    ou prescritiva já existe explicitamente no contexto de origem.
    """
    return _normalize_semantic_text(
        json.dumps(
            context,
            ensure_ascii=False,
            default=str,
        )
    )


def _sentence_has_explicit_distribution_evidence(
    sentence: str,
) -> bool:
    """
    Aceita quantificação distributiva somente quando a própria frase
    apresenta evidência numérica explícita, como:
    - percentual;
    - razão X de Y;
    - contagem X/Y.
    """
    normalized = _normalize_semantic_text(sentence)

    evidence_patterns = (
        r"\b\d+(?:[.,]\d+)?\s*%",
        r"\b\d+\s+de\s+\d+\b",
        r"\b\d+\s*/\s*\d+\b",
    )

    return any(
        re.search(pattern, normalized)
        for pattern in evidence_patterns
    )


def validate_ai_analysis_semantics(
    analysis: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Barreira fail-safe pós-Nemotron.

    Objetivo:
    - NÃO decidir investimentos;
    - NÃO reinterpretar os sete robôs;
    - NÃO corrigir silenciosamente o texto da IA;
    - somente rejeitar uma análise que ultrapasse limites semânticos
      críticos definidos pela governança do CIO.

    Em caso de violação, a resposta não é publicada como relatório válido.
    """
    if not isinstance(analysis, str) or not analysis.strip():
        raise CIOAISemanticValidationError(
            "A análise da IA está vazia ou possui formato inválido."
        )

    if not isinstance(context, dict) or not context:
        raise CIOAISemanticValidationError(
            "O contexto para validação semântica está vazio ou inválido."
        )

    normalized_analysis = _normalize_semantic_text(analysis)
    context_corpus = _context_semantic_corpus(context)

    violations = []

    # --------------------------------------------------------
    # A) Quantificadores/distribuições sem evidência explícita
    # --------------------------------------------------------
    distributive_patterns = (
        r"\bpredominantemente\b",
        r"\bpredominancia\b",
        r"\ba maioria\b",
        r"\bmaior parte\b",
        r"\bgrande parte\b",
        r"\bquase todos\b",
        r"\bquase todas\b",
        r"\bmuitos desses sinais\b",
        r"\bmuitas dessas oportunidades\b",
        r"\bprincipalmente\b",
        r"\bgeralmente\b",
        r"\bem geral\b",
    )

    sentences = re.split(
        r"(?<=[.!?])\s+|\n+",
        analysis,
    )

    for sentence in sentences:
        normalized_sentence = _normalize_semantic_text(sentence)

        if not normalized_sentence:
            continue

        matched_terms = [
            pattern
            for pattern in distributive_patterns
            if re.search(pattern, normalized_sentence)
        ]

        if (
            matched_terms
            and not _sentence_has_explicit_distribution_evidence(sentence)
        ):
            violations.append({
                "code": "UNSUPPORTED_DISTRIBUTIVE_QUANTIFIER",
                "detail": sentence.strip(),
            })

    # --------------------------------------------------------
    # B) Consequência operacional criada pela IA
    # --------------------------------------------------------
    operational_patterns = (
        r"\blimita(?:m)? (?:a )?exposicao\b",
        r"\breduz(?:em)? (?:a )?exposicao\b",
        r"\bimpede(?:m)? (?:qualquer )?exposicao\b",
        r"\bimpede(?:m)? (?:a )?entrada\b",
        r"\bimpede(?:m)? (?:qualquer )?acao automatica\b",
        r"\bnao (?:e|sao) convertid[oa]s? em autorizacao de execucao\b",
        r"\bexige(?:m)? (?:a )?saida\b",
        r"\bexige(?:m)? espera\b",
        r"\bexige(?:m)? preservacao de capital\b",
        r"\bexige(?:m)? rebalanceamento\b",
        r"\bobrig(?:a|am) (?:a )?reduzir\b",
        r"\bobrig(?:a|am) (?:a )?aumentar\b",
    )

    for pattern in operational_patterns:
        for match in re.finditer(pattern, normalized_analysis):
            matched_text = match.group(0)

            # Se a própria formulação já existe no contexto de origem,
            # ela pode ser relatada; caso contrário, é criação da IA.
            if matched_text not in context_corpus:
                violations.append({
                    "code": "UNSUPPORTED_OPERATIONAL_CONSEQUENCE",
                    "detail": matched_text,
                })

    # --------------------------------------------------------
    # C) Prescrição própria sem suporte explícito na fonte
    # --------------------------------------------------------
    prescriptive_patterns = (
        r"\bdeve ser respeitad[oa]s?\b",
        r"\bdevem ser respeitad[oa]s?\b",
        r"\bdeve ser considerad[oa]s?\b",
        r"\bdevem ser considerad[oa]s?\b",
        r"\bexige cautela\b",
        r"\bexigem cautela\b",
        r"\bexige acompanhamento\b",
        r"\bexigem acompanhamento\b",
    )

    for pattern in prescriptive_patterns:
        for match in re.finditer(pattern, normalized_analysis):
            matched_text = match.group(0)

            if matched_text not in context_corpus:
                violations.append({
                    "code": "UNSUPPORTED_PRESCRIPTIVE_LANGUAGE",
                    "detail": matched_text,
                })

    # --------------------------------------------------------
    # D) Metodologia/arquitetura transformada em timing
    # --------------------------------------------------------
    # Detecta a relação indevida somente quando termos de metodologia
    # aparecem explicitamente classificados como timing na mesma frase.
    methodology_terms = (
        r"financial strength",
        r"growth",
        r"valuation",
        r"momentum(?:\s+\d+m(?:\s*\+\s*\d+m)?)?",
        r"fundamentos",
        r"desconto",
        r"ranking",
        r"score interno",
        r"filtro",
        r"peneira",
        r"\d+(?:[.,]\d+)?\s*%\s*valuation",
        r"\d+(?:[.,]\d+)?\s*%\s*desconto",
        r"\d+(?:[.,]\d+)?\s*%\s*fundamentos",
    )

    timing_relation_patterns = (
        r"\btiming\s+(?:is|esta|está|fica|permanece|e|é)\s+"
        r"(?:embedded|embutid[oa]|incorporad[oa]|basead[oa])",
        r"\b(?:embedded|embutid[oa]|incorporad[oa])\s+(?:in|no|na|nos|nas)\s+"
        r"(?:timing|sinal|sinais)",
        r"\bmetodologia\b.{0,80}\btiming\b",
        r"\barquitetura\b.{0,80}\btiming\b",
        r"\bcriterios?\b.{0,80}\btiming\b",
        r"\bcritérios?\b.{0,80}\btiming\b",
    )

    for sentence in sentences:
        normalized_sentence = _normalize_semantic_text(sentence)
        if not normalized_sentence:
            continue

        has_methodology = any(
            re.search(pattern, normalized_sentence)
            for pattern in methodology_terms
        )
        has_timing_relation = any(
            re.search(pattern, normalized_sentence)
            for pattern in timing_relation_patterns
        )

        if has_methodology and has_timing_relation:
            violations.append({
                "code": "METHODOLOGY_AS_TIMING",
                "detail": sentence.strip(),
            })

    # --------------------------------------------------------
    # E) Linguagem imperativa própria do CIO
    # --------------------------------------------------------
    # A seção de observação deve descrever fatos; não pode ordenar
    # monitoramento/acompanhamento criado pela própria IA.
    imperative_patterns = (
        r"^\s*[-*•]?\s*monitor(?:e|ar)?\b",
        r"^\s*[-*•]?\s*watch\b",
        r"^\s*[-*•]?\s*follow\b",
        r"^\s*[-*•]?\s*track\b",
        r"^\s*[-*•]?\s*acompanhe\b",
        r"^\s*[-*•]?\s*observe\b",
        r"^\s*[-*•]?\s*monitore\b",
    )

    for line in analysis.splitlines():
        normalized_line = _normalize_semantic_text(line)
        if not normalized_line:
            continue

        # Remove numeração/lista apenas para detectar o verbo inicial.
        normalized_line = re.sub(
            r"^\s*(?:[-*•]|\d+[\.\)])\s*",
            "",
            normalized_line,
        )

        if any(
            re.search(pattern, normalized_line)
            for pattern in imperative_patterns
        ):
            # Se a formulação literal não veio da fonte, é instrução criada.
            if normalized_line not in context_corpus:
                violations.append({
                    "code": "UNSUPPORTED_IMPERATIVE_LANGUAGE",
                    "detail": line.strip(),
                })

    # --------------------------------------------------------
    # F) Oportunidade transformada em possibilidade operacional
    # --------------------------------------------------------
    # "Oportunidade" pode ser relatada como fato de origem, mas não
    # convertida pela IA em possibilidade de entrada/exposição/compra.
    opportunity_operational_patterns = (
        r"\bfor potential entry opportunit(?:y|ies)\b",
        r"\bpotential entry opportunit(?:y|ies)\b",
        r"\bpossibil(?:idade|idades) de entrada\b",
        r"\bpotencial(?:is)? entrad(?:a|as)\b",
        r"\boportunidade(?:s)? de entrada\b",
        r"\bpossibil(?:idade|idades) de aumentar exposicao\b",
        r"\bpossibil(?:idade|idades) de exposicao\b",
        r"\bpotencial(?:mente)? comprar\b",
    )

    for pattern in opportunity_operational_patterns:
        for match in re.finditer(pattern, normalized_analysis):
            matched_text = match.group(0)
            if matched_text not in context_corpus:
                violations.append({
                    "code": "OPPORTUNITY_AS_OPERATIONAL_POSSIBILITY",
                    "detail": matched_text,
                })

    # Remove duplicidades preservando ordem.
    unique_violations = []
    seen = set()

    for violation in violations:
        key = (
            violation.get("code"),
            violation.get("detail"),
        )
        if key not in seen:
            seen.add(key)
            unique_violations.append(violation)

    if unique_violations:
        compact = "; ".join(
            f"{item['code']}: {item['detail']}"
            for item in unique_violations[:8]
        )

        raise CIOAISemanticValidationError(
            "Resposta da NVIDIA rejeitada pela barreira de fidelidade "
            f"semântica V1.5. Violações: {compact}"
        )

    return {
        "status": "PASS",
        "barrier_version": CIO_AI_VERSION,
        "violations": [],
        "fail_safe": True,
        "source_data_changed": False,
    }


# ============================================================
# SYSTEM PROMPT LIMPO PARA RECONSTRUÇÃO SEMÂNTICA — V1.5
# ============================================================

SEMANTIC_CORRECTION_SYSTEM_PROMPT = """
Você é a camada de reconstrução semântica do INVESTMENT CIO AI.

Reconstrua a análise usando somente o contexto estruturado fornecido.

Regras obrigatórias:
- não invente fatos, causas, relações, estatísticas ou recomendações;
- preserve sinais, scores, rankings, decisões, restrições e governança;
- preserve o escopo exato de cada evidência;
- não transforme metodologia em causa ou timing;
- mantenha metodologia, arquitetura, pesos, critérios e filtros separados de timing;
- na seção "SELEÇÃO X TIMING", nunca descreva metodologia, arquitetura, pesos,
  critérios, filtros, Financial Strength, Growth, Valuation, Momentum,
  Fundamentos ou Desconto como timing, nem diga que o timing está "embutido",
  "incorporado" ou "baseado" nesses elementos;
- somente trate algo como timing quando o contexto o identificar explicitamente
  como timing para aquele mesmo sinal ou ativo; sem essa evidência, declare apenas
  que o contexto não fornece evidência explícita de timing para aquela relação;
- use linguagem exclusivamente descritiva, sem comandos próprios de observação ou acompanhamento;
- na seção "PONTOS PRIORITÁRIOS PARA OBSERVAÇÃO", escreva somente fatos,
  estados, divergências, restrições e sinais já presentes no contexto, em forma
  nominal/descritiva; não inicie itens com verbos de ação ou acompanhamento como
  "Monitorar", "Monitor", "Monitore", "Acompanhar", "Acompanhe", "Observar",
  "Observe", "Verificar", "Verifique", "Watch", "Follow" ou "Track";
- não transforme oportunidade em possibilidade operacional de entrada, compra ou exposição;
- trate ENTRADA, ENTRADA FORTE, PRÉ-ENTRADA, AGUARDAR, AGUARDAR GATILHO,
  AGUARDAR PULLBACK e AGUARDAR ROMPIMENTO exclusivamente como rótulos/sinais
  dos sistemas quando estiverem presentes no contexto;
- ao relatar esses sinais, prefira a forma neutra:
  "o sistema informa/classifica o ticker como <SINAL>";
- não acrescente aos sinais palavras como "oportunidade de entrada",
  "possibilidade de entrada", "potencial de entrada" ou equivalentes;
- não use "maioria", "maior parte", "grande parte", "principalmente",
  "predominantemente", "geralmente", "em geral", "quase todos" ou equivalentes,
  salvo quando a MESMA frase apresentar percentual, X de Y ou X/Y que sustente
  explicitamente a distribuição;
- se não houver evidência distributiva explícita, descreva os sinais
  individualmente ou use somente "há sinais..." sem quantificar sua frequência;
- não transforme status em causa;
- não transforme coexistência em convergência;
- não derive efeitos operacionais não explicitados pela fonte;
- não transforme descrição em obrigação ou recomendação própria;
- nunca escreva como formulação própria "deve ser considerado", "deve ser considerada",
  "devem ser considerados", "devem ser consideradas", "deve ser respeitado",
  "deve ser respeitada", "devem ser respeitados", "devem ser respeitadas",
  "exige cautela" ou "exige acompanhamento"; substitua por redação puramente
  factual/descritiva, como "o contexto registra a restrição", "a restrição está
  registrada no contexto" ou "o sistema informa a restrição";
- mantenha a decisão final humana;
- produza somente a nova análise final;
- produza obrigatoriamente as 11 seções, nesta ordem:
  1. CONTEXTO GERAL
  2. RELAÇÃO ENTRE OS SISTEMAS
  3. CONVERGÊNCIAS
  4. DIVERGÊNCIAS
  5. RISCO X OPORTUNIDADE
  6. MACRO X MICRO
  7. SELEÇÃO X TIMING
  8. RESTRIÇÕES E GOVERNANÇA
  9. PONTOS PRIORITÁRIOS PARA OBSERVAÇÃO
  10. SÍNTESE CIO
  11. RASTREABILIDADE
- não reproduza o contexto JSON como resposta;
- não comente o processo de correção, rejeição ou validação.
""".strip()


# ============================================================
# AUTOCORREÇÃO SEMÂNTICA CONTROLADA — V1.5
# ============================================================

def _extract_forbidden_semantic_terms(
    validation_error: Exception,
) -> list[str]:
    """
    Extrai somente formulações efetivamente detectadas pela barreira.

    A lista é usada exclusivamente para impedir que a autocorreção
    repita, cite, exemplifique ou parafraseie a própria violação.
    """
    normalized_error = _normalize_semantic_text(validation_error)

    candidates = (
        # Quantificadores/distribuições
        "predominantemente",
        "predominancia",
        "a maioria",
        "maior parte",
        "grande parte",
        "quase todos",
        "quase todas",
        "muitos desses sinais",
        "muitas dessas oportunidades",
        "principalmente",
        "geralmente",
        "em geral",

        # Consequências operacionais
        "limita exposicao",
        "limita a exposicao",
        "reduz exposicao",
        "reduz a exposicao",
        "impede qualquer exposicao",
        "impede exposicao",
        "impede entrada",
        "impede a entrada",
        "exige saida",
        "exige a saida",
        "exige espera",
        "exige preservacao de capital",
        "exige rebalanceamento",
        "obriga a reduzir",
        "obriga reduzir",
        "obriga a aumentar",
        "obriga aumentar",

        # Prescrição
        "deve ser respeitado",
        "deve ser respeitada",
        "devem ser respeitados",
        "devem ser respeitadas",
        "deve ser considerado",
        "deve ser considerada",
        "devem ser considerados",
        "devem ser consideradas",
        "exige cautela",
        "exigem cautela",
        "exige acompanhamento",
        "exigem acompanhamento",
    )

    found = []
    seen = set()

    for candidate in candidates:
        normalized_candidate = _normalize_semantic_text(candidate)
        if normalized_candidate in normalized_error and normalized_candidate not in seen:
            seen.add(normalized_candidate)
            found.append(candidate)

    return found


def _extract_semantic_violation_codes(
    validation_error: Exception,
) -> list[str]:
    """
    Extrai apenas os CÓDIGOS das violações semânticas.

    Não reutiliza no prompt de reparo:
    - a análise rejeitada;
    - o detalhe textual rejeitado;
    - as formulações literais que causaram a rejeição.

    Isso reduz a reintrodução do próprio conteúdo inválido no prompt
    enviado ao Nemotron durante a única autocorreção semântica.
    """
    error_text = str(validation_error)

    supported_codes = (
        "UNSUPPORTED_DISTRIBUTIVE_QUANTIFIER",
        "UNSUPPORTED_OPERATIONAL_CONSEQUENCE",
        "UNSUPPORTED_PRESCRIPTIVE_LANGUAGE",
        "METHODOLOGY_AS_TIMING",
        "UNSUPPORTED_IMPERATIVE_LANGUAGE",
        "OPPORTUNITY_AS_OPERATIONAL_POSSIBILITY",
        "STRUCTURAL_EMPTY_RESPONSE",
        "STRUCTURAL_CONTEXT_DUMP",
        "STRUCTURAL_MISSING_SECTION",
        "STRUCTURAL_SECTION_ORDER",
        "STRUCTURAL_EMPTY_SECTION",
    )

    found = []
    for code in supported_codes:
        if code in error_text and code not in found:
            found.append(code)

    return found


def _build_semantic_correction_prompt(
    context: dict,
    rejected_analysis: str,
    validation_error: Exception,
) -> str:
    """
    Solicita UMA reconstrução integral usando somente o contexto
    estruturado original.

    Não reenvia:
    - a resposta rejeitada;
    - os detalhes literais da violação;
    - o prompt original com exemplos linguísticos.
    """
    del rejected_analysis

    violation_codes = _extract_semantic_violation_codes(
        validation_error
    )

    if violation_codes:
        violation_block = "\n".join(
            f"- {code}"
            for code in violation_codes
        )
    else:
        violation_block = "- SEMANTIC_FIDELITY_VIOLATION"

    context_json = json.dumps(
        context,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    return f"""
A geração anterior não passou pela validação semântica.

CLASSES DE VIOLAÇÃO DETECTADAS:
{violation_block}

REGRAS OBRIGATÓRIAS PARA A RECONSTRUÇÃO:

Reconstrua a análise integral do zero usando SOMENTE o CONTEXTO
ESTRUTURADO ORIGINAL abaixo.

A redação rejeitada não é fornecida. Não tente reconstruí-la, citá-la,
resumi-la, explicá-la ou comentá-la.

A resposta deve conter SOMENTE a nova análise final.

- Para classe distributiva, não crie distribuição, proporção,
  frequência ou predominância sem evidência numérica explícita.
- Para classe de consequência operacional, descreva somente fatos de
  origem explicitamente disponíveis e não derive efeitos operacionais
  que não estejam registrados no contexto e atribuídos à fonte.
- Para classe prescritiva, use descrição neutra dos fatos de origem e
  não transforme fatos, estados ou restrições em obrigação, orientação
  ou recomendação própria.

REGRAS GERAIS:
- produza exatamente as 11 seções abaixo, nesta ordem:
  1. CONTEXTO GERAL
  2. RELAÇÃO ENTRE OS SISTEMAS
  3. CONVERGÊNCIAS
  4. DIVERGÊNCIAS
  5. RISCO X OPORTUNIDADE
  6. MACRO X MICRO
  7. SELEÇÃO X TIMING
  8. RESTRIÇÕES E GOVERNANÇA
  9. PONTOS PRIORITÁRIOS PARA OBSERVAÇÃO
  10. SÍNTESE CIO
  11. RASTREABILIDADE
- não reproduza o contexto JSON como resposta;
- use exclusivamente o contexto estruturado original;
- não acrescente fatos, causas, relações ou recomendações;
- não altere sinais, scores, rankings ou decisões;
- não transforme restrição em efeito operacional inferido;
- não transforme descrição em prescrição;
- nunca escreva como formulação própria "deve ser considerado", "deve ser considerada",
  "devem ser considerados", "devem ser consideradas", "deve ser respeitado",
  "deve ser respeitada", "devem ser respeitados", "devem ser respeitadas",
  "exige cautela" ou "exige acompanhamento"; use somente redação factual/descritiva,
  como "o contexto registra a restrição", "a restrição está registrada no contexto"
  ou "o sistema informa a restrição";
- não transforme metodologia em timing ou causa;
- mantenha metodologia, arquitetura, pesos, critérios e filtros separados de timing;
- na seção "SELEÇÃO X TIMING", nunca descreva metodologia, arquitetura, pesos,
  critérios, filtros, Financial Strength, Growth, Valuation, Momentum,
  Fundamentos ou Desconto como timing, nem diga que o timing está "embutido",
  "incorporado" ou "baseado" nesses elementos;
- somente trate algo como timing quando o contexto o identificar explicitamente
  como timing para aquele mesmo sinal ou ativo; sem essa evidência, declare apenas
  que o contexto não fornece evidência explícita de timing para aquela relação;
- use linguagem exclusivamente descritiva, sem comandos próprios de observação ou acompanhamento;
- na seção "PONTOS PRIORITÁRIOS PARA OBSERVAÇÃO", escreva somente fatos,
  estados, divergências, restrições e sinais já presentes no contexto, em forma
  nominal/descritiva; não inicie itens com verbos de ação ou acompanhamento como
  "Monitorar", "Monitor", "Monitore", "Acompanhar", "Acompanhe", "Observar",
  "Observe", "Verificar", "Verifique", "Watch", "Follow" ou "Track";
- não transforme oportunidade em possibilidade operacional de entrada, compra ou exposição;
- preserve ENTRADA, ENTRADA FORTE, PRÉ-ENTRADA, AGUARDAR, AGUARDAR GATILHO,
  AGUARDAR PULLBACK e AGUARDAR ROMPIMENTO como rótulos literais dos sistemas;
- para esses rótulos, use formulação descritiva do tipo
  "o sistema informa/classifica o ticker como <SINAL>";
- não acrescente "oportunidade de entrada", "possibilidade de entrada",
  "potencial de entrada" ou expressão operacional equivalente;
- não use "maioria", "maior parte", "grande parte", "principalmente",
  "predominantemente", "geralmente", "em geral", "quase todos" ou equivalentes
  sem percentual, X de Y ou X/Y explícito na mesma frase;
- sem evidência distributiva explícita, descreva individualmente ou use apenas
  formulação neutra como "há sinais..." sem afirmar frequência ou predominância;
- não transforme status em causa;
- não amplie o escopo da evidência;
- não transforme coexistência em convergência;
- não crie quantificação distributiva sem evidência explícita;
- preserve Kill Switch, Hard Block, restrições e governança exatamente
  como aparecem no contexto;
- preserve a decisão final humana;
- não explique o processo de correção, rejeição ou validação.

Quando uma interpretação mais ampla não estiver explicitamente
sustentada, use formulação estritamente descritiva e de menor alcance
semântico.

CONTEXTO ESTRUTURADO ORIGINAL:
{context_json}
""".strip()


def _is_transient_nvidia_503(exc: Exception) -> bool:
    """Identifica indisponibilidade temporária HTTP 503 da NVIDIA."""
    status_code = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    response_status = getattr(response, "status_code", None)
    message = str(exc).lower()

    return (
        status_code == 503
        or response_status == 503
        or "error code: 503" in message
        or "service temporarily overloaded" in message
        or "service unavailable" in message
    )


def _request_nvidia_analysis(
    client: Any,
    selected_model: str,
    user_prompt: str,
    system_prompt: str = SYSTEM_PROMPT,
    temperature: float = 1.0,
) -> str:
    """
    Executa NVIDIA NIM com resiliência somente para HTTP 503.

    - 3 tentativas totais;
    - espera progressiva de 10s e 30s;
    - outros erros não são repetidos;
    - persistindo 503, mantém fail-safe.
    """
    max_attempts = 3
    retry_delays = (10, 30)

    for attempt in range(1, max_attempts + 1):
        try:
            completion = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=temperature,
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

            return _extract_response_text(completion)

        except Exception as exc:
            transient_503 = _is_transient_nvidia_503(exc)

            if transient_503 and attempt < max_attempts:
                time.sleep(retry_delays[attempt - 1])
                continue

            if transient_503:
                raise CIOAIResponseError(
                    "Falha na execução da NVIDIA NIM após "
                    f"{max_attempts} tentativas por indisponibilidade "
                    f"temporária HTTP 503: {exc}"
                ) from exc

            raise CIOAIResponseError(
                "Falha na execução da NVIDIA NIM: "
                f"{exc}"
            ) from exc


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

    # ========================================================
    # 1ª GERAÇÃO NVIDIA
    # ========================================================

    analysis = _request_nvidia_analysis(
        client,
        selected_model,
        prompt,
    )

    semantic_retry_used = False
    first_semantic_rejection = None

    # ========================================================
    # BARREIRA + UMA AUTOCORREÇÃO CONTROLADA — V1.5
    # ========================================================

    try:
        structural_validation = validate_ai_analysis_structure(
            analysis,
        )
        semantic_validation = validate_ai_analysis_semantics(
            analysis,
            context,
        )

    except (
        CIOAIStructuralValidationError,
        CIOAISemanticValidationError,
    ) as first_error:
        semantic_retry_used = True
        first_semantic_rejection = str(first_error)

        correction_prompt = _build_semantic_correction_prompt(
            context,
            analysis,
            first_error,
        )

        corrected_analysis = _request_nvidia_analysis(
            client,
            selected_model,
            correction_prompt,
            system_prompt=SEMANTIC_CORRECTION_SYSTEM_PROMPT,
            temperature=0.2,
        )

        # Fail-safe final:
        # a segunda resposta precisa passar pelas DUAS barreiras.
        # Persistindo falha estrutural ou semântica, a exceção é
        # propagada e nenhum relatório é aceito/publicado.
        structural_validation = validate_ai_analysis_structure(
            corrected_analysis,
        )
        semantic_validation = validate_ai_analysis_semantics(
            corrected_analysis,
            context,
        )

        analysis = corrected_analysis

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

        "structural_validation": _clone(
            structural_validation
        ),

        "semantic_validation": {
            **_clone(semantic_validation),
            "retry_used": semantic_retry_used,
            "max_semantic_retries": 1,
            "first_rejection_recorded": (
                first_semantic_rejection is not None
            ),
        },

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

            "convergence_requires_comparable_evidence": True,

            "causal_scope_must_be_preserved": True,

            "cross_asset_causal_generalization_allowed": False,

            "summary_evidence_scope_preserved": True,

            # V1.3
            "status_label_implies_cause": False,

            "quantifiers_require_explicit_evidence": True,

            "methodology_implies_signal_cause": False,

            "methodology_implies_future_signal_change": False,

            "group_statistics_may_be_invented": False,

            # V1.4
            "methodology_implies_timing": False,

            "restrictions_imply_operational_consequences": False,

            "ai_created_prescriptive_language_without_source": False,

            "prescriptive_language_requires_source_attribution": True,

            # V1.5
            "structural_report_barrier_enabled": True,

            "structural_validation_passed": (
                structural_validation.get("status") == "PASS"
            ),

            "required_report_sections": len(
                REQUIRED_REPORT_SECTIONS
            ),

            "semantic_fidelity_barrier_enabled": True,

            "semantic_validation_passed": (
                semantic_validation.get("status") == "PASS"
            ),

            "semantic_violations_accepted": False,

            "semantic_fail_safe_enabled": True,

            "semantic_auto_correction_enabled": True,

            "semantic_auto_correction_max_retries": 1,

            "semantic_auto_correction_used": semantic_retry_used,

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
    "SYSTEM_PROMPT",
    "CIOAIError",
    "CIOAIConfigurationError",
    "CIOAIInputError",
    "CIOAIResponseError",
    "CIOAISemanticValidationError",
    "CIOAIStructuralValidationError",
    "REQUIRED_REPORT_SECTIONS",
    "validate_orchestrator_context",
    "build_ai_context",
    "build_ai_prompt",
    "validate_ai_analysis_structure",
    "validate_ai_analysis_semantics",
    "run_cio_ai",
    "analyze_cio_context",
]
