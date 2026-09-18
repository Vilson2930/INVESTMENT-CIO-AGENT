# ============================================================
# adapters/b3_equities_adapter.py
# INVESTMENT CIO AGENT
#
# ADAPTER — PORTFOLIO-B3-OPERATIONAL
#
# Objetivo:
# Converter o agent_output_raw.json produzido pelo
# Portfolio-B3-Operational para o schema universal do
# Investment CIO Agent.
#
# PRINCÍPIOS:
# - NÃO recalcula seleção fundamental
# - NÃO recalcula sinais técnicos
# - NÃO recalcula pesos
# - NÃO remove ativos da carteira
# - NÃO transforma EVITAR em exclusão
# - NÃO altera decisão do sistema-fonte
# - Preserva rastreabilidade dos dados originais
# ============================================================

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


# ============================================================
# IDENTIDADE DO SISTEMA
# ============================================================

SYSTEM_ID = "b3_equities"
SYSTEM_NAME = "Portfolio-B3-Operational"

ACCEPTED_SOURCE_SYSTEMS = {
    "PORTFOLIO_B3_OPERATIONAL",
    "Portfolio-B3-Operational",
}

ADAPTER_VERSION = "1.0"


# ============================================================
# UTILITÁRIOS
# ============================================================

def _safe_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    return text


def _unique(values: list[Any]) -> list[Any]:
    result = []

    for value in values:
        if value not in result:
            result.append(value)

    return result


# ============================================================
# VALIDAÇÃO DA FONTE
# ============================================================

def _validate_source(raw: dict) -> None:
    if not isinstance(raw, dict):
        raise TypeError(
            "O output bruto do Portfolio-B3 deve ser um dicionário."
        )

    source_system = raw.get("source_system")

    if source_system not in ACCEPTED_SOURCE_SYSTEMS:
        raise ValueError(
            "source_system inválido para o B3 Equities Adapter: "
            f"{source_system!r}"
        )


# ============================================================
# POSIÇÕES
# ============================================================

