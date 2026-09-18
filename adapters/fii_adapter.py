# ============================================================
# INVESTMENT CIO AGENT
# adapters/fii_adapter.py
# ============================================================
#
# Adapter:
# FII INSTITUTIONAL SCANNER
#
# RESPONSABILIDADE
# ------------------------------------------------------------
# Traduz a saída bruta do FII Institutional Scanner para o
# schema universal do Investment CIO Agent.
#
# PRINCÍPIOS
# ------------------------------------------------------------
# 1. Não recalcula scores.
# 2. Não recalcula ranking.
# 3. Não reordena ranking.
# 4. Não altera a carteira.
# 5. Não altera pesos.
# 6. Não altera decisões operacionais.
# 7. Não altera fração de execução.
# 8. Não transforma capital reservado em rejeição do ativo.
# 9. Não cria BUY/HOLD global.
# 10. Não executa ordens.
#
# ============================================================

from __future__ import annotations

from collections import Counter
from typing import Any


# ============================================================
# IDENTIDADE
# ============================================================

SYSTEM_ID = "fii"

SYSTEM_NAME = "FII Institutional Scanner"

ACCEPTED_SOURCE_SYSTEMS = {
    "FII_INSTITUTIONAL_SCANNER",
    "FII Institutional Scanner",
}


# ============================================================
# AUXILIARES
# ============================================================

def _safe_float(
    value: Any,
) -> float | None:

    if value is None:
        return None

    try:

        converted = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    if converted != converted:
        return None

    if converted in (
        float("inf"),
        float("-inf"),
    ):
        return None

    return converted


def _safe_int(
    value: Any,
) -> int | None:

    if value is None:
        return None

    try:

        return int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


def _safe_bool(
    value: Any,
) -> bool | None:

    if isinstance(
        value,
        bool,
    ):
        return value

    if value is None:
        return None

    return None


def _safe_string(
    value: Any,
) -> str | None:

    if value is None:
        return None

    value = str(
        value
    ).strip()

    if not value:
        return None

    return value


def _as_list(
    value: Any,
) -> list:

    if isinstance(
        value,
        list,
    ):
        return value

    return []


def _as_dict(
    value: Any,
) -> dict:

    if isinstance(
        value,
        dict,
    ):
        return value

    return {}


def _count_field(
    records: list[dict],
    field: str,
) -> dict[str, int]:

    counter = Counter()

    for item in records:

        if not isinstance(
            item,
            dict,
        ):
            continue

        value = item.get(
            field
        )

        if value is None:
            value = "SEM_DADO"

        counter[
            str(value)
        ] += 1

    return dict(
        counter
    )


# ============================================================
# VALIDAÇÃO DA FONTE
# ============================================================

def _validate_source(
    raw: dict[str, Any],
) -> None:

    if not isinstance(
        raw,
        dict,
    ):

        raise TypeError(
            "A saída do FII Scanner deve ser um dict."
        )

    source_system = raw.get(
        "source_system"
    )

    if (
        source_system
        not in ACCEPTED_SOURCE_SYSTEMS
    ):

        raise ValueError(
            "source_system inválido para "
            "FII Institutional Scanner: "
            f"{source_system}"
        )

    ranking = raw.get(
        "ranking"
    )

    portfolio = raw.get(
        "portfolio"
    )

    diagnostics = raw.get(
        "diagnostics"
    )

    if not isinstance(
        ranking,
        list,
    ):

        raise ValueError(
            "ranking ausente ou inválido."
        )

    if not ranking:

        raise ValueError(
            "ranking está vazio."
        )

    if not isinstance(
        portfolio,
        list,
    ):

        raise ValueError(
            "portfolio ausente ou inválido."
        )

    if not portfolio:

        raise ValueError(
            "portfolio está vazio."
        )

    if not isinstance(
        diagnostics,
        dict,
    ):

        raise ValueError(
            "diagnostics ausente ou inválido."
        )


# ============================================================
# RANKING INSTITUCIONAL
# ============================================================

