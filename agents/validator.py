# ============================================================
# INVESTMENT CIO AGENT
# agents/validator.py
# ============================================================
#
# Valida os dados recebidos dos sistemas quantitativos
# antes que sejam utilizados pelo agente central.
#
# ============================================================

import json
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker


# ============================================================
# CAMINHOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SCHEMA_PATH = (
    BASE_DIR
    / "schemas"
    / "agent_output_schema.json"
)


# ============================================================
# CARREGAMENTO DO SCHEMA
# ============================================================

def load_schema():

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema não encontrado: {SCHEMA_PATH}"
        )

    with open(
        SCHEMA_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# VALIDADOR
# ============================================================

def validate_agent_output(data):

    schema = load_schema()

    validator = Draft7Validator(
        schema,
        format_checker=FormatChecker()
    )

    errors = sorted(
        validator.iter_errors(data),
        key=lambda error: list(error.path)
    )

    if not errors:

        return {
            "valid": True,
            "errors": []
        }

    formatted_errors = []

    for error in errors:

        path = ".".join(
            str(item)
            for item in error.absolute_path
        )

        if not path:
            path = "root"

        formatted_errors.append(
            {
                "path": path,
                "message": error.message
            }
        )

    return {
        "valid": False,
        "errors": formatted_errors
    }


# ============================================================
# VALIDAÇÃO DE ARQUIVO JSON
# ============================================================

def validate_agent_output_file(file_path):

    path = Path(file_path)

    if not path.exists():
        return {
            "valid": False,
            "errors": [
                {
                    "path": "file",
                    "message": (
                        f"Arquivo não encontrado: {path}"
                    )
                }
            ]
        }

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

    except json.JSONDecodeError as error:

        return {
            "valid": False,
            "errors": [
                {
                    "path": "json",
                    "message": (
                        f"JSON inválido: {error}"
                    )
                }
            ]
        }

    return validate_agent_output(data)
