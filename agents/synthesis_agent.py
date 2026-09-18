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


SYNTHESIS_VERSION = "2.0"


# ============================================================
# REGISTRO DOS SETE SISTEMAS E CAMADAS FUNCIONAIS
# ============================================================

SYSTEM_REGISTRY = {
    "sp500_cycle": {
        "canonical_name": "SP500_CYCLE_ATLAS",
        "layer": "REGIME",
        "aliases": {"SP500_CYCLE_ATLAS"},
    },
    "global_portfolio": {
        "canonical_name": "COPIAULTIMOROB",
        "layer": "GLOBAL_RISK",
        "aliases": {"COPIAULTIMOROB"},
    },
    "us_equities": {
        "canonical_name": "US_EQUITIES",
        "layer": "ASSET_SELECTION",
        "aliases": {
            "US_EQUITIES",
            "PORTFOLIO_ACOES_AMERICANA",
            "PORTFOLIO ACOES AMERICANA",
            "PORTFOLIO AÇÕES AMERICANA",
            "PORTFOLIO-ACOES-AMERICANA-TESTE",
            "PORTFOLIO-AÇÕES-AMERICANA-TESTE",
        },
    },
    "b3_equities": {
        "canonical_name": "B3_EQUITIES",
        "layer": "ASSET_SELECTION",
        "aliases": {
            "B3_EQUITIES",
            "PORTFOLIO_B3_OPERATIONAL",
            "PORTFOLIO-B3-OPERATIONAL",
        },
    },
    "fii": {
        "canonical_name": "FII",
        "layer": "ASSET_SELECTION",
        "aliases": {
            "FII",
            "FII_INSTITUTIONAL_SCANNER",
            "FII INSTITUTIONAL SCANNER",
            "FII-SCANNER",
        },
    },
    "ai_infrastructure": {
        "canonical_name": "AI_INFRASTRUCTURE",
        "layer": "OPPORTUNITY_SCANNER",
        "aliases": {
            "AI_INFRASTRUCTURE",
            "AI_INFRASTRUCTURE_SCANNER",
            "AI INFRASTRUCTURE SCANNER",
        },
    },
    "growth": {
        "canonical_name": "GROWTH",
        "layer": "OPPORTUNITY_SCANNER",
        "aliases": {
            "GROWTH",
            "GROWTH_OPPORTUNITY_ENGINE",
            "GROWTH OPPORTUNITY ENGINE",
        },
    },
}

EXPECTED_SYSTEM_IDS = tuple(SYSTEM_REGISTRY.keys())


def _identify_registered_system(output):
    """
    Identifica um output padronizado sem recalcular ou reinterpretar sinais.

    Prioridade:
    1. system_id padronizado pelo adapter;
    2. system_name / aliases conhecidos.
    """
    system_id = str(output.get("system_id") or "").strip()
    if system_id in SYSTEM_REGISTRY:
        return system_id

    system_name = _normalize_text(output.get("system_name"))
    if not system_name:
        return None

    for registered_id, config in SYSTEM_REGISTRY.items():
        aliases = {_normalize_text(value) for value in config["aliases"]}
        if system_name in aliases:
            return registered_id

    return None


def _extract_generic_evidence(output, registered_id):
    """
    Extrai somente evidências já produzidas pelo adapter.
    Não cria score, não reordena ativos e não altera sinais.
    """
    decision = _safe_dict(output.get("decision"))
    risk = _safe_dict(output.get("risk"))
    opportunities = _safe_list(output.get("opportunities"))
    positions = _safe_list(output.get("positions"))

    return {
        "system_id": registered_id,
        "system_name": output.get("system_name"),
        "layer": SYSTEM_REGISTRY[registered_id]["layer"],
        "status": output.get("status"),
        "signal": decision.get("signal"),
        "confidence": decision.get("confidence"),
        "summary": decision.get("summary"),
        "risk_level": risk.get("level"),
        "risk_score": risk.get("score"),
        "risk_alerts": _flatten_alerts(risk.get("alerts", [])),
        "positions_count": len(positions),
        "opportunities_count": len(opportunities),
        # Cópias rasas preservando exatamente a ordem recebida.
        "positions": list(positions),
        "opportunities": list(opportunities),
    }


def _build_system_layers(outputs_by_id):
    layers = {
        "REGIME": [],
        "GLOBAL_RISK": [],
        "ASSET_SELECTION": [],
        "OPPORTUNITY_SCANNER": [],
    }

    for registered_id in EXPECTED_SYSTEM_IDS:
        output = outputs_by_id.get(registered_id)
        if output is None:
            continue

        evidence = _extract_generic_evidence(output, registered_id)
        layers[evidence["layer"]].append(evidence)

    return layers


