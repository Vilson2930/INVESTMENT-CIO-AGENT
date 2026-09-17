from datetime import datetime, timezone


SYSTEM_ID = "global_portfolio"
SYSTEM_NAME = "COPIAULTIMOROB"
SOURCE_SYSTEM = "COPIAULTIMOROB"
ADAPTER_VERSION = "1.0"


def _to_float(value, default=None):
    """
    Converte um valor para float com segurança.
    """
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value, default=None):
    """
    Converte valores comuns para booleano.
    """
    if isinstance(value, bool):
        return value

    if value is None:
        return default

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {"true", "1", "yes", "sim"}:
            return True

        if normalized in {"false", "0", "no", "nao", "não"}:
            return False

    return default


def _normalize_confidence(value):
    """
    Converte confidence score para escala universal 0.0 - 1.0.

    Exemplos:
        66.40 -> 0.664
        0.92  -> 0.92
    """
    number = _to_float(value)

    if number is None:
        return None

    if number > 1:
        number = number / 100.0

    return max(0.0, min(number, 1.0))


def _get_section(payload, *names):
    """
    Procura uma seção usando nomes alternativos.
    """
    for name in names:
        section = payload.get(name)

        if isinstance(section, dict):
            return section

    return {}


def _first_value(*values):
    """
    Retorna o primeiro valor não vazio.
    """
    for value in values:
        if value is not None and value != "":
            return value

    return None


def _extract_warnings(payload):
    """
    Consolida alertas importantes do COPIAULTIMOROB.
    """
    warnings = []

    survival = _get_section(
        payload,
        "survival",
        "survival_audit",
        "risk",
    )

    stress = _get_section(
        payload,
        "stress",
        "stress_summary",
    )

    risk_budget = _get_section(
        payload,
        "risk_budget",
        "risk_budget_summary",
    )

    liquidity = _get_section(
        payload,
        "liquidity",
        "liquidity_summary",
    )

    counterparty = _get_section(
        payload,
        "counterparty",
        "counterparty_summary",
    )

    governance = _get_section(
        payload,
        "governance",
        "risk_committee",
    )

    survival_status = _first_value(
        survival.get("survival_status"),
        payload.get("survival_status"),
    )

    ruin_risk = _first_value(
        survival.get("ruin_risk"),
        payload.get("ruin_risk"),
    )

    kill_switch = _first_value(
        survival.get("survival_kill_switch"),
        payload.get("survival_kill_switch"),
        payload.get("kill_switch"),
    )

    stress_level = _first_value(
        stress.get("stress_level"),
        payload.get("stress_level"),
    )

    forced_selling = _first_value(
        stress.get("forced_selling_any"),
        stress.get("forced_selling"),
        payload.get("forced_selling"),
    )

    risk_budget_level = _first_value(
        risk_budget.get("risk_budget_level"),
        payload.get("risk_budget_level"),
    )

    liquidity_level = _first_value(
        liquidity.get("liquidity_level"),
        payload.get("liquidity_level"),
    )

    counterparty_level = _first_value(
        counterparty.get("counterparty_level"),
        payload.get("counterparty_level"),
    )

    final_verdict = _first_value(
        governance.get("final_verdict"),
        payload.get("final_verdict"),
    )

    if survival_status and str(survival_status).upper() not in {
        "APROVADO",
        "OK",
        "ROBUSTO",
    }:
        warnings.append(
            f"Survival status: {survival_status}"
        )

    if ruin_risk and str(ruin_risk).upper() in {
        "ALTO",
        "CRITICO",
        "CRÍTICO",
    }:
        warnings.append(
            f"Risco de ruína: {ruin_risk}"
        )

    if _to_bool(kill_switch, False):
        warnings.append(
            "Survival Kill Switch ativo."
        )

    if stress_level and str(stress_level).upper() in {
        "ALTO",
        "CRITICO",
        "CRÍTICO",
    }:
        warnings.append(
            f"Stress level: {stress_level}"
        )

    if _to_bool(forced_selling, False):
        warnings.append(
            "Stress engine identificou forced selling."
        )

    if risk_budget_level and str(risk_budget_level).upper() in {
        "ALTO",
        "CRITICO",
        "CRÍTICO",
    }:
        warnings.append(
            f"Risk Budget: {risk_budget_level}"
        )

    if liquidity_level and str(liquidity_level).upper() in {
        "FRAGIL",
        "FRÁGIL",
        "CRITICO",
        "CRÍTICO",
    }:
        warnings.append(
            f"Liquidez: {liquidity_level}"
        )

    if counterparty_level and str(counterparty_level).upper() in {
        "FRAGIL",
        "FRÁGIL",
        "CRITICO",
        "CRÍTICO",
    }:
        warnings.append(
            f"Contraparte: {counterparty_level}"
        )

    if final_verdict and str(final_verdict).upper() not in {
        "APROVADO",
        "OK",
        "NORMAL",
    }:
        warnings.append(
            f"Governança: {final_verdict}"
        )

    return warnings