def _build_ranking(
    raw_ranking: list[dict],
) -> list[dict]:

    result = []

    # IMPORTANTE:
    # não usamos sorted().
    #
    # A ordem recebida do motor é preservada exatamente.

    for item in raw_ranking:

        if not isinstance(
            item,
            dict,
        ):
            continue

        result.append(
            {
                "ticker":
                    _safe_string(
                        item.get(
                            "ticker"
                        )
                    ),

                "ranking_institucional":
                    _safe_int(
                        item.get(
                            "ranking_institucional"
                        )
                    ),

                "categoria_motor":
                    _safe_string(
                        item.get(
                            "categoria_motor"
                        )
                    ),

                "segmento":
                    _safe_string(
                        item.get(
                            "segmento"
                        )
                    ),

                "fundamental_score_final":
                    _safe_float(
                        item.get(
                            "fundamental_score_final"
                        )
                    ),

                "status_fundamental":
                    _safe_string(
                        item.get(
                            "status_fundamental"
                        )
                    ),

                "fundamental_aprovado_final":
                    _safe_bool(
                        item.get(
                            "fundamental_aprovado_final"
                        )
                    ),

                "technical_score":
                    _safe_float(
                        item.get(
                            "technical_score"
                        )
                    ),

                "classificacao_tecnica":
                    _safe_string(
                        item.get(
                            "classificacao_tecnica"
                        )
                    ),

                "status_timing":
                    _safe_string(
                        item.get(
                            "status_timing"
                        )
                    ),

                "institutional_score":
                    _safe_float(
                        item.get(
                            "institutional_score"
                        )
                    ),

                "classificacao_institucional":
                    _safe_string(
                        item.get(
                            "classificacao_institucional"
                        )
                    ),

                "decisao_operacional":
                    _safe_string(
                        item.get(
                            "decisao_operacional"
                        )
                    ),

                "prioridade_portfolio":
                    _safe_string(
                        item.get(
                            "prioridade_portfolio"
                        )
                    ),

                "candidato_carteira":
                    _safe_bool(
                        item.get(
                            "candidato_carteira"
                        )
                    ),

                "dy_12m":
                    _safe_float(
                        item.get(
                            "dy_12m"
                        )
                    ),

                "pvp":
                    _safe_float(
                        item.get(
                            "pvp"
                        )
                    ),

                "confianca_dados":
                    _safe_float(
                        item.get(
                            "confianca_dados"
                        )
                    ),

                "liquidez_media_60d":
                    _safe_float(
                        item.get(
                            "liquidez_media_60d"
                        )
                    ),

                "pilar_renda":
                    _safe_float(
                        item.get(
                            "pilar_renda"
                        )
                    ),

                "pilar_estrutura":
                    _safe_float(
                        item.get(
                            "pilar_estrutura"
                        )
                    ),

                "pilar_valuation":
                    _safe_float(
                        item.get(
                            "pilar_valuation"
                        )
                    ),

                "pilar_robustez":
                    _safe_float(
                        item.get(
                            "pilar_robustez"
                        )
                    ),

                "pilar_risco":
                    _safe_float(
                        item.get(
                            "pilar_risco"
                        )
                    ),

                "risco_especial":
                    item.get(
                        "risco_especial"
                    ),

                # ------------------------------------------------
                # Dados técnicos preservados
                # ------------------------------------------------

                "rsi14":
                    _safe_float(
                        item.get(
                            "rsi14"
                        )
                    ),

                "retorno_1m":
                    _safe_float(
                        item.get(
                            "retorno_1m"
                        )
                    ),

                "retorno_3m":
                    _safe_float(
                        item.get(
                            "retorno_3m"
                        )
                    ),

                "retorno_6m":
                    _safe_float(
                        item.get(
                            "retorno_6m"
                        )
                    ),

                "dist_sma20":
                    _safe_float(
                        item.get(
                            "dist_sma20"
                        )
                    ),

                "dist_sma50":
                    _safe_float(
                        item.get(
                            "dist_sma50"
                        )
                    ),

                "dist_sma200":
                    _safe_float(
                        item.get(
                            "dist_sma200"
                        )
                    ),

                "distancia_max_52s":
                    _safe_float(
                        item.get(
                            "distancia_max_52s"
                        )
                    ),

                "volume_relativo":
                    _safe_float(
                        item.get(
                            "volume_relativo"
                        )
                    ),

                "score_tendencia":
                    _safe_float(
                        item.get(
                            "score_tendencia"
                        )
                    ),

                "penalidade_estiramento":
                    _safe_float(
                        item.get(
                            "penalidade_estiramento"
                        )
                    ),
            }
        )

    return result


