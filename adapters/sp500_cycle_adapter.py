# ============================================================
# INVESTMENT CIO AGENT
# adapters/sp500_cycle_adapter.py
# ============================================================
#
# Adaptador oficial:
# SP500_CYCLE_ATLAS -> INVESTMENT CIO AGENT
#
# O adaptador NÃO recalcula indicadores.
# Apenas traduz a saída real do Atlas para o contrato universal.
#
# ============================================================

from datetime import datetime, timezone


SYSTEM_ID = "sp500_cycle"
SYSTEM_NAME = "SP500_CYCLE_ATLAS"
SCHEMA_VERSION = "1.0"
ADAPTER_VERSION = "1.1"


def _safe_float(value):

    if value is None:
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def _normalize_confidence(value):

    value = _safe_float(value)

    if value is None:
        return None

    if value > 1:
        value = value / 100

    return max(
        0.0,
        min(1.0, value)
    )


def _extract_audit_warnings(ai_audit):

    warnings = ai_audit.get(
        "warnings"
    )

    if warnings is None:
        return []

    if isinstance(warnings, list):
        return [
            str(item)
            for item in warnings
        ]

    return [
        str(warnings)
    ]


def build_sp500_agent_output(payload):

    # ========================================================
    # 1. VALIDAÇÃO DA SAÍDA BRUTA
    # ========================================================

    if not isinstance(payload, dict):

        raise TypeError(
            "A saída bruta do SP500 Cycle Atlas "
            "deve ser um dicionário."
        )

    source_system = payload.get(
        "source_system"
    )

    if source_system != SYSTEM_NAME:

        raise ValueError(
            "source_system inválido para o "
            "SP500 Cycle Atlas."
        )

    state = payload.get(
        "current_state"
    )

    ai_audit = payload.get(
        "ai_audit"
    )

    if not isinstance(state, dict):

        raise ValueError(
            "current_state ausente ou inválido "
            "na saída do Atlas."
        )

    if not isinstance(ai_audit, dict):

        ai_audit = {}

    # ========================================================
    # 2. IDENTIDADE TEMPORAL
    # ========================================================

    generated_at = payload.get(
        "generated_at"
    )

    if not generated_at:

        generated_at = datetime.now(
            timezone.utc
        ).isoformat()

    # ========================================================
    # 3. DECISÃO ORIGINAL DO ATLAS
    # ========================================================

    existing_position = state.get(
        "existing_position"
    )

    equity_allocation = _safe_float(
        state.get(
            "new_contribution_equity"
        )
    )

    reserve_allocation = _safe_float(
        state.get(
            "new_contribution_reserve"
        )
    )

    operational_regime = state.get(
        "operational_regime"
    )

    signal = (
        existing_position
        or operational_regime
        or "UNDEFINED"
    )

    # ========================================================
    # 4. AUDITORIA INDEPENDENTE
    # ========================================================

    audit_status = ai_audit.get(
        "audit_status"
    )

    engine_consistency_score = (
        _safe_float(
            ai_audit.get(
                "engine_consistency_score"
            )
        )
    )

    audit_data_quality_score = (
        _safe_float(
            ai_audit.get(
                "data_quality_score"
            )
        )
    )

    ai_dissent = ai_audit.get(
        "ai_dissent"
    )

    # Usamos a consistência da auditoria como medida
    # informacional de confiança do output.
    #
    # Isso NÃO altera a decisão do Atlas.
    confidence = _normalize_confidence(
        engine_consistency_score
    )

    # ========================================================
    # 5. QUALIDADE DOS DADOS
    # ========================================================

    critical_fields = [
        "date",
        "sp500",
        "drawdown",
        "cape",
        "operational_regime",
        "existing_position",
        "new_contribution_equity",
        "new_contribution_reserve",
    ]

    missing_fields = [
        field
        for field in critical_fields
        if state.get(field) is None
    ]

    warnings = []

    if missing_fields:

        warnings.append(
            "Campos críticos ausentes na "
            "saída do SP500 Cycle Atlas."
        )

    warnings.extend(
        _extract_audit_warnings(
            ai_audit
        )
    )

    if missing_fields:

        status = "WARNING"

    elif audit_status in {
        "CONFIRMED_WITH_WARNINGS",
        "WARNING",
        "DATA_INSUFFICIENT",
    }:

        status = "WARNING"

    elif ai_dissent is True:

        status = "WARNING"

    else:

        status = "OK"

    # ========================================================
    # 6. CONTRATO UNIVERSAL
    # ========================================================

    output = {

        "schema_version": SCHEMA_VERSION,

        "system_id": SYSTEM_ID,

        "system_name": SYSTEM_NAME,

        "generated_at": generated_at,

        "status": status,

        # ====================================================
        # DECISÃO
        # ====================================================

        "decision": {

            "signal": str(
                signal
            ),

            "confidence": confidence,

            "summary": (
                "Decisão quantitativa produzida pelo "
                "SP500 Cycle Atlas."
            ),

            "operational_regime": (
                operational_regime
            ),

            "existing_position": (
                existing_position
            ),

            "new_contribution_equity": (
                equity_allocation
            ),

            "new_contribution_reserve": (
                reserve_allocation
            ),
        },

        # ====================================================
        # MÉTRICAS
        # ====================================================

        "metrics": {

            "date": state.get(
                "date"
            ),

            "sp500": _safe_float(
                state.get(
                    "sp500"
                )
            ),

            "drawdown": _safe_float(
                state.get(
                    "drawdown"
                )
            ),

            "return_12m": _safe_float(
                state.get(
                    "return_12m"
                )
            ),

            "cape": _safe_float(
                state.get(
                    "cape"
                )
            ),

            "cape_percentile": (
                _safe_float(
                    state.get(
                        "cape_percentile"
                    )
                )
            ),

            "bull_start_date": state.get(
                "bull_start_date"
            ),

            "bull_start_price": (
                _safe_float(
                    state.get(
                        "bull_start_price"
                    )
                )
            ),

            "bull_age_years": (
                _safe_float(
                    state.get(
                        "bull_age_years"
                    )
                )
            ),

            "bull_return": _safe_float(
                state.get(
                    "bull_return"
                )
            ),

            "fed_funds": _safe_float(
                state.get(
                    "fed_funds"
                )
            ),

            "fed_change_12m": (
                _safe_float(
                    state.get(
                        "fed_change_12m"
                    )
                )
            ),

            "yield_curve_10y_2y": (
                _safe_float(
                    state.get(
                        "yield_curve_10y_2y"
                    )
                )
            ),

            "inflation_yoy": (
                _safe_float(
                    state.get(
                        "inflation_yoy"
                    )
                )
            ),

            "inflation_change_6m": (
                _safe_float(
                    state.get(
                        "inflation_change_6m"
                    )
                )
            ),

            "unemployment": _safe_float(
                state.get(
                    "unemployment"
                )
            ),

            "sahm_indicator": (
                _safe_float(
                    state.get(
                        "sahm_indicator"
                    )
                )
            ),

            "industrial_production_yoy": (
                _safe_float(
                    state.get(
                        "industrial_production_yoy"
                    )
                )
            ),

            "valuation_regime": state.get(
                "valuation_regime"
            ),

            "momentum_regime": state.get(
                "momentum_regime"
            ),

            "drawdown_regime": state.get(
                "drawdown_regime"
            ),

            "labor_regime": state.get(
                "labor_regime"
            ),

            "industrial_regime": state.get(
                "industrial_regime"
            ),

            "inflation_regime": state.get(
                "inflation_regime"
            ),

            "monetary_regime": state.get(
                "monetary_regime"
            ),

            "curve_regime": state.get(
                "curve_regime"
            ),

            "market_regime": state.get(
                "market_regime"
            ),

            "cycle_phase": state.get(
                "cycle_phase"
            ),

            "structural_risk": state.get(
                "structural_risk"
            ),

            "top_timing": state.get(
                "top_timing"
            ),

            "macro_deterioration_count": (
                _safe_float(
                    state.get(
                        "macro_deterioration_count"
                    )
                )
            ),

            "market_deterioration_count": (
                _safe_float(
                    state.get(
                        "market_deterioration_count"
                    )
                )
            ),

            "operational_regime": (
                operational_regime
            ),
        },

        # ====================================================
        # RISCO
        # ====================================================

        "risk": {

            "level": state.get(
                "structural_risk"
            ),

            "score": None,

            "alerts": warnings,
        },

        # ====================================================
        # QUALIDADE DOS DADOS
        # ====================================================

        "data_quality": {

            "score": (
                audit_data_quality_score
            ),

            "missing_fields": (
                missing_fields
            ),

            "warnings": warnings,
        },

        # ====================================================
        # POSIÇÕES / OPORTUNIDADES
        # ====================================================

        "positions": [],

        "opportunities": [],

        # ====================================================
        # AUDITORIA
        # ====================================================

        "audit": {

            "status": (
                audit_status
            ),

            "engine_consistency_score": (
                engine_consistency_score
            ),

            "data_quality_score": (
                audit_data_quality_score
            ),

            "ai_dissent": (
                ai_dissent
            ),

            "regime_audit": ai_audit.get(
                "regime_audit"
            ),

            "data_integrity": ai_audit.get(
                "data_integrity"
            ),

            "rule_consistency": ai_audit.get(
                "rule_consistency"
            ),

            "policy_consistency": ai_audit.get(
                "policy_consistency"
            ),

            "reserve_consistency": ai_audit.get(
                "reserve_consistency"
            ),

            "cross_evidence": ai_audit.get(
                "cross_evidence"
            ),

            "strengths": ai_audit.get(
                "strengths"
            ),

            "manual_review_points": (
                ai_audit.get(
                    "manual_review_points"
                )
            ),

            "final_opinion": ai_audit.get(
                "final_opinion"
            ),
        },

        # ====================================================
        # METADADOS
        # ====================================================

        "metadata": {

            "source": SYSTEM_NAME,

            "source_export_version": (
                payload.get(
                    "export_version"
                )
            ),

            "adapter": (
                "sp500_cycle_adapter"
            ),

            "adapter_version": (
                ADAPTER_VERSION
            ),

            "reserve_stage": state.get(
                "reserve_stage"
            ),

            "reserve_stage_fraction": (
                _safe_float(
                    state.get(
                        "reserve_stage_fraction"
                    )
                )
            ),

            "reserve_cumulative_fraction": (
                _safe_float(
                    state.get(
                        "reserve_cumulative_fraction"
                    )
                )
            ),

            "reserve_deployment_status": (
                state.get(
                    "reserve_deployment_status"
                )
            ),

            "reserve_pending": state.get(
                "reserve_pending"
            ),

            "reserve_blocked_by_regime": (
                state.get(
                    "reserve_blocked_by_regime"
                )
            ),
        },
    }

    return output
