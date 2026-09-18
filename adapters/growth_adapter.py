# =============================================================================
# INVESTMENT CIO AGENT
# adapters/growth_adapter.py
#
# Adapter oficial do:
# GROWTH OPPORTUNITY ENGINE
#
# Responsabilidade:
# - receber o JSON exportado pelo motor;
# - preservar os dados e decisões produzidos pelo motor;
# - converter a saída para o schema universal do Investment CIO Agent.
#
# Este adapter NÃO:
# - recalcula fundamentos;
# - recalcula indicadores;
# - recalcula pullback;
# - recalcula Falling Score;
# - recalcula confirmações;
# - altera sinais;
# - altera ranking;
# - altera pesos;
# - executa ordens.
# =============================================================================

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


SYSTEM_ID = "growth"
SYSTEM_NAME = "Growth Opportunity Engine"

ACCEPTED_SOURCE_SYSTEMS = {
    "GROWTH_OPPORTUNITY_ENGINE",
    "Growth Opportunity Engine",
}


# =============================================================================
# UTILITÁRIOS
# =============================================================================

def _as_dict(
    value: Any,
) -> Dict[str, Any]:

    if isinstance(value, dict):
        return value

    return {}


def _as_list(
    value: Any,
) -> List[Any]:

    if isinstance(value, list):
        return value

    return []


def _safe_number(
    value: Any,
):

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(
        value,
        (int, float),
    ):
        return value

    return None


# =============================================================================
# VALIDAÇÃO DO PAYLOAD DE ORIGEM
# =============================================================================

def _validate_source(
    payload: Dict[str, Any],
) -> None:

    if not isinstance(payload, dict):

        raise ValueError(
            "Payload do Growth Opportunity Engine "
            "deve ser um objeto JSON."
        )

    source_system = payload.get(
        "source_system"
    )

    if (
        source_system
        not in ACCEPTED_SOURCE_SYSTEMS
    ):

        raise ValueError(
            "source_system inválido para "
            "Growth Opportunity Engine: "
            f"{source_system}"
        )

    strategy = payload.get(
        "strategy"
    )

    if not isinstance(
        strategy,
        list,
    ):

        raise ValueError(
            "Campo strategy ausente ou inválido."
        )

    if not strategy:

        raise ValueError(
            "Campo strategy está vazio."
        )

    signals = payload.get(
        "signals"
    )

    if not isinstance(
        signals,
        list,
    ):

        raise ValueError(
            "Campo signals ausente ou inválido."
        )


# =============================================================================
# STATUS
# =============================================================================

def _build_status(
    payload: Dict[str, Any],
) -> str:

    strategy = _as_list(
        payload.get("strategy")
    )

    signals = _as_list(
        payload.get("signals")
    )

    fundamentals = _as_list(
        payload.get("fundamentals")
    )

    warnings = []

    if not strategy:
        warnings.append(
            "strategy vazio"
        )

    if not signals:
        warnings.append(
            "signals vazio"
        )

    if not fundamentals:
        warnings.append(
            "fundamentals vazio"
        )

    if warnings:
        return "WARNING"

    return "OK"


# =============================================================================
# DATA QUALITY
# =============================================================================

def _build_data_quality(
    payload: Dict[str, Any],
) -> Dict[str, Any]:

    missing_fields = []
    warnings = []

    required_fields = [
        "source_system",
        "export_version",
        "generated_at",
        "summary",
        "fundamentals",
        "institutional",
        "signals",
        "strategy",
        "metadata",
    ]

    for field in required_fields:

        if field not in payload:

            missing_fields.append(
                field
            )

    strategy = _as_list(
        payload.get("strategy")
    )

    if not strategy:

        warnings.append(
            "Nenhuma linha disponível em strategy."
        )

    signals = _as_list(
        payload.get("signals")
    )

    if not signals:

        warnings.append(
            "Nenhuma linha disponível em signals."
        )

    return {
        "score": None,
        "missing_fields":
            missing_fields,
        "warnings":
            warnings,
    }