def _build_all_system_alerts(outputs_by_id):
    alerts = []

    for registered_id in EXPECTED_SYSTEM_IDS:
        output = outputs_by_id.get(registered_id)
        if output is None:
            continue

        risk = _safe_dict(output.get("risk"))
        for alert in _flatten_alerts(risk.get("alerts", [])):
            alerts.append(f"{output.get('system_name')}: {alert}")

    return _unique_list(alerts)


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
# INTERFACE GENÉRICA — SETE SISTEMAS
# ============================================================

def synthesize_outputs(outputs):
    """
    Síntese institucional V2.

    Compatibilidade:
    - SP500_CYCLE_ATLAS e COPIAULTIMOROB continuam sendo a base
      da comparação macro/risco já validada na versão 1.1.
    - Os outros cinco sistemas entram como evidências nas suas
      camadas funcionais, sem serem convertidos em postura macro.
    - A função continua aceitando apenas os dois motores-base,
      preservando compatibilidade com testes e integrações antigas.
    """

    if not isinstance(outputs, list):
        raise SynthesisError(
            "outputs deve ser uma lista."
        )

    outputs_by_id = {}
    unknown_systems = []

    for output in outputs:
        if not isinstance(output, dict):
            continue

        _validate_system_output(output)

        registered_id = _identify_registered_system(output)

        if registered_id is None:
            unknown_systems.append(
                output.get("system_name")
                or output.get("system_id")
                or "UNKNOWN"
            )
            continue

        if registered_id in outputs_by_id:
            raise SynthesisError(
                "Output duplicado para o sistema "
                f"'{registered_id}'."
            )

        outputs_by_id[registered_id] = output

    sp500_output = outputs_by_id.get("sp500_cycle")
    global_output = outputs_by_id.get("global_portfolio")

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

    # Mantém integralmente a lógica macro/risco já validada.
    synthesis = build_synthesis(
        sp500_output,
        global_output
    )

    # A versão final desta interface é V2, embora build_synthesis
    # permaneça retrocompatível quando chamado diretamente.
    synthesis["synthesis_version"] = SYNTHESIS_VERSION

    systems_present = [
        system_id
        for system_id in EXPECTED_SYSTEM_IDS
        if system_id in outputs_by_id
    ]

    systems_missing = [
        system_id
        for system_id in EXPECTED_SYSTEM_IDS
        if system_id not in outputs_by_id
    ]

    system_layers = _build_system_layers(
        outputs_by_id
    )

    synthesis["systems_analyzed"] = [
        outputs_by_id[system_id].get("system_name")
        for system_id in systems_present
    ]

    synthesis["systems_registry"] = {
        "expected_count": len(EXPECTED_SYSTEM_IDS),
        "received_count": len(systems_present),
        "systems_present": systems_present,
        "systems_missing": systems_missing,
        "unknown_systems": unknown_systems,
        "all_seven_present": (
            len(systems_present) == len(EXPECTED_SYSTEM_IDS)
        ),
    }

    synthesis["layers"] = system_layers

    # Mantém a comparação SP500 x COPIA como comparação de postura.
    # Seleção e scanners NÃO são transformados em RISK_SEEKING /
    # DEFENSIVE / NEUTRAL.
    synthesis["layer_policy"] = {
        "REGIME": (
            "Contexto de ciclo/regime. "
            "Não altera sinais de outros motores."
        ),
        "GLOBAL_RISK": (
            "Contexto global de risco e restrições. "
            "Não reclassifica oportunidades."
        ),
        "ASSET_SELECTION": (
            "Seleção e sinais específicos dos mercados. "
            "Não participa como voto de postura macro."
        ),
        "OPPORTUNITY_SCANNER": (
            "Oportunidades e timing específicos. "
            "Não participa como voto de postura macro."
        ),
    }

    # Consolida alertas já existentes nos sete outputs.
    # Não cria novo score de risco.
    all_alerts = _build_all_system_alerts(
        outputs_by_id
    )

    existing_alerts = _safe_list(
        _safe_dict(synthesis.get("risk")).get("alerts")
    )

    synthesis["risk"]["alerts"] = _unique_list(
        existing_alerts + all_alerts
    )

    synthesis["evidence"] = {
        "asset_selection": (
            system_layers["ASSET_SELECTION"]
        ),
        "opportunity_scanners": (
            system_layers["OPPORTUNITY_SCANNER"]
        ),
    }

    synthesis["policy"].update({
        "seven_system_registry_enabled": True,
        "selection_systems_used_as_macro_votes": False,
        "opportunity_systems_used_as_macro_votes": False,
        "source_order_preserved": True,
        "source_signals_preserved": True,
        "new_scores_created": False,
    })

    return synthesis