def _build_position(position: dict) -> dict:

    ticker = _normalize_text(
        position.get("TICKER")
    )

    sector = _normalize_text(
        position.get("MACRO_SECTOR")
    )

    technical_signal = _normalize_text(
        position.get("SIGNAL_TECHNICAL")
    )

    technical_conviction = _normalize_text(
        position.get("CONVICTION_TECHNICAL")
    )

    technical_risk = _normalize_text(
        position.get("RISK_TECHNICAL")
    )

    operational_action = _normalize_text(
        position.get("OPERATIONAL_ACTION")
    )

    technical_status = _normalize_text(
        position.get("TECHNICAL_STATUS")
    )

    return {
        "ticker": ticker,

        "sector": sector,

        "top4_rank": _safe_int(
            position.get("TOP4_RANK")
        ),

        "sector_rank": _safe_int(
            position.get("SECTOR_RANK")
        ),

        "selection": {
            "price_quality_status": _normalize_text(
                position.get("PRICE_QUALITY_STATUS")
            ),

            "discount_52w": _safe_float(
                position.get("DISCOUNT_52W")
            ),

            "discount_score": _safe_float(
                position.get("DISCOUNT_SCORE")
            ),

            "fund_components_valid": _safe_int(
                position.get("FUND_COMPONENTS_VALID")
            ),

            "fund_score": _safe_float(
                position.get("FUND_SCORE")
            ),

            "final_score": _safe_float(
                position.get("FINAL_SCORE")
            ),
        },

        "allocation": {
            "sector_weight": _safe_float(
                position.get("SECTOR_WEIGHT")
            ),

            "within_sector_weight": _safe_float(
                position.get("WITHIN_SECTOR_WEIGHT")
            ),

            "portfolio_weight": _safe_float(
                position.get("PORTFOLIO_WEIGHT")
            ),
        },

        "technical": {
            "status": technical_status,

            "date": _normalize_text(
                position.get("TECHNICAL_DATE")
            ),

            "observations": _safe_int(
                position.get("TECHNICAL_OBS")
            ),

            "price": _safe_float(
                position.get("TECH_PRICE")
            ),

            "mm20": _safe_float(
                position.get("MM20")
            ),

            "mm50": _safe_float(
                position.get("MM50")
            ),

            "mm200": _safe_float(
                position.get("MM200")
            ),

            "rsi14": _safe_float(
                position.get("RSI14")
            ),

            "macd": _safe_float(
                position.get("MACD")
            ),

            "macd_signal": _safe_float(
                position.get("MACD_SIGNAL")
            ),

            "macd_hist": _safe_float(
                position.get("MACD_HIST")
            ),

            "atr14": _safe_float(
                position.get("ATR14")
            ),

            "atr_pct": _safe_float(
                position.get("ATR_PCT")
            ),

            "return_20d": _safe_float(
                position.get("RETURN_20D")
            ),

            "return_60d": _safe_float(
                position.get("RETURN_60D")
            ),

            "dist_mm20": _safe_float(
                position.get("DIST_MM20")
            ),

            "dist_mm50": _safe_float(
                position.get("DIST_MM50")
            ),

            "dist_mm200": _safe_float(
                position.get("DIST_MM200")
            ),

            "volume_strength": _safe_float(
                position.get("VOLUME_STRENGTH")
            ),

            "score_trend": _safe_float(
                position.get("SCORE_TREND")
            ),

            "score_entry": _safe_float(
                position.get("SCORE_ENTRY")
            ),

            "score_momentum": _safe_float(
                position.get("SCORE_MOMENTUM")
            ),

            "score_volume": _safe_float(
                position.get("SCORE_VOLUME")
            ),

            "score_risk": _safe_float(
                position.get("SCORE_RISK")
            ),

            "score_technical": _safe_float(
                position.get("SCORE_TECHNICAL")
            ),

            "signal": technical_signal,

            "conviction": technical_conviction,

            "risk": technical_risk,

            "operational_action": operational_action,

            "trend_status": _normalize_text(
                position.get("TREND_STATUS")
            ),

            "rsi_status": _normalize_text(
                position.get("RSI_STATUS")
            ),

            "momentum_status": _normalize_text(
                position.get("MOMENTUM_STATUS")
            ),

            "volume_status": _normalize_text(
                position.get("VOLUME_STATUS")
            ),

            "volatility_status": _normalize_text(
                position.get("VOLATILITY_STATUS")
            ),

            "diagnostic": _normalize_text(
                position.get("TECHNICAL_DIAGNOSTIC")
            ),
        },

        "decision": {
            "signal": technical_signal,

            "conviction": technical_conviction,

            "risk": technical_risk,

            "operational_action": operational_action,
        },
    }


# ============================================================
# RESUMOS
# ============================================================

def _build_signal_counts(
    positions: list[dict],
) -> dict:

    signals = []

    for position in positions:
        signal = (
            position
            .get("decision", {})
            .get("signal")
        )

        if signal:
            signals.append(signal)

    return dict(Counter(signals))


def _build_sector_counts(
    positions: list[dict],
) -> dict:

    sectors = []

    for position in positions:
        sector = position.get("sector")

        if sector:
            sectors.append(sector)

    return dict(Counter(sectors))


def _calculate_weight_sum(
    positions: list[dict],
) -> float:

    total = 0.0

    for position in positions:
        weight = (
            position
            .get("allocation", {})
            .get("portfolio_weight")
        )

        if weight is not None:
            total += weight

    return total


# ============================================================
# QUALIDADE DOS DADOS
# ============================================================