def _determine_status(payload, warnings):
    """
    Determina o status técnico do output universal.

    IMPORTANTE:
    WARNING não altera a decisão original do robô.
    Apenas informa ao CIO Agent que existem alertas relevantes.
    """
    governance = _get_section(
        payload,
        "governance",
        "risk_committee",
    )

    final_verdict = _first_value(
        governance.get("final_verdict"),
        payload.get("final_verdict"),
    )

    kill_switch = _first_value(
        payload.get("kill_switch"),
        payload.get("survival_kill_switch"),
    )

    if _to_bool(kill_switch, False):
        return "WARNING"

    if final_verdict:
        verdict_upper = str(final_verdict).upper()

        if any(
            term in verdict_upper
            for term in (
                "REPROVADO",
                "BLOQUEAR",
                "CRITICO",
                "CRÍTICO",
            )
        ):
            return "WARNING"

    if warnings:
        return "WARNING"

    return "OK"


def build_copiaultimorob_agent_output(payload):
    """
    Converte o output bruto do COPIAULTIMOROB
    para o contrato universal do INVESTMENT CIO AGENT.

    O adaptador NÃO recalcula a estratégia.
    O adaptador NÃO altera decisões.
    O adaptador apenas traduz e organiza os dados.
    """

    if not isinstance(payload, dict):
        raise TypeError(
            "Payload do COPIAULTIMOROB deve ser um dicionário."
        )

    source_system = payload.get("source_system")

    if source_system != SOURCE_SYSTEM:
        raise ValueError(
            "Sistema de origem inválido. "
            f"Esperado: {SOURCE_SYSTEM}. "
            f"Recebido: {source_system}"
        )

    generated_at = payload.get("generated_at")

    if not generated_at:
        generated_at = datetime.now(
            timezone.utc
        ).isoformat()

    macro = _get_section(
        payload,
        "macro",
        "macro_state",
        "macro_summary",
    )

    portfolio = _get_section(
        payload,
        "portfolio",
        "portfolio_summary",
    )

    allocation = _get_section(
        payload,
        "allocation",
        "allocation_advisor",
        "allocation_summary",
    )

    survival = _get_section(
        payload,
        "survival",
        "survival_audit",
        "risk",
    )

    stress = _get_section(
        payload,
        "stress",
        "stress_summary",
    )

    risk_budget = _get_section(
        payload,
        "risk_budget",
        "risk_budget_summary",
    )

    liquidity = _get_section(
        payload,
        "liquidity",
        "liquidity_summary",
    )

    counterparty = _get_section(
        payload,
        "counterparty",
        "counterparty_summary",
    )

    governance = _get_section(
        payload,
        "governance",
        "risk_committee",
    )

    ai_audit = _get_section(
        payload,
        "ai_audit",
        "ai_audit_summary",
    )

    nvidia_audit = _get_section(
        payload,
        "openai_audit",
        "nvidia_audit",
        "openai_audit_summary",
    )

    regime = _first_value(
        macro.get("regime"),
        payload.get("regime"),
        payload.get("macro_regime"),
    )

    operational_signal = _first_value(
        macro.get("sinal_operacional"),
        macro.get("signal"),
        payload.get("sinal_operacional"),
        payload.get("signal"),
        "UNDEFINED",
    )

    confidence_raw = _first_value(
        macro.get("confidence_score"),
        payload.get("confidence_score"),
    )

    confidence = _normalize_confidence(
        confidence_raw
    )

    final_verdict = _first_value(
        governance.get("final_verdict"),
        payload.get("final_verdict"),
    )

    committee_action = _first_value(
        governance.get("committee_action"),
        payload.get("committee_action"),
    )

    integrated_risk_level = _first_value(
        governance.get("integrated_risk_level"),
        payload.get("integrated_risk_level"),
    )

    warnings = _extract_warnings(payload)

    status = _determine_status(
        payload,
        warnings,
    )

    survival_status = _first_value(
        survival.get("survival_status"),
        payload.get("survival_status"),
    )

    ruin_risk = _first_value(
        survival.get("ruin_risk"),
        payload.get("ruin_risk"),
    )

    survival_kill_switch = _first_value(
        survival.get("survival_kill_switch"),
        payload.get("survival_kill_switch"),
        payload.get("kill_switch"),
    )

    stress_level = _first_value(
        stress.get("stress_level"),
        payload.get("stress_level"),
    )

    stress_score = _first_value(
        stress.get("stress_score"),
        payload.get("stress_score"),
    )

    risk_budget_level = _first_value(
        risk_budget.get("risk_budget_level"),
        payload.get("risk_budget_level"),
    )

    risk_budget_score = _first_value(
        risk_budget.get("risk_budget_score"),
        payload.get("risk_budget_score"),
    )

    liquidity_level = _first_value(
        liquidity.get("liquidity_level"),
        payload.get("liquidity_level"),
    )

    liquidity_score = _first_value(
        liquidity.get("liquidity_score"),
        payload.get("liquidity_score"),
    )

    counterparty_level = _first_value(
        counterparty.get("counterparty_level"),
        payload.get("counterparty_level"),
    )

    counterparty_score = _first_value(
        counterparty.get("counterparty_score"),
        payload.get("counterparty_score"),
    )

    risk_level = _first_value(
        integrated_risk_level,
        stress_level,
        risk_budget_level,
        ruin_risk,
    )

    data_quality_score = _first_value(
        nvidia_audit.get("data_quality_score"),
        ai_audit.get("data_quality_score"),
    )

    output = {
        "schema_version": "1.0",
        "system_id": SYSTEM_ID,
        "system_name": SYSTEM_NAME,
        "generated_at": generated_at,
        "status": status,

        "decision": {
            "signal": str(operational_signal),
            "confidence": confidence,
            "summary": (
                f"Regime macro: {regime}; "
                f"sinal operacional: {operational_signal}; "
                f"veredito de governança: {final_verdict}; "
                f"ação do comitê: {committee_action}."
            ),
        },

        "metrics": {
            "macro_regime": regime,
            "macro_signal": operational_signal,
            "macro_conviction": _to_float(
                _first_value(
                    macro.get("macro_conviction"),
                    payload.get("macro_conviction"),
                )
            ),
            "macro_momentum": _to_float(
                _first_value(
                    macro.get("macro_momentum"),
                    payload.get("macro_momentum"),
                )
            ),
            "confidence_score_raw": _to_float(
                confidence_raw
            ),

            "portfolio_total_value": _to_float(
                _first_value(
                    portfolio.get("total_value"),
                    payload.get("total_value"),
                )
            ),

            "gross_turnover_final": _to_float(
                _first_value(
                    portfolio.get("gross_turnover_final"),
                    payload.get("gross_turnover_final"),
                )
            ),

            "turnover_status": _first_value(
                portfolio.get("turnover_status"),
                payload.get("turnover_status"),
            ),

            "allocation_alignment_score": _to_float(
                _first_value(
                    allocation.get(
                        "allocation_alignment_score"
                    ),
                    payload.get(
                        "allocation_alignment_score"
                    ),
                )
            ),

            "allocation_alignment_level": _first_value(
                allocation.get(
                    "allocation_alignment_level"
                ),
                payload.get(
                    "allocation_alignment_level"
                ),
            ),

            "total_model_drift_pct": _to_float(
                _first_value(
                    allocation.get(
                        "total_model_drift_pct"
                    ),
                    payload.get(
                        "total_model_drift_pct"
                    ),
                )
            ),

            "top_gap_asset": _first_value(
                allocation.get("top_gap_asset"),
                payload.get("top_gap_asset"),
            ),

            "top_gap_abs_pct": _to_float(
                _first_value(
                    allocation.get("top_gap_abs_pct"),
                    payload.get("top_gap_abs_pct"),
                )
            ),

            "survival_status": survival_status,
            "ruin_risk": ruin_risk,
            "survival_kill_switch": _to_bool(
                survival_kill_switch
            ),

            "stress_level": stress_level,
            "stress_score": _to_float(
                stress_score
            ),

            "max_drawdown_pct": _to_float(
                _first_value(
                    stress.get("max_drawdown_pct"),
                    payload.get("max_drawdown_pct"),
                )
            ),

            "forced_selling": _to_bool(
                _first_value(
                    stress.get("forced_selling_any"),
                    stress.get("forced_selling"),
                    payload.get("forced_selling"),
                )
            ),

            "risk_budget_level": risk_budget_level,

            "risk_budget_score": _to_float(
                risk_budget_score
            ),

            "top_risk_asset": _first_value(
                risk_budget.get("top_risk_asset"),
                payload.get("top_risk_asset"),
            ),

            "max_risk_contribution_pct": _to_float(
                _first_value(
                    risk_budget.get(
                        "max_risk_contribution_pct"
                    ),
                    payload.get(
                        "max_risk_contribution_pct"
                    ),
                )
            ),

            "liquidity_level": liquidity_level,

            "liquidity_score": _to_float(
                liquidity_score
            ),

            "aggregate_haircut_pct": _to_float(
                _first_value(
                    liquidity.get(
                        "aggregate_haircut_pct"
                    ),
                    liquidity.get(
                        "aggregate_operational_haircut_pct"
                    ),
                    payload.get(
                        "aggregate_haircut_pct"
                    ),
                )
            ),

            "counterparty_level": counterparty_level,

            "counterparty_score": _to_float(
                counterparty_score
            ),

            "largest_counterparty": _first_value(
                counterparty.get(
                    "largest_counterparty"
                ),
                payload.get(
                    "largest_counterparty"
                ),
            ),

            "integrated_risk_level": integrated_risk_level,
            "committee_action": committee_action,
            "final_verdict": final_verdict,
        },

        "risk": {
            "level": (
                str(risk_level)
                if risk_level is not None
                else None
            ),
            "score": _to_float(
                risk_budget_score
            ),
            "alerts": warnings,
        },

        "data_quality": {
            "score": _to_float(
                data_quality_score
            ),
            "missing_fields": [],
            "warnings": warnings,
        },

        "positions": [],

        "opportunities": [],

        "audit": {
            "deterministic_audit_status": _first_value(
                ai_audit.get("ai_audit_status"),
                payload.get("ai_audit_status"),
            ),

            "deterministic_audit_score": _to_float(
                _first_value(
                    ai_audit.get("ai_audit_score"),
                    payload.get("ai_audit_score"),
                )
            ),

            "deterministic_root_cause": _first_value(
                ai_audit.get("root_cause"),
                payload.get("ai_root_cause"),
            ),

            "nvidia_status": _first_value(
                nvidia_audit.get(
                    "openai_audit_status"
                ),
                nvidia_audit.get("status"),
                payload.get("nvidia_status"),
            ),

            "nvidia_verdict": _first_value(
                nvidia_audit.get(
                    "audit_verdict"
                ),
                payload.get(
                    "nvidia_verdict"
                ),
            ),

            "nvidia_score": _to_float(
                _first_value(
                    nvidia_audit.get(
                        "audit_score"
                    ),
                    payload.get(
                        "nvidia_score"
                    ),
                )
            ),

            "nvidia_confidence": _to_float(
                _first_value(
                    nvidia_audit.get(
                        "audit_confidence"
                    ),
                    payload.get(
                        "nvidia_confidence"
                    ),
                )
            ),

            "nvidia_severity": _first_value(
                nvidia_audit.get("severity"),
                payload.get("nvidia_severity"),
            ),

            "nvidia_root_cause": _first_value(
                nvidia_audit.get("root_cause"),
                payload.get(
                    "nvidia_root_cause"
                ),
            ),

            "nvidia_final_opinion": _first_value(
                nvidia_audit.get(
                    "final_opinion"
                ),
                payload.get(
                    "nvidia_final_opinion"
                ),
            ),
        },

        "metadata": {
            "source_system": SOURCE_SYSTEM,
            "source_export_version": payload.get(
                "export_version"
            ),
            "adapter_version": ADAPTER_VERSION,

            "macro_regime": regime,
            "operational_signal": operational_signal,

            "survival_status": survival_status,
            "survival_kill_switch": _to_bool(
                survival_kill_switch
            ),

            "governance_final_verdict": final_verdict,
            "committee_action": committee_action,

            "adapter_policy": (
                "TRANSLATION_ONLY_NO_RECALCULATION"
            ),
        },
    }

    return output