# ============================================================
# CARTEIRA ESTRATÉGICA
# ============================================================

def _build_positions(
    raw_portfolio: list[dict],
) -> list[dict]:

    positions = []

    # A ordem final produzida pelo Portfolio Engine também
    # é preservada. Não fazemos sorted().

    for item in raw_portfolio:

        if not isinstance(
            item,
            dict,
        ):
            continue

        strategic_weight = _safe_float(
            item.get(
                "peso_estrategico"
            )
        )

        executable_weight = _safe_float(
            item.get(
                "peso_executavel"
            )
        )

        reserved_weight = _safe_float(
            item.get(
                "peso_reservado"
            )
        )

        positions.append(
            {
                "ticker":
                    _safe_string(
                        item.get(
                            "ticker"
                        )
                    ),

                "category":
                    _safe_string(
                        item.get(
                            "categoria_motor"
                        )
                    ),

                "segment":
                    _safe_string(
                        item.get(
                            "segmento"
                        )
                    ),

                # ============================================
                # SCORES ORIGINAIS
                # ============================================

                "fundamental_score":
                    _safe_float(
                        item.get(
                            "fundamental_score_final"
                        )
                    ),

                "technical_score":
                    _safe_float(
                        item.get(
                            "technical_score"
                        )
                    ),

                "institutional_score":
                    _safe_float(
                        item.get(
                            "institutional_score"
                        )
                    ),

                "institutional_classification":
                    _safe_string(
                        item.get(
                            "classificacao_institucional"
                        )
                    ),

                # ============================================
                # TIMING / DECISÃO
                # ============================================

                "timing_status":
                    _safe_string(
                        item.get(
                            "status_timing"
                        )
                    ),

                "operational_decision":
                    _safe_string(
                        item.get(
                            "decisao_operacional"
                        )
                    ),

                "final_status":
                    _safe_string(
                        item.get(
                            "status_final"
                        )
                    ),

                # ============================================
                # PESOS
                # ============================================

                "strategic_weight":
                    strategic_weight,

                "strategic_weight_pct":
                    _safe_float(
                        item.get(
                            "peso_estrategico_pct"
                        )
                    ),

                "execution_fraction":
                    _safe_float(
                        item.get(
                            "fracao_execucao"
                        )
                    ),

                "executable_weight":
                    executable_weight,

                "executable_weight_pct":
                    _safe_float(
                        item.get(
                            "peso_executavel_pct"
                        )
                    ),

                "reserved_weight":
                    reserved_weight,

                "reserved_weight_pct":
                    _safe_float(
                        item.get(
                            "peso_reservado_pct"
                        )
                    ),

                # ============================================
                # FUNDAMENTOS
                # ============================================

                "dy_12m":
                    _safe_float(
                        item.get(
                            "dy_12m"
                        )
                    ),

                "pvp":
                    _safe_float(
                        item.get(
                            "pvp"
                        )
                    ),

                "data_confidence":
                    _safe_float(
                        item.get(
                            "confianca_dados"
                        )
                    ),

                # ============================================
                # INFORMAÇÃO ORIGINAL COMPLEMENTAR
                # ============================================

                "portfolio_priority":
                    _safe_string(
                        item.get(
                            "prioridade_portfolio"
                        )
                    ),
            }
        )

    return positions


# ============================================================
# MÉTRICAS
# ============================================================