def _build_data_quality(
    raw: dict,
    positions: list[dict],
) -> dict:

    warnings = []
    missing_fields = []

    portfolio_audit = (
        raw.get("portfolio_audit")
        or {}
    )

    technical_audit = (
        raw.get("technical_audit")
        or {}
    )

    price_audit = (
        raw.get("price_audit")
        or {}
    )

    if not portfolio_audit.get(
        "valid",
        False,
    ):
        warnings.append(
            "A auditoria estrutural da carteira não foi aprovada."
        )

    for item in (
        portfolio_audit.get("missing_fields")
        or []
    ):
        missing_fields.append(str(item))

    for item in (
        portfolio_audit.get("warnings")
        or []
    ):
        warnings.append(str(item))

    if len(positions) != 12:
        warnings.append(
            "Quantidade de posições diferente "
            f"de 12: {len(positions)}."
        )

    missing_tickers = [
        index
        for index, position in enumerate(positions)
        if not position.get("ticker")
    ]

    if missing_tickers:
        missing_fields.append(
            "positions[].ticker"
        )

    missing_signals = [
        position.get("ticker")
        for position in positions
        if not (
            position
            .get("decision", {})
            .get("signal")
        )
    ]

    if missing_signals:
        warnings.append(
            "Ativos sem sinal técnico: "
            + ", ".join(
                str(item)
                for item in missing_signals
            )
        )

    insufficient = [
        position.get("ticker")
        for position in positions
        if (
            position
            .get("technical", {})
            .get("status")
            == "INSUFFICIENT_INDICATORS"
        )
    ]

    if insufficient:
        warnings.append(
            "Indicadores técnicos insuficientes: "
            + ", ".join(
                str(item)
                for item in insufficient
            )
        )

    technical_status_counts = (
        technical_audit.get("status_counts")
        or {}
    )

    technical_review = _safe_int(
        technical_status_counts.get("REVIEW")
    ) or 0

    if technical_review > 0:
        warnings.append(
            "Auditoria técnica contém "
            f"{technical_review} item(ns) REVIEW."
        )

    external_status_counts = (
        price_audit.get("external_status_counts")
        or {}
    )

    external_review = _safe_int(
        external_status_counts.get("REVIEW")
    ) or 0

    if external_review > 0:
        warnings.append(
            "Validação externa de preços contém "
            f"{external_review} item(ns) REVIEW."
        )

    weight_sum = _calculate_weight_sum(
        positions
    )

    if abs(weight_sum - 1.0) > 0.001:
        warnings.append(
            "A soma dos pesos da carteira "
            f"é {weight_sum:.6f}, diferente de 1.0."
        )

    return {
        "score": None,

        "missing_fields": _unique(
            missing_fields
        ),

        "warnings": _unique(
            warnings
        ),
    }


# ============================================================
# STATUS
# ============================================================

def _determine_status(
    data_quality: dict,
) -> str:

    if data_quality.get("missing_fields"):
        return "WARNING"

    if data_quality.get("warnings"):
        return "WARNING"

    return "OK"


# ============================================================
# RISCO
# ============================================================

def _build_risk(
    positions: list[dict],
    data_quality: dict,
) -> dict:

    risk_counts = Counter()

    for position in positions:
        risk = (
            position
            .get("decision", {})
            .get("risk")
        )

        if risk:
            risk_counts[risk] += 1

    return {
        "level": None,

        "score": None,

        "alerts": list(
            data_quality.get("warnings")
            or []
        ),

        "technical_risk_counts": dict(
            risk_counts
        ),
    }


# ============================================================
# DECISÃO UNIVERSAL
# ============================================================

def _build_decision(
    positions: list[dict],
) -> dict:

    signal_counts = _build_signal_counts(
        positions
    )

    return {
        "signal":
            "PORTFOLIO_WITH_ASSET_SIGNALS",

        "confidence":
            None,

        "summary":
            (
                "Carteira B3 selecionada pelo sistema-fonte "
                "com sinais técnicos preservados por ativo. "
                "Nenhum sinal global de carteira foi "
                "inferido pelo adapter."
            ),

        "asset_signal_counts":
            signal_counts,
    }


# ============================================================
# MÉTRICAS
# ============================================================

def _build_metrics(
    raw: dict,
    positions: list[dict],
) -> dict:

    portfolio_audit = (
        raw.get("portfolio_audit")
        or {}
    )

    technical_audit = (
        raw.get("technical_audit")
        or {}
    )

    price_audit = (
        raw.get("price_audit")
        or {}
    )

    engine = (
        raw.get("engine")
        or {}
    )

    return {
        "number_of_stocks":
            len(positions),

        "number_of_sectors":
            len(
                _build_sector_counts(
                    positions
                )
            ),

        "sector_counts":
            _build_sector_counts(
                positions
            ),

        "portfolio_weight_sum":
            _calculate_weight_sum(
                positions
            ),

        "asset_signal_counts":
            _build_signal_counts(
                positions
            ),

        "portfolio_structure_valid":
            portfolio_audit.get("valid"),

        "duplicate_tickers":
            portfolio_audit.get(
                "duplicate_tickers"
            ),

        "architecture":
            engine.get("architecture"),

        "sector_rule":
            engine.get("sector_rule"),

        "stock_rule":
            engine.get("stock_rule"),

        "technical_layer":
            engine.get("technical_layer"),

        "technical_audit":
            technical_audit,

        "price_audit":
            price_audit,

        "sector_summary":
            raw.get("sector_summary")
            or [],
    }


