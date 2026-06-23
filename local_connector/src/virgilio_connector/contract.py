"""JSON serialization helpers for the connector/Caronte contract."""

from __future__ import annotations

import json
from typing import Any

from .models import CaronteCommand, CaronteResponse, ContractValidationError


def _load_json_object(payload: str | bytes | bytearray) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ContractValidationError("payload must be valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ContractValidationError("payload root must be an object")
    return value


def command_from_json(payload: str | bytes | bytearray) -> CaronteCommand:
    return CaronteCommand.from_mapping(_load_json_object(payload))


def response_from_json(payload: str | bytes | bytearray) -> CaronteResponse:
    return CaronteResponse.from_mapping(_load_json_object(payload))


def command_to_json(command: CaronteCommand, *, indent: int | None = None) -> str:
    return json.dumps(
        command.to_dict(),
        ensure_ascii=False,
        indent=indent,
        separators=None if indent is not None else (",", ":"),
    )


def response_to_json(response: CaronteResponse, *, indent: int | None = None) -> str:
    return json.dumps(
        response.to_dict(),
        ensure_ascii=False,
        indent=indent,
        separators=None if indent is not None else (",", ":"),
    )