def _build_metrics(
    raw: dict[str, Any],
    ranking: list[dict],
    portfolio: list[dict],
) -> dict[str, Any]:

    summary = _as_dict(
        raw.get(
            "summary"
        )
    )

    diagnostics = _as_dict(
        raw.get(
            "diagnostics"
        )
    )

    exposure = _as_dict(
        diagnostics.get(
            "exposicao"
        )
    )

    return {

        # ================================================
        # TAMANHO DO PIPELINE
        # ================================================

        "database_count":
            _safe_int(
                summary.get(
                    "database_count"
                )
            ),

        "fundamentals_count":
            _safe_int(
                summary.get(
                    "fundamentals_count"
                )
            ),

        "technical_count":
            _safe_int(
                summary.get(
                    "technical_count"
                )
            ),

        "ranking_count":
            len(
                ranking
            ),

        "portfolio_count":
            len(
                portfolio
            ),

        # ================================================
        # SCORES DA CARTEIRA
        # ================================================

        "fundamental_score":
            _safe_float(
                diagnostics.get(
                    "fundamental_score"
                )
            ),

        "technical_score":
            _safe_float(
                diagnostics.get(
                    "technical_score"
                )
            ),

        "institutional_score":
            _safe_float(
                diagnostics.get(
                    "institutional_score"
                )
            ),

        "dy_12m":
            _safe_float(
                diagnostics.get(
                    "dy_12m"
                )
            ),

        # ================================================
        # RISCO / DIVERSIFICAÇÃO
        # ================================================

        "robust_volatility":
            _safe_float(
                diagnostics.get(
                    "volatilidade_robusta"
                )
            ),

        "hhi":
            _safe_float(
                diagnostics.get(
                    "hhi"
                )
            ),

        "effective_fiis":
            _safe_float(
                diagnostics.get(
                    "numero_efetivo_fiis"
                )
            ),

        "risk_trading_days":
            _safe_int(
                diagnostics.get(
                    "pregoes_risco"
                )
            ),

        # ================================================
        # EXECUÇÃO
        # ================================================

        "strategic_weight":
            _safe_float(
                summary.get(
                    "strategic_weight_sum"
                )
            ),

        "executable_weight":
            _safe_float(
                diagnostics.get(
                    "peso_executavel"
                )
            ),

        "reserved_weight":
            _safe_float(
                diagnostics.get(
                    "peso_reservado"
                )
            ),

        # ================================================
        # OTIMIZAÇÃO
        # ================================================

        "optimization_success":
            _safe_bool(
                diagnostics.get(
                    "optimization_success"
                )
            ),

        "optimization_message":
            _safe_string(
                diagnostics.get(
                    "optimization_message"
                )
            ),

        # ================================================
        # EXPOSIÇÕES
        # ================================================

        "exposure": {

            str(key):
                _safe_float(
                    value
                )

            for key, value
            in exposure.items()

        },

        # ================================================
        # DISTRIBUIÇÕES
        # ================================================

        "operational_decision_distribution":
            _count_field(
                portfolio,
                "decisao_operacional",
            ),

        "final_status_distribution":
            _count_field(
                portfolio,
                "status_final",
            ),

        "institutional_classification_distribution":
            _count_field(
                ranking,
                "classificacao_institucional",
            ),

        "category_distribution":
            _count_field(
                portfolio,
                "categoria_motor",
            ),

        "segment_distribution":
            _count_field(
                portfolio,
                "segmento",
            ),
    }


# ============================================================
# RISCO
# ============================================================

