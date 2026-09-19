# ============================================================
# INVESTMENT CIO AGENT
# agents/risk_agent.py
# ============================================================
#
# Camada central de risco do Investment CIO Agent.
#
# Responsabilidades:
# 1. Receber a síntese já produzida pelo Synthesis Agent.
# 2. Ler restrições e alertas de risco já produzidos pelos motores.
# 3. Separar risco global de oportunidades/seleção de ativos.
# 4. Detectar quando existe oportunidade sob restrição de risco.
# 5. Preservar integralmente os sinais originais.
# 6. Produzir um contexto de risco para as próximas camadas do CIO.
#
# Este módulo NÃO:
# - recalcula indicadores;
# - cria score quantitativo novo;
# - altera sinais;
# - reordena ativos;
# - transforma AGUARDAR em COMPRA;
# - transforma ENTRADA_FORTE em AGUARDAR;
# - executa ordens;
# - substitui decisão humana.
#
# ============================================================

from datetime import datetime, timezone


RISK_AGENT_VERSION = "1.0"


# ============================================================
# EXCEÇÕES
# ============================================================

class RiskAgentError(Exception):
    """Erro geral da camada central de risco."""


class InvalidSynthesisError(RiskAgentError):
    """Síntese inválida ou incompleta para análise de risco."""


# ============================================================
# AUXILIARES
# ============================================================

def _safe_dict(value):
    if isinstance(value, dict):
        return value
    return {}


def _safe_list(value):
    if isinstance(value, list):
        return value
    return []


def _normalize_text(value):
    if value is None:
        return None
    return str(value).strip().upper()


def _unique_list(values):
    result = []

    for value in values:
        if value is None:
            continue

        if value not in result:
            result.append(value)

    return result


def _validate_synthesis(synthesis):
    if not isinstance(synthesis, dict):
        raise InvalidSynthesisError(
            "A síntese deve ser um dicionário."
        )

    required = (
        "synthesis_version",
        "status",
        "comparison",
        "risk",
        "policy",
    )

    missing = [
        field
        for field in required
        if field not in synthesis
    ]

    if missing:
        raise InvalidSynthesisError(
            "Síntese incompleta. Campos ausentes: "
            + ", ".join(missing)
        )

    if not isinstance(
        synthesis.get("comparison"),
        dict
    ):
        raise InvalidSynthesisError(
            "Campo 'comparison' deve ser um dicionário."
        )

    if not isinstance(
        synthesis.get("risk"),
        dict
    ):
        raise InvalidSynthesisError(
            "Campo 'risk' deve ser um dicionário."
        )

    if not isinstance(
        synthesis.get("policy"),
        dict
    ):
        raise InvalidSynthesisError(
            "Campo 'policy' deve ser um dicionário."
        )

    return True


# ============================================================
# EXTRAÇÃO DE RISCO GLOBAL
# ============================================================

def _extract_global_risk(synthesis):
    risk = _safe_dict(
        synthesis.get("risk")
    )

    comparison = _safe_dict(
        synthesis.get("comparison")
    )

    return {
        "sp500_risk_level": (
            risk.get("sp500_risk_level")
        ),
        "global_risk_level": (
            risk.get("global_risk_level")
        ),
        "global_survival_status": (
            risk.get("global_survival_status")
        ),
        "global_kill_switch": (
            risk.get("global_kill_switch")
        ),
        "alerts": list(
            _safe_list(risk.get("alerts"))
        ),
        "sp500_stance": (
            comparison.get("sp500_stance")
        ),
        "global_stance": (
            comparison.get("global_stance")
        ),
        "relationship": (
            comparison.get("relationship")
        ),
    }


# ============================================================
# RESTRIÇÕES DE RISCO
# ============================================================