# =============================================================================
# RISCO
# =============================================================================

def _build_risk(
    payload: Dict[str, Any],
) -> Dict[str, Any]:

    #
    # O Growth Opportunity Engine não produz
    # um regime global de risco de carteira.
    #
    # Portanto o adapter NÃO inventa score,
    # nível ou classificação de risco.
    #

    return {
        "level": None,
        "score": None,
        "alerts": [],
    }


# =============================================================================
# MÉTRICAS
# =============================================================================

def _build_metrics(
    payload: Dict[str, Any],
) -> Dict[str, Any]:

    summary = deepcopy(
        _as_dict(
            payload.get("summary")
        )
    )

    strategy = _as_list(
        payload.get("strategy")
    )

    signals = _as_list(
        payload.get("signals")
    )

    fundamentals = _as_list(
        payload.get("fundamentals")
    )

    institutional = _as_list(
        payload.get("institutional")
    )

    market_data = _as_list(
        payload.get("market_data")
    )

    return {
        "market_tickers":
            len(market_data),

        "fundamentals_count":
            len(fundamentals),

        "institutional_count":
            len(institutional),

        "signals_count":
            len(signals),

        "strategy_count":
            len(strategy),

        "source_summary":
            summary,
    }


# =============================================================================
# OPORTUNIDADES
# =============================================================================

def _build_opportunities(
    payload: Dict[str, Any],
) -> List[Dict[str, Any]]:

    strategy = deepcopy(
        _as_list(
            payload.get("strategy")
        )
    )

    opportunities = []

    #
    # IMPORTANTE:
    #
    # Não filtrar AGUARDAR.
    # Não reordenar.
    #
    # A ordem existente em strategy é a ordem
    # produzida pelo rank_opportunities()
    # do próprio motor.
    #

    for source_row in strategy:

        if not isinstance(
            source_row,
            dict,
        ):
            continue

        row = deepcopy(
            source_row
        )

        ticker = row.get(
            "ticker"
        )

        signal = row.get(
            "signal"
        )

        opportunity = {
            "ticker":
                ticker,

            "signal":
                signal,

            "source_rank":
                len(opportunities) + 1,

            "pullback":
                _safe_number(
                    row.get(
                        "pullback"
                    )
                ),

            "pullback_zone":
                row.get(
                    "pullback_zone"
                ),

            "falling_score":
                _safe_number(
                    row.get(
                        "falling_score"
                    )
                ),

            "falling_risk":
                row.get(
                    "falling_risk"
                ),

            "confirmations_total":
                _safe_number(
                    row.get(
                        "confirmations_total"
                    )
                ),

            "institutional_score":
                _safe_number(
                    row.get(
                        "institutional_score"
                    )
                ),

            "fundamentals_ok":
                row.get(
                    "fundamentals_ok"
                ),

            "growth_class":
                row.get(
                    "growth_class"
                ),

            "initial_weight":
                _safe_number(
                    row.get(
                        "initial_weight"
                    )
                ),

            "confirmation_weight":
                _safe_number(
                    row.get(
                        "confirmation_weight"
                    )
                ),

            "effective_weight":
                _safe_number(
                    row.get(
                        "effective_weight"
                    )
                ),

            "current_cash_weight":
                _safe_number(
                    row.get(
                        "current_cash_weight"
                    )
                ),

            "needs_confirmation":
                row.get(
                    "needs_confirmation"
                ),

            "confirmation_executed":
                row.get(
                    "confirmation_executed"
                ),

            "reason":
                row.get(
                    "reason"
                ),

            #
            # Preserva integralmente a linha
            # original produzida pelo motor.
            #
            "source_data":
                row,
        }

        opportunities.append(
            opportunity
        )

    return opportunities


# =============================================================================
# DECISÃO UNIVERSAL
# =============================================================================