def _build_risk(
    raw: dict[str, Any],
) -> dict[str, Any]:

    diagnostics = _as_dict(
        raw.get(
            "diagnostics"
        )
    )

    extreme_events = _as_dict(
        diagnostics.get(
            "eventos_extremos"
        )
    )

    alerts = []

    for ticker, count in (
        extreme_events.items()
    ):

        numeric_count = _safe_int(
            count
        )

        if (
            numeric_count is not None
            and numeric_count > 0
        ):

            alerts.append(
                f"{ticker}: "
                f"{numeric_count} evento(s) extremo(s)"
            )

    optimization_success = (
        _safe_bool(
            diagnostics.get(
                "optimization_success"
            )
        )
    )

    if optimization_success is False:

        alerts.append(
            "Otimização de portfólio "
            "não reportou sucesso."
        )

    return {

        # Não inventamos classificação LOW/MEDIUM/HIGH.
        "level":
            None,

        # Não transformamos volatilidade em score de risco.
        "score":
            None,

        "alerts":
            alerts,

        "volatility":
            _safe_float(
                diagnostics.get(
                    "volatilidade_robusta"
                )
            ),

        "hhi":
            _safe_float(
                diagnostics.get(
                    "hhi"
                )
            ),

        "effective_fiis":
            _safe_float(
                diagnostics.get(
                    "numero_efetivo_fiis"
                )
            ),

        "extreme_events":
            extreme_events,
    }


# ============================================================
# QUALIDADE DOS DADOS
# ============================================================

def _build_data_quality(
    raw: dict[str, Any],
    ranking: list[dict],
    portfolio: list[dict],
) -> dict[str, Any]:

    missing_fields = []
    warnings = []

    if not ranking:

        missing_fields.append(
            "ranking"
        )

    if not portfolio:

        missing_fields.append(
            "portfolio"
        )

    diagnostics = _as_dict(
        raw.get(
            "diagnostics"
        )
    )

    required_diagnostics = [

        "fundamental_score",
        "technical_score",
        "institutional_score",
        "volatilidade_robusta",
        "peso_executavel",
        "peso_reservado",

    ]

    for field in required_diagnostics:

        if field not in diagnostics:

            missing_fields.append(
                f"diagnostics.{field}"
            )

    optimization_success = (
        diagnostics.get(
            "optimization_success"
        )
    )

    if optimization_success is False:

        warnings.append(
            "Portfolio optimizer reportou "
            "optimization_success=False."
        )

    # Não criamos score artificial de qualidade.
    return {

        "score":
            None,

        "missing_fields":
            missing_fields,

        "warnings":
            warnings,
    }


# ============================================================
# AUDITORIA DO EXPORTADOR DE ORIGEM
# ============================================================

def _build_audit(
    raw: dict[str, Any],
) -> dict[str, Any]:

    metadata = _as_dict(
        raw.get(
            "metadata"
        )
    )

    export_policy = _as_dict(
        metadata.get(
            "export_policy"
        )
    )

    return {

        "source_export_policy":
            export_policy,

        "adapter_policy": {

            "recalculates_scores":
                False,

            "recalculates_ranking":
                False,

            "reorders_ranking":
                False,

            "recalculates_portfolio":
                False,

            "changes_portfolio_members":
                False,

            "recalculates_weights":
                False,

            "changes_operational_decisions":
                False,

            "changes_execution_fraction":
                False,

            "changes_executable_weight":
                False,

            "changes_reserved_weight":
                False,

            "creates_global_buy_signal":
                False,

            "executes_broker_orders":
                False,

        },
    }


# ============================================================
# STATUS UNIVERSAL
# ============================================================

def _determine_status(
    data_quality: dict[str, Any],
    metrics: dict[str, Any],
) -> str:

    if data_quality[
        "missing_fields"
    ]:

        return "WARNING"

    if (
        metrics.get(
            "optimization_success"
        )
        is False
    ):

        return "WARNING"

    return "OK"


# ============================================================
# ADAPTER PRINCIPAL
# ============================================================