def _detect_global_restrictions(global_risk):
    """
    Detecta restrições usando somente fatos já presentes
    na síntese. Não calcula um novo score de risco.
    """

    restrictions = []

    if global_risk.get(
        "global_kill_switch"
    ) is True:

        restrictions.append({
            "code": "GLOBAL_KILL_SWITCH_ACTIVE",
            "source": "COPIAULTIMOROB",
            "severity": "CRITICAL",
            "message": (
                "Survival Kill Switch global ativo."
            ),
        })

    global_level = _normalize_text(
        global_risk.get(
            "global_risk_level"
        )
    )

    if global_level in {
        "CRITICO",
        "CRÍTICO",
        "CRITICAL",
    }:

        restrictions.append({
            "code": "GLOBAL_RISK_CRITICAL",
            "source": "COPIAULTIMOROB",
            "severity": "CRITICAL",
            "message": (
                "Nível global de risco classificado "
                "como crítico pelo sistema de origem."
            ),
        })

    global_stance = _normalize_text(
        global_risk.get(
            "global_stance"
        )
    )

    if global_stance == "DEFENSIVE":

        restrictions.append({
            "code": "GLOBAL_DEFENSIVE_STANCE",
            "source": "COPIAULTIMOROB",
            "severity": "HIGH",
            "message": (
                "Postura global defensiva identificada "
                "pela síntese."
            ),
        })

    relationship = _normalize_text(
        global_risk.get(
            "relationship"
        )
    )

    if relationship == "DIVERGENCE":

        restrictions.append({
            "code": "MACRO_RISK_DIVERGENCE",
            "source": "SYNTHESIS_AGENT",
            "severity": "WARNING",
            "message": (
                "SP500 Cycle Atlas e COPIAULTIMOROB "
                "apresentam posturas divergentes."
            ),
        })

    return restrictions


# ============================================================
# EVIDÊNCIAS DE SELEÇÃO E OPORTUNIDADES
# ============================================================

def _extract_layer_evidence(synthesis):
    """
    Preserva os objetos recebidos da síntese e sua ordem.
    """

    layers = _safe_dict(
        synthesis.get("layers")
    )

    asset_selection = list(
        _safe_list(
            layers.get("ASSET_SELECTION")
        )
    )

    opportunity_scanners = list(
        _safe_list(
            layers.get("OPPORTUNITY_SCANNER")
        )
    )

    return {
        "asset_selection": asset_selection,
        "opportunity_scanners": (
            opportunity_scanners
        ),
    }


def _collect_source_signals(evidence):
    """
    Coleta sinais existentes apenas para evidência.
    Não os classifica, pontua ou modifica.
    """

    collected = []

    for system in (
        evidence["asset_selection"]
        + evidence["opportunity_scanners"]
    ):

        system_id = system.get("system_id")
        system_name = system.get("system_name")

        decision_signal = system.get("signal")

        if decision_signal is not None:
            collected.append({
                "system_id": system_id,
                "system_name": system_name,
                "scope": "SYSTEM",
                "signal": decision_signal,
            })

        for position in _safe_list(
            system.get("positions")
        ):

            signal = (
                position.get("entry_signal")
                or position.get("signal")
                or position.get("final_status")
                or position.get("decision")
            )

            if signal is not None:
                collected.append({
                    "system_id": system_id,
                    "system_name": system_name,
                    "scope": "POSITION",
                    "ticker": position.get("ticker"),
                    "signal": signal,
                })

        for opportunity in _safe_list(
            system.get("opportunities")
        ):

            signal = (
                opportunity.get("signal")
                or opportunity.get("signal_status")
                or opportunity.get("final_status")
                or opportunity.get("decision")
            )

            if signal is not None:
                collected.append({
                    "system_id": system_id,
                    "system_name": system_name,
                    "scope": "OPPORTUNITY",
                    "ticker": opportunity.get("ticker"),
                    "signal": signal,
                })

    return collected


# ============================================================
# TENSÃO ENTRE RISCO E OPORTUNIDADES
# ============================================================

def _has_positive_entry_evidence(source_signals):
    """
    Identifica apenas a existência de sinais de entrada
    explicitamente produzidos pelos motores.

    Isso NÃO significa autorização de compra.
    """

    positive_terms = {
        "ENTRADA FORTE",
        "ENTRADA_FORTE",
        "ENTRADA",
        "ENTRADA APROVADA",
        "ENTRADA_APROVADA",
        "ENTRADA PARCIAL",
        "ENTRADA_PARCIAL",
        "COMPRA",
        "COMPRAR AGORA",
        "COMPRAR_AGORA",
    }

    for item in source_signals:
        signal = _normalize_text(
            item.get("signal")
        )

        if signal in positive_terms:
            return True

    return False


