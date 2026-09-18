# ============================================================
# INVESTMENT CIO AGENT
# adapters/ai_infrastructure_adapter.py
# ============================================================
#
# Adapter do:
# AI_INFRASTRUCTURE_SCANNER
#
# RESPONSABILIDADE:
# Traduzir o JSON bruto produzido pelo scanner para o schema
# universal do Investment CIO Agent.
#
# PRINCÍPIOS:
# - NÃO recalcula indicadores;
# - NÃO recalcula Institutional Score;
# - NÃO recalcula Technical Entry Score;
# - NÃO recalcula Entry Timing Score;
# - NÃO recalcula Final Score;
# - NÃO altera ranking;
# - NÃO altera sinais;
# - NÃO transforma pré-entrada em compra;
# - NÃO remove ativos;
# - NÃO cria recomendação global de investimento;
# - NÃO executa operações.
#
# ============================================================

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any


# ============================================================
# IDENTIDADE
# ============================================================

SYSTEM_ID = "ai_infrastructure"

SYSTEM_NAME = "AI Infrastructure Scanner"

EXPECTED_SOURCE_SYSTEMS = {
    "AI_INFRASTRUCTURE_SCANNER",
    "AI Infrastructure Scanner",
}


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _as_dict(
    value: Any,
) -> dict[str, Any]:
    """
    Retorna dicionário ou objeto vazio.
    """

    if isinstance(value, dict):
        return value

    return {}


def _as_list(
    value: Any,
) -> list[Any]:
    """
    Retorna lista ou lista vazia.
    """

    if isinstance(value, list):
        return value

    return []


def _safe_float(
    value: Any,
) -> float | None:
    """
    Converte número para float sem criar valor artificial.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def _safe_int(
    value: Any,
) -> int | None:
    """
    Converte número para inteiro quando possível.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    try:
        return int(value)

    except (TypeError, ValueError):
        return None


def _safe_bool(
    value: Any,
) -> bool | None:
    """
    Preserva booleanos.

    Não converte strings arbitrariamente.
    """

    if isinstance(value, bool):
        return value

    return None


def _clean_string(
    value: Any,
) -> str | None:
    """
    Normaliza somente espaços externos.

    Não altera o conteúdo semântico.
    """

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    return text


def _unique_strings(
    values: list[Any],
) -> list[str]:
    """
    Remove duplicatas preservando a ordem.
    """

    result: list[str] = []

    for value in values:

        text = _clean_string(value)

        if (
            text is not None
            and text not in result
        ):
            result.append(text)

    return result


def _generated_at(
    raw: dict[str, Any],
) -> str:
    """
    Preserva generated_at da fonte.

    Usa horário atual somente se a fonte não o fornecer.
    """

    value = _clean_string(
        raw.get("generated_at")
    )

    if value is not None:
        return value

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# VALIDAÇÃO DA FONTE
# ============================================================

def _validate_source(
    raw: dict[str, Any],
) -> None:
    """
    Verifica se o JSON pertence ao motor esperado.
    """

    if not isinstance(raw, dict):
        raise TypeError(
            "O output bruto deve ser um dicionário."
        )

    source_system = _clean_string(
        raw.get("source_system")
    )

    if source_system not in EXPECTED_SOURCE_SYSTEMS:
        raise ValueError(
            "Fonte inválida para "
            "AI Infrastructure Adapter: "
            f"{source_system!r}"
        )

    executive_ranking = raw.get(
        "executive_ranking"
    )

    if not isinstance(
        executive_ranking,
        list,
    ):
        raise ValueError(
            "'executive_ranking' ausente "
            "ou inválido."
        )


# ============================================================
# DISTRIBUIÇÕES
# ============================================================

def _count_field(
    records: list[Any],
    field: str,
) -> dict[str, int]:
    """
    Conta valores existentes.

    É somente agregação descritiva.
    """

    counter: Counter[str] = Counter()

    for record in records:

        if not isinstance(record, dict):
            continue

        value = _clean_string(
            record.get(field)
        )

        if value is not None:
            counter[value] += 1

    return dict(counter)


# ============================================================
# EXTRAÇÃO DE TICKERS
# ============================================================

