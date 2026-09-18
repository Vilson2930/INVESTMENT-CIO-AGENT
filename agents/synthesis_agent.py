# ============================================================
# INVESTMENT CIO AGENT
# agents/synthesis_agent.py
# ============================================================
#
# Camada central de síntese entre sistemas quantitativos.
#
# Responsabilidades:
# 1. Receber outputs já padronizados pelo Collector.
# 2. Preservar as decisões originais dos robôs.
# 3. Identificar concordâncias.
# 4. Identificar divergências.
# 5. Consolidar alertas de risco.
# 6. Produzir uma visão executiva para o CIO Agent.
#
# Este módulo NÃO:
# - recalcula indicadores;
# - altera sinais;
# - substitui decisões dos robôs;
# - executa ordens;
# - cria recomendação de compra ou venda.
#
# ============================================================

from datetime import datetime, timezone


SYNTHESIS_VERSION = "1.1"


# ============================================================
# EXCEÇÕES
# ============================================================

class SynthesisError(Exception):
    """Erro geral da camada de síntese."""


class InvalidSystemOutputError(SynthesisError):
    """Output de sistema inválido para síntese."""


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _normalize_text(value):

    if value is None:
        return None

    return str(value).strip().upper()


def _safe_dict(value):

    if isinstance(value, dict):
        return value

    return {}


def _safe_list(value):

    if isinstance(value, list):
        return value

    return []


def _flatten_alerts(value):
    """
    Normaliza alertas sem alterar seu conteúdo semântico.

    Aceita:
    - string simples;
    - listas aninhadas;
    - strings que representam listas Python/JSON.

    Retorna sempre uma lista plana de strings.
    """
    import ast

    result = []

    def visit(item):
        if item is None:
            return

        if isinstance(item, (list, tuple, set)):
            for child in item:
                visit(child)
            return

        if isinstance(item, str):
            stripped = item.strip()

            if not stripped:
                return

            if (
                (stripped.startswith("[") and stripped.endswith("]"))
                or (stripped.startswith("(") and stripped.endswith(")"))
            ):
                try:
                    parsed = ast.literal_eval(stripped)
                except (ValueError, SyntaxError):
                    parsed = None

                if isinstance(parsed, (list, tuple, set)):
                    visit(parsed)
                    return

            result.append(stripped)
            return

        result.append(str(item))

    visit(value)
    return _unique_list(result)


def _unique_list(values):

    result = []

    for value in values:

        if value is None:
            continue

        if value not in result:
            result.append(value)

    return result


# ============================================================
# VALIDAÇÃO DOS OUTPUTS RECEBIDOS
# ============================================================

def _validate_system_output(output):

    if not isinstance(output, dict):

        raise InvalidSystemOutputError(
            "Cada output deve ser um dicionário."
        )

    required_fields = (
        "system_id",
        "system_name",
        "status",
        "decision",
        "risk",
    )

    missing = [
        field
        for field in required_fields
        if field not in output
    ]

    if missing:

        raise InvalidSystemOutputError(
            "Output incompleto. Campos ausentes: "
            + ", ".join(missing)
        )

    if not isinstance(
        output.get("decision"),
        dict
    ):

        raise InvalidSystemOutputError(
            "Campo 'decision' deve ser um dicionário."
        )

    if not isinstance(
        output.get("risk"),
        dict
    ):

        raise InvalidSystemOutputError(
            "Campo 'risk' deve ser um dicionário."
        )

    return True


# ============================================================
# EXTRAÇÃO DO SP500 CYCLE ATLAS
# ============================================================

def _extract_sp500_view(output):

    decision = _safe_dict(
        output.get("decision")
    )

    risk = _safe_dict(
        output.get("risk")
    )

    metrics = _safe_dict(
        output.get("metrics")
    )

    audit = _safe_dict(
        output.get("audit")
    )

    return {

        "system_id": output.get(
            "system_id"
        ),

        "system_name": output.get(
            "system_name"
        ),

        "status": output.get(
            "status"
        ),

        "signal": decision.get(
            "signal"
        ),

        "operational_regime": (
            decision.get(
                "operational_regime"
            )
            or metrics.get(
                "operational_regime"
            )
        ),

        "new_contribution_equity": (
            decision.get(
                "new_contribution_equity"
            )
        ),

        "new_contribution_reserve": (
            decision.get(
                "new_contribution_reserve"
            )
        ),

        "risk_level": risk.get(
            "level"
        ),

        "risk_alerts": _safe_list(
            risk.get("alerts")
        ),

        "audit_status": audit.get(
            "audit_status"
        ),

        "engine_consistency_score": (
            audit.get(
                "engine_consistency_score"
            )
        ),

        "data_quality_score": (
            audit.get(
                "data_quality_score"
            )
        ),

        "ai_dissent": audit.get(
            "ai_dissent"
        ),
    }