def _build_decision(
    payload: Dict[str, Any],
) -> Dict[str, Any]:

    summary = _as_dict(
        payload.get("summary")
    )

    signal_counts = _as_dict(
        summary.get(
            "signal_counts"
        )
    )

    strong = signal_counts.get(
        "ENTRADA_FORTE",
        0,
    )

    partial = signal_counts.get(
        "ENTRADA_PARCIAL",
        0,
    )

    wait = signal_counts.get(
        "AGUARDAR",
        0,
    )

    #
    # O sinal universal descreve o TIPO
    # de informação produzida pelo motor.
    #
    # Não transforma várias oportunidades
    # em uma recomendação global de compra.
    #

    return {
        "signal":
            "OPPORTUNITY_SET_WITH_ENTRY_SIGNALS",

        "confidence":
            None,

        "summary":
            (
                "Growth Opportunity Engine: "
                f"{strong} ENTRADA_FORTE, "
                f"{partial} ENTRADA_PARCIAL, "
                f"{wait} AGUARDAR."
            ),
    }


# =============================================================================
# AUDITORIA
# =============================================================================

def _build_audit(
    payload: Dict[str, Any],
) -> Dict[str, Any]:

    metadata = deepcopy(
        _as_dict(
            payload.get("metadata")
        )
    )

    export_policy = deepcopy(
        _as_dict(
            metadata.get(
                "export_policy"
            )
        )
    )

    return {
        "source_system":
            payload.get(
                "source_system"
            ),

        "source_export_version":
            payload.get(
                "export_version"
            ),

        "adapter":
            "growth_adapter",

        "adapter_version":
            "1.0",

        "preserves_source_ranking":
            True,

        "preserves_source_signals":
            True,

        "preserves_waiting_opportunities":
            True,

        "recalculates_indicators":
            False,

        "recalculates_fundamentals":
            False,

        "recalculates_signals":
            False,

        "recalculates_ranking":
            False,

        "recalculates_weights":
            False,

        "executes_broker_orders":
            False,

        "source_export_policy":
            export_policy,
    }


# =============================================================================
# ADAPTER PRINCIPAL
# =============================================================================

def adapt_growth_output(
    payload: Dict[str, Any],
) -> Dict[str, Any]:

    _validate_source(
        payload
    )

    status = _build_status(
        payload
    )

    opportunities = (
        _build_opportunities(
            payload
        )
    )

    result = {
        "schema_version":
            "1.0",

        "system_id":
            SYSTEM_ID,

        "system_name":
            SYSTEM_NAME,

        "generated_at":
            payload.get(
                "generated_at"
            ),

        "status":
            status,

        "decision":
            _build_decision(
                payload
            ),

        "metrics":
            _build_metrics(
                payload
            ),

        "risk":
            _build_risk(
                payload
            ),

        "data_quality":
            _build_data_quality(
                payload
            ),

        "opportunities":
            opportunities,

        "audit":
            _build_audit(
                payload
            ),

        "metadata": {
            "source_system":
                payload.get(
                    "source_system"
                ),

            "source_export_version":
                payload.get(
                    "export_version"
                ),

            "source_metadata":
                deepcopy(
                    _as_dict(
                        payload.get(
                            "metadata"
                        )
                    )
                ),

            #
            # Preservação adicional dos blocos
            # de origem para auditoria posterior.
            #
            "source_fundamentals":
                deepcopy(
                    _as_list(
                        payload.get(
                            "fundamentals"
                        )
                    )
                ),

            "source_institutional":
                deepcopy(
                    _as_list(
                        payload.get(
                            "institutional"
                        )
                    )
                ),

            "source_signals":
                deepcopy(
                    _as_list(
                        payload.get(
                            "signals"
                        )
                    )
                ),

            "source_market_data":
                deepcopy(
                    _as_list(
                        payload.get(
                            "market_data"
                        )
                    )
                ),
        },
    }

    return result


# =============================================================================
# INTERFACE GENÉRICA
# =============================================================================

def adapt(
    payload: Dict[str, Any],
) -> Dict[str, Any]:

    return adapt_growth_output(
        payload
    )