def _extract_tickers(
    records: list[Any],
) -> list[str]:
    """
    Extrai tickers preservando ordem.
    """

    tickers: list[str] = []

    for record in records:

        if not isinstance(record, dict):
            continue

        ticker = _clean_string(
            record.get("ticker")
        )

        if (
            ticker is not None
            and ticker not in tickers
        ):
            tickers.append(ticker)

    return tickers


# ============================================================
# NORMALIZAÇÃO DE OPORTUNIDADE
# ============================================================

def _build_opportunity(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Converte uma linha do ranking executivo em uma
    oportunidade do schema universal.

    Nenhum score é recalculado.
    """

    return {
        "ticker":
            _clean_string(
                record.get("ticker")
            ),

        "company":
            _clean_string(
                record.get("company")
            ),

        "sector":
            _clean_string(
                record.get("setor")
            ),

        "ranking":
            _safe_int(
                record.get("ranking")
            ),

        "signal":
            _clean_string(
                record.get("signal_status")
            ),

        "signal_approved":
            _safe_bool(
                record.get("signal_approved")
            ),

        "signal_strength":
            _clean_string(
                record.get("signal_strength")
            ),

        "ranking_quality":
            _clean_string(
                record.get("ranking_quality")
            ),

        "opportunity_profile":
            _clean_string(
                record.get("opportunity_profile")
            ),

        "priority_score":
            _safe_float(
                record.get("priority_score")
            ),

        "final_score":
            _safe_float(
                record.get("final_score")
            ),

        "institutional_score":
            _safe_float(
                record.get("institutional_score")
            ),

        "institutional_classification":
            _clean_string(
                record.get(
                    "institutional_classification"
                )
            ),

        "institutional_diagnosis":
            _clean_string(
                record.get(
                    "institutional_diagnosis"
                )
            ),

        "technical_entry_score":
            _safe_float(
                record.get(
                    "technical_entry_score"
                )
            ),

        "technical_classification":
            _clean_string(
                record.get(
                    "technical_classification"
                )
            ),

        "technical_diagnosis":
            _clean_string(
                record.get(
                    "technical_diagnosis"
                )
            ),

        "entry_timing_score":
            _safe_float(
                record.get(
                    "entry_timing_score"
                )
            ),

        "timing_status":
            _clean_string(
                record.get("timing_status")
            ),

        "timing_approved":
            _safe_bool(
                record.get("timing_approved")
            ),

        "timing_confidence":
            _safe_float(
                record.get("timing_confidence")
            ),

        "pullback_probability":
            _safe_float(
                record.get(
                    "pullback_probability"
                )
            ),

        "parabolic_risk":
            _clean_string(
                record.get("parabolic_risk")
            ),

        "entry_probability":
            _safe_float(
                record.get("entry_probability")
            ),

        "estimated_upside_percent":
            _safe_float(
                record.get(
                    "estimated_upside_percent"
                )
            ),

        "risk_reward_ratio":
            _safe_float(
                record.get("risk_reward_ratio")
            ),

        "close":
            _safe_float(
                record.get("close")
            ),

        "executive_decision":
            _clean_string(
                record.get("executive_decision")
            ),

        "positive_factors":
            _clean_string(
                record.get(
                    "signal_positive_factors"
                )
            ),

        "pending_conditions":
            _clean_string(
                record.get(
                    "signal_pending_conditions"
                )
            ),

        "rejection_reasons":
            _clean_string(
                record.get(
                    "signal_rejection_reasons"
                )
            ),
    }


# ============================================================
# STATUS UNIVERSAL
# ============================================================

def _determine_status(
    executive_ranking: list[Any],
    raw: dict[str, Any],
) -> str:
    """
    Define apenas saúde estrutural da integração.

    NÃO representa sinal de investimento.
    """

    if not executive_ranking:
        return "DATA_INSUFFICIENT"

    metadata = _as_dict(
        raw.get("metadata")
    )

    export_policy = _as_dict(
        metadata.get("export_policy")
    )

    preserved = export_policy.get(
        "source_results_preserved"
    )

    if preserved is False:
        return "WARNING"

    return "OK"


# ============================================================
# DECISÃO UNIVERSAL
# ============================================================

def _build_decision(
    executive_ranking: list[Any],
    approved_entries: list[Any],
    watchlist: list[Any],
) -> dict[str, Any]:
    """
    O scanner produz decisões por ativo.

    Portanto, NÃO inventamos BUY/HOLD/SELL global.

    O signal universal identifica a natureza da evidência
    entregue ao CIO.
    """

    approved_count = len(
        approved_entries
    )

    watchlist_count = len(
        watchlist
    )

    classified_count = len(
        executive_ranking
    )

    summary = (
        f"{classified_count} empresas classificadas; "
        f"{approved_count} entradas aprovadas; "
        f"{watchlist_count} ativos na watchlist."
    )

    return {
        "signal":
            "OPPORTUNITY_SCANNER",

        "confidence":
            None,

        "summary":
            summary,
    }


# ============================================================
# RISCO
# ============================================================

def _build_risk(
    executive_ranking: list[Any],
) -> dict[str, Any]:
    """
    Preserva alertas observados no próprio motor.

    Não cria score global de risco.
    """

    alerts: list[str] = []

    timing_veto_count = 0
    parabolic_high_count = 0
    pullback_required_count = 0

    for record in executive_ranking:

        if not isinstance(record, dict):
            continue

        if record.get("timing_veto") is True:
            timing_veto_count += 1

        parabolic_risk = _clean_string(
            record.get("parabolic_risk")
        )

        if (
            parabolic_risk is not None
            and parabolic_risk.upper()
            in {
                "ALTO",
                "HIGH",
            }
        ):
            parabolic_high_count += 1

        if record.get(
            "pullback_required"
        ) is True:
            pullback_required_count += 1

    if timing_veto_count:
        alerts.append(
            f"{timing_veto_count} ativo(s) "
            "com timing_veto."
        )

    if parabolic_high_count:
        alerts.append(
            f"{parabolic_high_count} ativo(s) "
            "com risco parabólico alto."
        )

    if pullback_required_count:
        alerts.append(
            f"{pullback_required_count} ativo(s) "
            "com pullback_required."
        )

    return {
        "level":
            None,

        "score":
            None,

        "alerts":
            alerts,
    }


# ============================================================
# QUALIDADE DOS DADOS
# ============================================================

def _build_data_quality(
    raw: dict[str, Any],
    executive_ranking: list[Any],
) -> dict[str, Any]:
    """
    Avalia somente integridade estrutural da mensagem.

    Não avalia a qualidade financeira do modelo.
    """

    missing_fields: list[str] = []
    warnings: list[str] = []

    if not executive_ranking:
        missing_fields.append(
            "executive_ranking"
        )

    required_asset_fields = [
        "ticker",
        "ranking",
        "signal_status",
        "final_score",
        "institutional_score",
        "technical_entry_score",
        "entry_timing_score",
        "executive_decision",
    ]

    for index, record in enumerate(
        executive_ranking
    ):

        if not isinstance(record, dict):

            warnings.append(
                f"executive_ranking[{index}] "
                "não é objeto."
            )

            continue

        missing_asset_fields = [
            field
            for field in required_asset_fields
            if field not in record
        ]

        if missing_asset_fields:

            warnings.append(
                f"executive_ranking[{index}] "
                "sem campos: "
                + ", ".join(
                    missing_asset_fields
                )
            )

    summary = _as_dict(
        raw.get("summary")
    )

    declared_count = _safe_int(
        summary.get(
            "classified_companies"
        )
    )

    actual_count = len(
        executive_ranking
    )

    if (
        declared_count is not None
        and declared_count != actual_count
    ):
        warnings.append(
            "Contagem declarada de empresas "
            "difere do executive_ranking: "
            f"{declared_count} vs {actual_count}."
        )

    score: float | None

    if missing_fields:
        score = 0.0

    elif warnings:
        score = None

    else:
        score = 1.0

    return {
        "score":
            score,

        "missing_fields":
            missing_fields,

        "warnings":
            warnings,
    }


# ============================================================
# AUDITORIA / PROVENIÊNCIA
# ============================================================

def _build_audit(
    raw: dict[str, Any],
) -> dict[str, Any]:

    metadata = _as_dict(
        raw.get("metadata")
    )

    export_policy = _as_dict(
        metadata.get("export_policy")
    )

    return {
        "source_system":
            _clean_string(
                raw.get("source_system")
            ),

        "source_export_version":
            _clean_string(
                raw.get("export_version")
            ),

        "indicators_recalculated":
            export_policy.get(
                "indicators_recalculated"
            ),

        "institutional_score_recalculated":
            export_policy.get(
                "institutional_score_recalculated"
            ),

        "technical_score_recalculated":
            export_policy.get(
                "technical_score_recalculated"
            ),

        "entry_timing_recalculated":
            export_policy.get(
                "entry_timing_recalculated"
            ),

        "signals_recalculated":
            export_policy.get(
                "signals_recalculated"
            ),

        "ranking_recalculated":
            export_policy.get(
                "ranking_recalculated"
            ),

        "executive_decisions_modified":
            export_policy.get(
                "executive_decisions_modified"
            ),

        "broker_execution_allowed":
            export_policy.get(
                "broker_execution_allowed"
            ),

        "source_results_preserved":
            export_policy.get(
                "source_results_preserved"
            ),
    }


# ============================================================
# ADAPTER PRINCIPAL
# ============================================================

def adapt_ai_infrastructure_output(
    raw: dict[str, Any],
) -> dict[str, Any]:
    """
    Converte AI_INFRASTRUCTURE_SCANNER para o schema
    universal do Investment CIO Agent.
    """

    _validate_source(
        raw
    )

    executive_ranking = _as_list(
        raw.get("executive_ranking")
    )

    approved_entries = _as_list(
        raw.get("approved_entries")
    )

    watchlist = _as_list(
        raw.get("watchlist")
    )

    best_by_sector = _as_list(
        raw.get("best_by_sector")
    )

    summary = _as_dict(
        raw.get("summary")
    )

    opportunities = [
        _build_opportunity(record)
        for record in executive_ranking
        if isinstance(record, dict)
    ]

    signal_counts = _count_field(
        executive_ranking,
        "signal_status",
    )

    ranking_quality_counts = _count_field(
        executive_ranking,
        "ranking_quality",
    )

    timing_status_counts = _count_field(
        executive_ranking,
        "timing_status",
    )

    approved_tickers = _extract_tickers(
        approved_entries
    )

    watchlist_tickers = _extract_tickers(
        watchlist
    )

    output = {
        "schema_version":
            "1.0",

        "system_id":
            SYSTEM_ID,

        "system_name":
            SYSTEM_NAME,

        "generated_at":
            _generated_at(raw),

        "status":
            _determine_status(
                executive_ranking,
                raw,
            ),

        "decision":
            _build_decision(
                executive_ranking,
                approved_entries,
                watchlist,
            ),

        "metrics": {
            "classified_companies":
                len(executive_ranking),

            "approved_entries":
                len(approved_entries),

            "watchlist_size":
                len(watchlist),

            "represented_sectors":
                len(best_by_sector),

            "signal_counts":
                signal_counts,

            "ranking_quality_counts":
                ranking_quality_counts,

            "timing_status_counts":
                timing_status_counts,

            "approved_tickers":
                approved_tickers,

            "watchlist_tickers":
                watchlist_tickers,

            "source_summary":
                summary,
        },

        "risk":
            _build_risk(
                executive_ranking
            ),

        "data_quality":
            _build_data_quality(
                raw,
                executive_ranking,
            ),

        "opportunities":
            opportunities,

        "audit":
            _build_audit(
                raw
            ),

        "metadata": {
            "source_system":
                _clean_string(
                    raw.get("source_system")
                ),

            "source_export_version":
                _clean_string(
                    raw.get("export_version")
                ),

            "adapter":
                "ai_infrastructure_adapter",

            "adapter_version":
                "1.0",

            "adapter_policy": {
                "recalculate_scores":
                    False,

                "reorder_ranking":
                    False,

                "modify_signals":
                    False,

                "remove_assets":
                    False,

                "invent_global_buy_signal":
                    False,

                "broker_execution":
                    False,
            },

            "ranking_semantics": (
                "O ranking e os sinais são preservados "
                "conforme produzidos pelo motor de origem."
            ),
        },
    }

    return output


# ============================================================
# INTERFACE GENÉRICA
# ============================================================

def adapt(
    raw: dict[str, Any],
) -> dict[str, Any]:
    """
    Interface padronizada utilizada pelo Collector.
    """

    return adapt_ai_infrastructure_output(
        raw
    )
