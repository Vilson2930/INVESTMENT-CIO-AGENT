from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Union

SYSTEM_ID = "us_equities"
SYSTEM_NAME = "portfolio-acoes-americana-teste"
EXPECTED_SOURCE_SYSTEMS = {"PORTFOLIO_ACOES_AMERICANA", "portfolio-acoes-americana-teste"}

def _load_raw(source: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(source, dict):
        return source
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError("A raiz do JSON deve ser um objeto.")
    return data

def _normalize_positions(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(x) for x in value if isinstance(x, dict)]

def _build_opportunities(positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fields = (
        "ticker", "sector", "entry_signal", "signal_percentile",
        "final_signal_score", "selection_score", "buy_priority_sector",
        "sector_weight", "stock_weight", "valuation_status",
        "discount_status", "fundamental_status", "timing_method"
    )
    return [{k: p.get(k) for k in fields} for p in positions]

def adapt_us_equities_output(source: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
    raw = _load_raw(source)
    source_system = raw.get("source_system")
    if source_system not in EXPECTED_SOURCE_SYSTEMS:
        raise ValueError(f"source_system inesperado: {source_system!r}")

    engine = raw.get("engine") if isinstance(raw.get("engine"), dict) else {}
    audit = raw.get("portfolio_audit") if isinstance(raw.get("portfolio_audit"), dict) else {}
    signals = raw.get("signal_summary") if isinstance(raw.get("signal_summary"), dict) else {}
    sectors = raw.get("sector_summary") if isinstance(raw.get("sector_summary"), list) else []
    policy = raw.get("policy") if isinstance(raw.get("policy"), dict) else {}
    positions = _normalize_positions(raw.get("positions"))

    missing, warnings = [], []
    if not raw.get("generated_at"):
        missing.append("generated_at")
    if not positions:
        missing.append("positions")

    n_stocks = audit.get("number_of_stocks")
    n_sectors = audit.get("number_of_sectors")
    total_weight = audit.get("total_weight")

    if n_stocks != 15:
        warnings.append(f"Estrutura esperada de 15 ações; recebido: {n_stocks}.")
    if n_sectors != 3:
        warnings.append(f"Estrutura esperada de 3 setores; recebido: {n_sectors}.")
    if isinstance(total_weight, (int, float)) and abs(float(total_weight) - 1.0) > 1e-6:
        warnings.append(f"Peso total diferente de 1.0: {total_weight}.")

    strong = int(signals.get("ENTRADA FORTE", 0) or 0)
    entry = int(signals.get("ENTRADA", 0) or 0)
    wait = int(signals.get("AGUARDAR", 0) or 0)
    no_buy = int(signals.get("NÃO COMPRAR AGORA", 0) or 0)

    if n_stocks is not None and strong + entry + wait + no_buy != n_stocks:
        warnings.append("A soma dos sinais não coincide com o número de ações.")

    status = "DATA_INSUFFICIENT" if missing else ("WARNING" if warnings else "OK")
    summary = (
        f"Carteira de ações americanas com {n_stocks} ações: "
        f"{strong} ENTRADA FORTE, {entry} ENTRADA, "
        f"{wait} AGUARDAR e {no_buy} NÃO COMPRAR AGORA."
    )

    return {
        "schema_version": "1.0",
        "system_id": SYSTEM_ID,
        "system_name": SYSTEM_NAME,
        "generated_at": raw.get("generated_at"),
        "status": status,
        "decision": {
            "signal": "MULTI_ASSET_SELECTION",
            "confidence": None,
            "summary": summary,
        },
        "metrics": {
            "asset_class": engine.get("asset_class"),
            "engine_role": engine.get("role"),
            "portfolio_size": n_stocks,
            "number_of_sectors": n_sectors,
            "total_weight": total_weight if isinstance(total_weight, (int, float)) else None,
            "entry_strong": strong,
            "entry": entry,
            "wait": wait,
            "do_not_buy_now": no_buy,
            "sector_summary": sectors,
        },
        "risk": {"level": None, "score": None, "alerts": warnings},
        "data_quality": {"score": None, "missing_fields": missing, "warnings": warnings},
        "positions": positions,
        "opportunities": _build_opportunities(positions),
        "audit": {
            "source_system": source_system,
            "export_version": raw.get("export_version"),
            "portfolio_audit": audit,
            "source_policy": policy,
            "source_signals_preserved": True,
            "source_scores_preserved": True,
            "source_weights_preserved": True,
            "adapter_recalculated_signals": False,
        },
        "metadata": {
            "adapter": "us_equities_adapter",
            "adapter_version": "1.0",
            "source_engine_name": engine.get("name"),
            "source_engine_role": engine.get("role"),
        },
    }

def adapt(source: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
    return adapt_us_equities_output(source)
