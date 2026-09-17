# ============================================================
# INVESTMENT CIO AGENT
# config.py
# ============================================================
#
# Configuração central dos sistemas quantitativos que alimentam
# o agente.
#
# IMPORTANTE:
# - Nenhuma chave de API deve ser colocada neste arquivo.
# - Nenhuma ordem de corretora é executada pelo agente.
# - Os sistemas quantitativos permanecem independentes.
#
# ============================================================


PROJECT_NAME = "INVESTMENT CIO AGENT"
VERSION = "0.1.0"


# ============================================================
# SISTEMAS OFICIAIS
# ============================================================

SYSTEMS = {

    "global_portfolio": {
        "name": "COPIAULTIMOROB",
        "role": "MACRO_RISK_ALLOCATION",
        "enabled": True,
    },

    "sp500_cycle": {
        "name": "SP500_CYCLE_ATLAS",
        "role": "MARKET_CYCLE_VALUATION",
        "enabled": True,
    },

    "us_equities": {
        "name": "portfolio-acoes-americana-teste",
        "role": "US_EQUITY_SELECTION_TIMING",
        "enabled": True,
    },

    "b3_equities": {
        "name": "Portfolio-B3-Operational",
        "role": "BRAZIL_EQUITY_SELECTION",
        "enabled": True,
    },

    "ai_infrastructure": {
        "name": "AI_INFRASTRUCTURE_SCANNER",
        "role": "AI_INFRASTRUCTURE_OPPORTUNITIES",
        "enabled": True,
    },

    "fii": {
        "name": "FII-Scanner",
        "role": "BRAZIL_REAL_ESTATE_FUNDS",
        "enabled": True,
    },

    "growth": {
        "name": "GROWTH-OPPORTUNITY-ENGINE",
        "role": "GROWTH_SMART_MONEY",
        "enabled": True,
    },
}


# ============================================================
# POLÍTICA DO AGENTE
# ============================================================

AGENT_POLICY = {

    # O agente não executará operações financeiras.
    "allow_broker_execution": False,

    # Preservar a decisão produzida pelos motores quantitativos.
    "override_quantitative_engine": False,

    # Exigir identificação da origem de cada sinal.
    "require_source_attribution": True,

    # Detectar divergências entre sistemas.
    "detect_conflicts": True,

    # Manter histórico das análises.
    "store_history": True,

    # Falha de um sistema não deve ser escondida.
    "report_missing_systems": True,
}


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def get_enabled_systems():

    return {
        key: value
        for key, value in SYSTEMS.items()
        if value.get("enabled", False)
    }


def validate_config():

    if not SYSTEMS:
        raise RuntimeError(
            "Nenhum sistema foi configurado."
        )

    enabled = get_enabled_systems()

    if not enabled:
        raise RuntimeError(
            "Nenhum sistema está habilitado."
        )

    return True
