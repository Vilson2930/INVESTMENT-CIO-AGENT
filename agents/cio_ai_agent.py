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
# - executa operações financeiras.
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

CIO_AI_VERSION = "1.0"

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
                    {}
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

Sua função é RELACIONAR os sistemas entre si.

Você NÃO substitui os motores quantitativos.

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
   - fatos.

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

11. Identifique convergências reais.

12. Identifique divergências reais.

13. Relacione:
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

17. Quando não houver evidência suficiente, declare isso.

18. Não execute operações financeiras.

19. Não produza comandos para corretora.

20. A decisão final permanece humana.

21. Preserve a ordem original dos ativos e oportunidades.

22. AGUARDAR não significa rejeição.

23. RESERVA ESTRATÉGICA não significa rejeição ou exclusão.

24. Não reordene resultados do AI_INFRASTRUCTURE_SCANNER
    utilizando interpretação ou score próprio.

OBJETIVO:

Transformar os resultados dos sete sistemas em uma análise
CIO única, coerente e rastreável, explicando COMO os sistemas
se relacionam entre si.

A análise deve servir como apoio à decisão humana.
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

Estruture a resposta exatamente nas seguintes seções:

1. CONTEXTO GERAL

Explique o cenário conjunto identificado pelos sistemas.

2. RELAÇÃO ENTRE OS SISTEMAS

Explique como regime, risco global, seleção de ativos,
timing e scanners de oportunidades se relacionam.

3. CONVERGÊNCIAS

Identifique apenas convergências sustentadas pelos dados.

4. DIVERGÊNCIAS

Identifique divergências reais.

Explique se a divergência decorre de funções diferentes
dos sistemas.

5. RISCO X OPORTUNIDADE

Mostre se existem oportunidades específicas dentro de um
ambiente de risco ou restrição global.

6. MACRO X MICRO

Relacione os motores macro e de risco com os motores de
seleção e oportunidades.

7. SELEÇÃO X TIMING

Explique a relação entre ativos selecionados e o momento
indicado pelos motores.

Não altere os sinais originais.

8. RESTRIÇÕES E GOVERNANÇA

Explique as restrições presentes.

Kill Switch e Hard Block devem ser apresentados exatamente
como constam no contexto.

9. PONTOS PRIORITÁRIOS PARA OBSERVAÇÃO

Identifique os principais pontos que merecem acompanhamento.

Não crie novos indicadores ou scores.

10. SÍNTESE CIO

Produza uma síntese integrada do cenário.

11. RASTREABILIDADE

Informe quais sistemas sustentam as principais conclusões.

Finalize obrigatoriamente declarando:

- nenhum sinal quantitativo foi alterado;
- nenhum indicador foi recalculado;
- nenhum novo score quantitativo foi criado;
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