# ============================================================
# ADAPTER PRINCIPAL
# ============================================================

def adapt_b3_equities_output(
    raw: dict,
) -> dict:

    _validate_source(raw)

    raw_positions = (
        raw.get("positions")
        or []
    )

    if not isinstance(
        raw_positions,
        list,
    ):
        raise TypeError(
            "O campo 'positions' deve ser uma lista."
        )

    positions = [
        _build_position(position)
        for position in raw_positions
        if isinstance(position, dict)
    ]

    data_quality = _build_data_quality(
        raw=raw,
        positions=positions,
    )

    status = _determine_status(
        data_quality
    )

    decision = _build_decision(
        positions
    )

    metrics = _build_metrics(
        raw=raw,
        positions=positions,
    )

    risk = _build_risk(
        positions=positions,
        data_quality=data_quality,
    )

    result = {
        "schema_version":
            "1.0",

        "system_id":
            SYSTEM_ID,

        "system_name":
            SYSTEM_NAME,

        "generated_at":
            raw.get("generated_at"),

        "status":
            status,

        "decision":
            decision,

        "metrics":
            metrics,

        "risk":
            risk,

        "data_quality":
            data_quality,

        "positions":
            positions,

        "audit": {
            "portfolio_audit":
                raw.get("portfolio_audit")
                or {},

            "technical_audit":
                raw.get("technical_audit")
                or {},

            "price_audit":
                raw.get("price_audit")
                or {},
        },

        "metadata": {
            "adapter_version":
                ADAPTER_VERSION,

            "source_system":
                raw.get("source_system"),

            "source_export_version":
                raw.get("export_version"),

            "engine":
                raw.get("engine")
                or {},

            "source_files":
                raw.get("source_files")
                or {},

            "adapter_policy": {
                "selection_recalculated":
                    False,

                "technical_signal_recalculated":
                    False,

                "weights_recalculated":
                    False,

                "portfolio_modified":
                    False,

                "source_decisions_preserved":
                    True,

                "technical_layer_overrides_selection":
                    False,

                "broker_execution_allowed":
                    False,
            },
        },
    }

    return result


# ============================================================
# INTERFACE GENÉRICA DO COLLECTOR
# ============================================================

def adapt(
    raw: dict,
) -> dict:

    return adapt_b3_equities_output(
        raw
    )


# ============================================================
# ARQUIVO -> ARQUIVO
# ============================================================

def adapt_b3_equities_file(
    input_file: str | Path,
    output_file: str | Path | None = None,
) -> dict:

    input_path = Path(
        input_file
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {input_path}"
        )

    with open(
        input_path,
        "r",
        encoding="utf-8",
    ) as file:
        raw = json.load(file)

    result = adapt_b3_equities_output(
        raw
    )

    if output_file is not None:

        output_path = Path(
            output_file
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            )

    return result


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    default_input = (
        Path("inputs")
        / "b3_equities"
        / "agent_output_raw.json"
    )

    default_output = (
        Path("outputs")
        / "b3_equities_agent_output.json"
    )

    result = adapt_b3_equities_file(
        input_file=default_input,
        output_file=default_output,
    )

    print()
    print("=" * 72)
    print(
        "INVESTMENT CIO AGENT — "
        "B3 EQUITIES ADAPTER"
    )
    print("=" * 72)

    print(
        f"Sistema: {result['system_name']}"
    )

    print(
        f"Status: {result['status']}"
    )

    print(
        "Ações: "
        f"{result['metrics']['number_of_stocks']}"
    )

    print(
        "Setores: "
        f"{result['metrics']['number_of_sectors']}"
    )

    print(
        "Sinais técnicos: "
        f"{result['metrics']['asset_signal_counts']}"
    )

    print(
        "Peso total: "
        f"{result['metrics']['portfolio_weight_sum']:.6f}"
    )

    print(
        f"Output: {default_output}"
    )

    print("=" * 72)
