# ============================================================
# INVESTMENT CIO AGENT
# tests/test_infrastructure.py
# ============================================================

from datetime import datetime, timezone

from config import validate_config
from agents.validator import (
    load_schema,
    validate_agent_output,
)


def main():

    print("=" * 70)
    print("INVESTMENT CIO AGENT — TESTE DE INFRAESTRUTURA")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. CONFIG
    # --------------------------------------------------------

    assert validate_config() is True

    print("CONFIG: OK")

    # --------------------------------------------------------
    # 2. SCHEMA
    # --------------------------------------------------------

    schema = load_schema()

    assert isinstance(schema, dict)
    assert schema.get("type") == "object"

    print("SCHEMA: OK")

    # --------------------------------------------------------
    # 3. TESTE COM DADO VÁLIDO
    # --------------------------------------------------------

    valid_output = {

        "schema_version": "1.0",

        "system_id": "sp500_cycle",

        "system_name": "SP500_CYCLE_ATLAS",

        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "status": "OK",

        "decision": {
            "signal": "HOLD",
            "confidence": 0.92,
            "summary": "Teste de infraestrutura."
        },

        "metrics": {
            "drawdown": -0.10,
            "cape": 35.0
        },

        "risk": {
            "level": "MODERATE",
            "score": 40.0,
            "alerts": []
        },

        "data_quality": {
            "score": 95.0,
            "missing_fields": [],
            "warnings": []
        },

        "positions": [],

        "opportunities": [],

        "audit": {},

        "metadata": {}
    }

    result = validate_agent_output(
        valid_output
    )

    assert result["valid"] is True, result["errors"]

    print("VALIDATOR: OK")
    print("TESTE VÁLIDO: PASSOU")

    # --------------------------------------------------------
    # 4. TESTE COM DADO INVÁLIDO
    # --------------------------------------------------------

    invalid_output = {
        "system_name": "ROBO_INVALIDO"
    }

    result_invalid = validate_agent_output(
        invalid_output
    )

    assert result_invalid["valid"] is False

    print(
        "TESTE INVÁLIDO: REJEITADO CORRETAMENTE"
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "INVESTMENT CIO AGENT — "
        "INFRAESTRUTURA BASE OK"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