# ============================================================
# EXTRAÇÃO DO COPIAULTIMOROB
# ============================================================

def _extract_global_view(output):

    decision = _safe_dict(
        output.get("decision")
    )

    risk = _safe_dict(
        output.get("risk")
    )

    metrics = _safe_dict(
        output.get("metrics")
    )

    audit = _safe_dict(
        output.get("audit")
    )

    return {

        "system_id": output.get(
            "system_id"
        ),

        "system_name": output.get(
            "system_name"
        ),

        "status": output.get(
            "status"
        ),

        "signal": decision.get(
            "signal"
        ),

        "macro_regime": metrics.get(
            "macro_regime"
        ),

        "final_verdict": metrics.get(
            "final_verdict"
        ),

        "committee_action": metrics.get(
            "committee_action"
        ),

        "integrated_risk_level": (
            metrics.get(
                "integrated_risk_level"
            )
        ),

        "survival_status": metrics.get(
            "survival_status"
        ),

        "survival_kill_switch": (
            metrics.get(
                "survival_kill_switch"
            )
        ),

        "stress_level": metrics.get(
            "stress_level"
        ),

        "risk_budget_level": metrics.get(
            "risk_budget_level"
        ),

        "risk_level": risk.get(
            "level"
        ),

        "risk_alerts": _safe_list(
            risk.get("alerts")
        ),

        "ai_audit_status": audit.get(
            "ai_audit_status"
        ),

        "ai_audit_score": audit.get(
            "ai_audit_score"
        ),

        "nvidia_audit_status": (
            audit.get(
                "nvidia_audit_status"
            )
        ),

        "nvidia_audit_score": (
            audit.get(
                "nvidia_audit_score"
            )
        ),
    }


# ============================================================
# CLASSIFICAÇÃO DO SP500
# ============================================================

def _classify_sp500(view):

    signal = _normalize_text(
        view.get("signal")
    )

    regime = _normalize_text(
        view.get("operational_regime")
    )

    equity = view.get(
        "new_contribution_equity"
    )

    reserve = view.get(
        "new_contribution_reserve"
    )

    if signal in {
        "SELL",
        "REDUCE",
        "EXIT",
    }:

        return "DEFENSIVE"

    if signal in {
        "BUY",
        "ACCUMULATE",
        "STRONG_BUY",
    }:

        return "RISK_SEEKING"

    if regime:

        if any(
            term in regime
            for term in (
                "RED",
                "BEAR",
                "DEFENSIVE",
                "CRISIS",
            )
        ):

            return "DEFENSIVE"

        if any(
            term in regime
            for term in (
                "GREEN",
                "EXPANSION",
                "BULL",
            )
        ):

            if (
                equity is not None
                and reserve is not None
                and equity > reserve
            ):

                return "RISK_SEEKING"

    if (
        equity is not None
        and reserve is not None
    ):

        if equity > reserve:
            return "RISK_SEEKING"

        if reserve > equity:
            return "DEFENSIVE"

    return "NEUTRAL"


# ============================================================
# CLASSIFICAÇÃO DO COPIAULTIMOROB
# ============================================================

def _classify_global(view):

    kill_switch = view.get(
        "survival_kill_switch"
    )

    final_verdict = _normalize_text(
        view.get("final_verdict")
    )

    committee_action = _normalize_text(
        view.get("committee_action")
    )

    risk_level = _normalize_text(
        view.get("risk_level")
    )

    signal = _normalize_text(
        view.get("signal")
    )

    if kill_switch is True:

        return "DEFENSIVE"

    if final_verdict:

        if any(
            term in final_verdict
            for term in (
                "REPROVADO",
                "BLOCK",
                "BLOQUEAR",
                "CRITICO",
                "CRÍTICO",
            )
        ):

            return "DEFENSIVE"

    if committee_action:

        if any(
            term in committee_action
            for term in (
                "BLOQUEAR",
                "REDUZIR",
                "REDUCE",
                "BLOCK",
            )
        ):

            return "DEFENSIVE"

    if risk_level in {
        "CRITICO",
        "CRÍTICO",
        "HIGH",
        "ALTO",
    }:

        return "DEFENSIVE"

    if signal in {
        "RISK_ON",
        "COMPRA",
        "BUY",
        "EXPANSAO",
        "EXPANSÃO",
    }:

        return "RISK_SEEKING"

    return "NEUTRAL"


