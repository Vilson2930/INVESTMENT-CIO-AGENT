# ============================================================
# INVESTMENT CIO AGENT
# agents/collector.py
# ============================================================
#
# Coletor central de outputs dos sistemas quantitativos.
#
# Responsabilidades:
# 1. Ler a saída bruta de um sistema.
# 2. Identificar o sistema de origem.
# 3. Encaminhar ao adaptador correto.
# 4. Validar contra o contrato universal.
# 5. Retornar resultado padronizado ao CIO Agent.
#
# O collector NÃO:
# - recalcula indicadores;
# - altera sinais;
# - muda decisões dos robôs;
# - executa ordens.
#
# ============================================================

import json
from pathlib import Path

from adapters.sp500_cycle_adapter import (
    build_sp500_agent_output,
)

from adapters.copiaultimorob_adapter import (
    build_copiaultimorob_agent_output,
)

from adapters.us_equities_adapter import (
    adapt_us_equities_output,
)

from adapters.b3_equities_adapter import (
    adapt_b3_equities_output,
)

from adapters.ai_infrastructure_adapter import (
    adapt_ai_infrastructure_output,
)

from adapters.fii_adapter import (
    adapt_fii_output,
)

from agents.validator import (
    validate_agent_output,
)


# ============================================================
# REGISTRO DE ADAPTADORES
# ============================================================

ADAPTER_REGISTRY = {

    "SP500_CYCLE_ATLAS": (
        build_sp500_agent_output
    ),

    "COPIAULTIMOROB": (
        build_copiaultimorob_agent_output
    ),

    "PORTFOLIO_ACOES_AMERICANA": (
        adapt_us_equities_output
    ),

    "PORTFOLIO_B3_OPERATIONAL": (
        adapt_b3_equities_output
    ),

    "AI_INFRASTRUCTURE_SCANNER": (
        adapt_ai_infrastructure_output
    ),

    "FII_INSTITUTIONAL_SCANNER": (
        adapt_fii_output
    ),

}


# ============================================================
# EXCEÇÕES
# ============================================================

class CollectorError(Exception):
    """Erro geral do collector."""


class UnsupportedSystemError(CollectorError):
    """Sistema ainda não possui adaptador registrado."""


class InvalidRawOutputError(CollectorError):
    """Output bruto inválido ou incompleto."""


class UniversalValidationError(CollectorError):
    """Output adaptado não passou pelo schema universal."""


# ============================================================
# LEITURA DO JSON
# ============================================================

def load_raw_output(file_path):

    path = Path(file_path)

    if not path.exists():

        raise FileNotFoundError(
            f"Arquivo não encontrado: {path}"
        )

    if not path.is_file():

        raise InvalidRawOutputError(
            f"O caminho não é um arquivo: {path}"
        )

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            payload = json.load(file)

    except json.JSONDecodeError as error:

        raise InvalidRawOutputError(
            f"JSON inválido em {path}: {error}"
        ) from error

    if not isinstance(payload, dict):

        raise InvalidRawOutputError(
            "A saída bruta deve possuir "
            "um objeto JSON na raiz."
        )

    return payload


# ============================================================
# IDENTIFICAÇÃO DO SISTEMA
# ============================================================

def identify_source_system(payload):

    if not isinstance(payload, dict):

        raise InvalidRawOutputError(
            "Payload deve ser um dicionário."
        )

    source_system = payload.get(
        "source_system"
    )

    if not source_system:

        raise InvalidRawOutputError(
            "Campo obrigatório "
            "'source_system' não encontrado."
        )

    if not isinstance(
        source_system,
        str
    ):

        raise InvalidRawOutputError(
            "Campo 'source_system' deve "
            "ser uma string."
        )

    return source_system


# ============================================================
# SELEÇÃO DO ADAPTADOR
# ============================================================

def get_adapter(source_system):

    adapter = ADAPTER_REGISTRY.get(
        source_system
    )

    if adapter is None:

        raise UnsupportedSystemError(
            "Sistema sem adaptador registrado: "
            f"{source_system}"
        )

    return adapter


# ============================================================
# VALIDAÇÃO UNIVERSAL
# ============================================================

def validate_universal_output(output):

    validation = validate_agent_output(
        output
    )

    if not validation["valid"]:

        errors = validation.get(
            "errors",
            []
        )

        formatted_errors = []

        for error in errors:

            path = error.get(
                "path",
                "unknown"
            )

            message = error.get(
                "message",
                "Erro desconhecido."
            )

            formatted_errors.append(
                f"{path}: {message}"
            )

        error_text = "; ".join(
            formatted_errors
        )

        raise UniversalValidationError(
            "Output adaptado não passou "
            "pelo contrato universal. "
            f"Erros: {error_text}"
        )

    return validation


# ============================================================
# PROCESSAMENTO DE PAYLOAD
# ============================================================

def collect_payload(payload):

    source_system = (
        identify_source_system(
            payload
        )
    )

    adapter = get_adapter(
        source_system
    )

    output = adapter(
        payload
    )

    validate_universal_output(
        output
    )

    return output


# ============================================================
# PROCESSAMENTO DE ARQUIVO
# ============================================================

def collect_file(file_path):

    payload = load_raw_output(
        file_path
    )

    return collect_payload(
        payload
    )


# ============================================================
# PROCESSAMENTO SEGURO
# ============================================================

def safe_collect_file(file_path):

    try:

        output = collect_file(
            file_path
        )

        return {

            "success": True,

            "system_id": output.get(
                "system_id"
            ),

            "system_name": output.get(
                "system_name"
            ),

            "status": output.get(
                "status"
            ),

            "output": output,

            "error": None,
        }

    except Exception as error:

        return {

            "success": False,

            "system_id": None,

            "system_name": None,

            "status": "ERROR",

            "output": None,

            "error": {

                "type": type(
                    error
                ).__name__,

                "message": str(
                    error
                ),
            },
        }


# ============================================================
# INFORMAÇÕES DO COLLECTOR
# ============================================================

def get_registered_systems():

    return sorted(
        ADAPTER_REGISTRY.keys()
    )


def is_system_supported(
    source_system
):

    return (
        source_system
        in ADAPTER_REGISTRY
    )