def adapt_fii_output(
    raw: dict[str, Any],
) -> dict[str, Any]:

    _validate_source(
        raw
    )

    raw_ranking = _as_list(
        raw.get(
            "ranking"
        )
    )

    raw_portfolio = _as_list(
        raw.get(
            "portfolio"
        )
    )

    ranking = _build_ranking(
        raw_ranking
    )

    positions = _build_positions(
        raw_portfolio
    )

    metrics = _build_metrics(

        raw=raw,

        ranking=raw_ranking,

        portfolio=raw_portfolio,

    )

    risk = _build_risk(
        raw
    )

    data_quality = (
        _build_data_quality(

            raw=raw,

            ranking=raw_ranking,

            portfolio=raw_portfolio,

        )
    )

    audit = _build_audit(
        raw
    )

    status = _determine_status(

        data_quality=data_quality,

        metrics=metrics,

    )

    executable_weight = (
        metrics.get(
            "executable_weight"
        )
    )

    reserved_weight = (
        metrics.get(
            "reserved_weight"
        )
    )

    portfolio_count = (
        metrics.get(
            "portfolio_count"
        )
    )

    summary_parts = [

        (
            f"Carteira estratégica com "
            f"{portfolio_count} FIIs."
        ),

    ]

    if executable_weight is not None:

        summary_parts.append(
            "Peso executável informado "
            f"pelo motor: "
            f"{executable_weight:.2%}."
        )

    if reserved_weight is not None:

        summary_parts.append(
            "Peso reservado informado "
            f"pelo motor: "
            f"{reserved_weight:.2%}."
        )

    # ========================================================
    # OUTPUT UNIVERSAL
    # ========================================================

    return {

        "schema_version":
            "1.0",

        "system_id":
            SYSTEM_ID,

        "system_name":
            SYSTEM_NAME,

        "generated_at":
            raw.get(
                "generated_at"
            ),

        "status":
            status,

        # ====================================================
        # DECISÃO
        # ====================================================
        #
        # O FII Scanner produz decisões por ativo e uma carteira
        # estratégica. Não inventamos BUY/HOLD global.
        #
        # ====================================================

        "decision": {

            "signal":
                "STRATEGIC_PORTFOLIO_WITH_EXECUTION",

            "confidence":
                None,

            "summary":
                " ".join(
                    summary_parts
                ),
        },

        # ====================================================
        # MÉTRICAS
        # ====================================================

        "metrics":
            metrics,

        # ====================================================
        # RISCO
        # ====================================================

        "risk":
            risk,

        # ====================================================
        # QUALIDADE DOS DADOS
        # ====================================================

        "data_quality":
            data_quality,

        # ====================================================
        # POSIÇÕES
        # ====================================================

        "positions":
            positions,

        # ====================================================
        # OPORTUNIDADES / RANKING
        # ====================================================

        "opportunities":
            ranking,

        # ====================================================
        # AUDITORIA
        # ====================================================

        "audit":
            audit,

        # ====================================================
        # METADADOS
        # ====================================================

        "metadata": {

            "source_system":
                raw.get(
                    "source_system"
                ),

            "source_export_version":
                raw.get(
                    "export_version"
                ),

            "adapter_version":
                "1.0",

            "adapter_type":
                "FII_INSTITUTIONAL_SCANNER",

            "portfolio_semantics": {

                "strategic_weight":
                    (
                        "Peso estrutural definido "
                        "pelo motor de portfólio."
                    ),

                "executable_weight":
                    (
                        "Parcela do peso estratégico "
                        "liberada para execução pelo "
                        "motor de origem."
                    ),

                "reserved_weight":
                    (
                        "Parcela estratégica ainda "
                        "reservada pelo motor. "
                        "Não significa exclusão do FII."
                    ),
            },

            "adapter_policy": {

                "recalculates_scores":
                    False,

                "recalculates_ranking":
                    False,

                "reorders_ranking":
                    False,

                "recalculates_portfolio":
                    False,

                "changes_portfolio_members":
                    False,

                "recalculates_weights":
                    False,

                "changes_operational_decisions":
                    False,

                "changes_execution_fraction":
                    False,

                "changes_executable_weight":
                    False,

                "changes_reserved_weight":
                    False,

                "creates_global_buy_signal":
                    False,

                "executes_broker_orders":
                    False,
            },
        },
    }


# ============================================================
# INTERFACE GENÉRICA DO COLLECTOR
# ============================================================

def adapt(
    raw: dict[str, Any],
) -> dict[str, Any]:

    return adapt_fii_output(
        raw
    )