# ============================================================
# RELAÇÃO ENTRE OS DOIS SISTEMAS
# ============================================================

def _compare_stances(
    sp500_stance,
    global_stance
):

    if (
        sp500_stance == global_stance
        and sp500_stance != "NEUTRAL"
    ):

        return "AGREEMENT"

    if (
        sp500_stance == "NEUTRAL"
        and global_stance == "NEUTRAL"
    ):

        return "NEUTRAL_AGREEMENT"

    if (
        sp500_stance == "NEUTRAL"
        or global_stance == "NEUTRAL"
    ):

        return "MIXED_CONTEXT"

    return "DIVERGENCE"


# ============================================================
# CONSOLIDAÇÃO DOS ALERTAS
# ============================================================

def _build_risk_alerts(
    sp500_view,
    global_view
):

    alerts = []

    for alert in _flatten_alerts(
        sp500_view.get(
            "risk_alerts",
            []
        )
    ):

        alerts.append(
            f"SP500_CYCLE_ATLAS: {alert}"
        )

    for alert in _flatten_alerts(
        global_view.get(
            "risk_alerts",
            []
        )
    ):

        alerts.append(
            f"COPIAULTIMOROB: {alert}"
        )

    if global_view.get(
        "survival_kill_switch"
    ) is True:

        alerts.append(
            "COPIAULTIMOROB: "
            "Survival Kill Switch ativo."
        )

    final_verdict = global_view.get(
        "final_verdict"
    )

    if final_verdict:

        normalized = _normalize_text(
            final_verdict
        )

        if normalized not in {
            "APROVADO",
            "OK",
            "NORMAL",
        }:

            alerts.append(
                "COPIAULTIMOROB: "
                f"veredito {final_verdict}."
            )

    return _unique_list(
        alerts
    )


# ============================================================
# QUALIDADE DA SÍNTESE
# ============================================================

def _determine_synthesis_status(
    sp500_view,
    global_view
):

    statuses = {
        _normalize_text(
            sp500_view.get("status")
        ),
        _normalize_text(
            global_view.get("status")
        ),
    }

    if "ERROR" in statuses:
        return "ERROR"

    if "DATA_INSUFFICIENT" in statuses:
        return "DATA_INSUFFICIENT"

    if "WARNING" in statuses:
        return "WARNING"

    return "OK"


# ============================================================
# SÍNTESE EXECUTIVA
# ============================================================