def _build_risk_opportunity_context(
    restrictions,
    source_signals,
):
    """
    Registra coexistência de risco e oportunidades.
    Não resolve a tensão substituindo os motores.
    """

    has_restrictions = bool(restrictions)

    has_positive_entry = (
        _has_positive_entry_evidence(
            source_signals
        )
    )

    if (
        has_restrictions
        and has_positive_entry
    ):
        state = "OPPORTUNITY_UNDER_RISK_RESTRICTION"

        interpretation = (
            "Existem sinais de entrada produzidos por "
            "motores específicos ao mesmo tempo em que "
            "há restrições de risco global. Os sinais "
            "originais permanecem preservados."
        )

    elif has_restrictions:
        state = "RISK_RESTRICTION_PRESENT"

        interpretation = (
            "Existem restrições de risco global "
            "registradas pelos sistemas de origem."
        )

    elif has_positive_entry:
        state = "ENTRY_EVIDENCE_WITHOUT_GLOBAL_RESTRICTION"

        interpretation = (
            "Existem sinais de entrada produzidos por "
            "motores específicos e nenhuma restrição "
            "global foi detectada nesta camada."
        )

    else:
        state = "NO_ENTRY_EVIDENCE_NO_GLOBAL_RESTRICTION"

        interpretation = (
            "Não foi identificada coexistência de "
            "sinais explícitos de entrada com "
            "restrições globais nesta análise."
        )

    return {
        "state": state,
        "has_global_restrictions": (
            has_restrictions
        ),
        "has_positive_entry_evidence": (
            has_positive_entry
        ),
        "interpretation": interpretation,
    }


# ============================================================
# STATUS DA CAMADA DE RISCO
# ============================================================

def _determine_risk_agent_status(
    synthesis,
    restrictions,
):
    synthesis_status = _normalize_text(
        synthesis.get("status")
    )

    if synthesis_status == "ERROR":
        return "ERROR"

    if synthesis_status == "DATA_INSUFFICIENT":
        return "DATA_INSUFFICIENT"

    critical = any(
        restriction.get("severity")
        == "CRITICAL"
        for restriction in restrictions
    )

    if critical:
        return "WARNING"

    if synthesis_status == "WARNING":
        return "WARNING"

    return "OK"


# ============================================================
# INTERFACE PRINCIPAL
# ============================================================

def assess_risk(synthesis):
    """
    Produz o contexto central de risco.

    O retorno é descritivo e de governança.
    Não é recomendação de investimento.
    """

    _validate_synthesis(
        synthesis
    )

    global_risk = _extract_global_risk(
        synthesis
    )

    restrictions = (
        _detect_global_restrictions(
            global_risk
        )
    )

    evidence = _extract_layer_evidence(
        synthesis
    )

    source_signals = (
        _collect_source_signals(
            evidence
        )
    )

    risk_opportunity_context = (
        _build_risk_opportunity_context(
            restrictions,
            source_signals,
        )
    )

    status = (
        _determine_risk_agent_status(
            synthesis,
            restrictions,
        )
    )

    restriction_codes = [
        item.get("code")
        for item in restrictions
    ]

    return {
        "risk_agent_version": (
            RISK_AGENT_VERSION
        ),

        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),

        "status": status,

        "source_synthesis_version": (
            synthesis.get(
                "synthesis_version"
            )
        ),

        "global_risk": global_risk,

        "restrictions": restrictions,

        "restriction_codes": (
            _unique_list(
                restriction_codes
            )
        ),

        "evidence": evidence,

        "source_signals": (
            source_signals
        ),

        "risk_opportunity_context": (
            risk_opportunity_context
        ),

        "policy": {
            "source_signals_preserved": True,
            "source_order_preserved": True,
            "indicators_recalculated": False,
            "new_quantitative_score_created": False,
            "source_decisions_overridden": False,
            "risk_restrictions_change_source_signals": False,
            "selection_systems_used_as_macro_votes": False,
            "opportunity_systems_used_as_macro_votes": False,
            "broker_execution_allowed": False,
            "human_decision_required": True,
        },
    }


# ============================================================
# INTERFACE GENÉRICA
# ============================================================

def run_risk_agent(synthesis):
    return assess_risk(
        synthesis
    )