def build_synthesis(
    sp500_output,
    global_output
):

    _validate_system_output(
        sp500_output
    )

    _validate_system_output(
        global_output
    )

    if (
        sp500_output.get("system_name")
        != "SP500_CYCLE_ATLAS"
    ):

        raise InvalidSystemOutputError(
            "Primeiro output deve ser "
            "SP500_CYCLE_ATLAS."
        )

    if (
        global_output.get("system_name")
        != "COPIAULTIMOROB"
    ):

        raise InvalidSystemOutputError(
            "Segundo output deve ser "
            "COPIAULTIMOROB."
        )

    sp500_view = _extract_sp500_view(
        sp500_output
    )

    global_view = _extract_global_view(
        global_output
    )

    sp500_stance = _classify_sp500(
        sp500_view
    )

    global_stance = _classify_global(
        global_view
    )

    relationship = _compare_stances(
        sp500_stance,
        global_stance
    )

    risk_alerts = _build_risk_alerts(
        sp500_view,
        global_view
    )

    synthesis_status = (
        _determine_synthesis_status(
            sp500_view,
            global_view
        )
    )

    if relationship == "AGREEMENT":

        interpretation = (
            "Os dois sistemas apresentam "
            "postura quantitativa compatível."
        )

    elif relationship == "NEUTRAL_AGREEMENT":

        interpretation = (
            "Os dois sistemas apresentam "
            "postura predominantemente neutra."
        )

    elif relationship == "DIVERGENCE":

        interpretation = (
            "Os sistemas apresentam posturas "
            "quantitativas divergentes. "
            "As decisões originais foram "
            "preservadas e a divergência deve "
            "ser analisada pelo CIO."
        )

    else:

        interpretation = (
            "Um dos sistemas apresenta postura "
            "neutra enquanto o outro apresenta "
            "direcionamento definido. "
            "O contexto é misto."
        )

    return {

        "synthesis_version": (
            SYNTHESIS_VERSION
        ),

        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),

        "status": synthesis_status,

        "systems_analyzed": [
            "SP500_CYCLE_ATLAS",
            "COPIAULTIMOROB",
        ],

        "source_decisions": {

            "SP500_CYCLE_ATLAS": {

                "signal": (
                    sp500_view.get(
                        "signal"
                    )
                ),

                "operational_regime": (
                    sp500_view.get(
                        "operational_regime"
                    )
                ),

                "new_contribution_equity": (
                    sp500_view.get(
                        "new_contribution_equity"
                    )
                ),

                "new_contribution_reserve": (
                    sp500_view.get(
                        "new_contribution_reserve"
                    )
                ),

                "stance": sp500_stance,
            },

            "COPIAULTIMOROB": {

                "signal": (
                    global_view.get(
                        "signal"
                    )
                ),

                "macro_regime": (
                    global_view.get(
                        "macro_regime"
                    )
                ),

                "final_verdict": (
                    global_view.get(
                        "final_verdict"
                    )
                ),

                "committee_action": (
                    global_view.get(
                        "committee_action"
                    )
                ),

                "stance": global_stance,
            },
        },

        "comparison": {

            "relationship": relationship,

            "sp500_stance": (
                sp500_stance
            ),

            "global_stance": (
                global_stance
            ),

            "interpretation": (
                interpretation
            ),
        },

        "risk": {

            "sp500_risk_level": (
                sp500_view.get(
                    "risk_level"
                )
            ),

            "global_risk_level": (
                global_view.get(
                    "risk_level"
                )
            ),

            "global_survival_status": (
                global_view.get(
                    "survival_status"
                )
            ),

            "global_kill_switch": (
                global_view.get(
                    "survival_kill_switch"
                )
            ),

            "alerts": risk_alerts,
        },

        "audit": {

            "sp500": {

                "status": (
                    sp500_view.get(
                        "audit_status"
                    )
                ),

                "engine_consistency_score": (
                    sp500_view.get(
                        "engine_consistency_score"
                    )
                ),

                "data_quality_score": (
                    sp500_view.get(
                        "data_quality_score"
                    )
                ),

                "ai_dissent": (
                    sp500_view.get(
                        "ai_dissent"
                    )
                ),
            },

            "copiaultimorob": {

                "ai_audit_status": (
                    global_view.get(
                        "ai_audit_status"
                    )
                ),

                "ai_audit_score": (
                    global_view.get(
                        "ai_audit_score"
                    )
                ),

                "nvidia_audit_status": (
                    global_view.get(
                        "nvidia_audit_status"
                    )
                ),

                "nvidia_audit_score": (
                    global_view.get(
                        "nvidia_audit_score"
                    )
                ),
            },
        },

        "policy": {

            "signals_preserved": True,

            "indicators_recalculated": False,

            "source_decisions_overridden": False,

            "broker_execution_allowed": False,

            "human_decision_required": True,
        },
    }


# ============================================================
# INTERFACE GENÉRICA
# ============================================================

def synthesize_outputs(outputs):

    if not isinstance(outputs, list):

        raise SynthesisError(
            "outputs deve ser uma lista."
        )

    sp500_output = None
    global_output = None

    for output in outputs:

        if not isinstance(output, dict):
            continue

        system_name = output.get(
            "system_name"
        )

        if (
            system_name
            == "SP500_CYCLE_ATLAS"
        ):

            sp500_output = output

        elif (
            system_name
            == "COPIAULTIMOROB"
        ):

            global_output = output

    if sp500_output is None:

        raise SynthesisError(
            "Output do SP500_CYCLE_ATLAS "
            "não encontrado."
        )

    if global_output is None:

        raise SynthesisError(
            "Output do COPIAULTIMOROB "
            "não encontrado."
        )

    return build_synthesis(
        sp500_output,
        global_output
    )
