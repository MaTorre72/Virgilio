"""Parser for the constrained YAML subset used by local configuration."""

from __future__ import annotations

from pathlib import Path


class LocalConfigYamlError(ValueError):
    """Raised when the constrained local YAML syntax is invalid."""


def parse_local_config_yaml(
    path: Path,
) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    if not path.is_file():
        raise LocalConfigYamlError(f"configuration file not found: {path}")
    accounts: list[dict[str, object]] = []
    storage: dict[str, object] | None = None
    current: dict[str, object] | None = None
    section: str | None = None
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        is_top_level_section = not line[:1].isspace() and stripped.endswith(":")
        if is_top_level_section and stripped == "accounts:":
            if current is not None:
                accounts.append(current)
                current = None
            section = "accounts"
            continue
        if is_top_level_section and stripped == "storage:":
            if current is not None:
                accounts.append(current)
                current = None
            section = "storage"
            storage = {}
            continue
        if is_top_level_section:
            if current is not None:
                accounts.append(current)
                current = None
            section = "ignored"
            continue
        if section is None:
            raise LocalConfigYamlError(
                f"unsupported content before a section at line {line_number}"
            )
        if section == "ignored":
            continue
        if section == "accounts" and stripped.startswith("- "):
            if current is not None:
                accounts.append(current)
            current = {}
            stripped = stripped[2:].strip()
            if stripped:
                key, value = _split_key_value(stripped, line_number)
                current[key] = _parse_scalar(value)
            continue
        if section == "storage":
            if storage is None:
                storage = {}
            key, value = _split_key_value(stripped, line_number)
            storage[key] = _parse_scalar(value)
            continue
        if current is None:
            raise LocalConfigYamlError(f"account item expected at line {line_number}")
        key, value = _split_key_value(stripped, line_number)
        current[key] = _parse_scalar(value)
    if current is not None:
        accounts.append(current)
    return accounts, storage


def _split_key_value(text: str, line_number: int) -> tuple[str, str]:
    if ":" not in text:
        raise LocalConfigYamlError(f"expected key: value at line {line_number}")
    key, value = text.split(":", 1)
    key = key.strip()
    if not key:
        raise LocalConfigYamlError(f"empty key at line {line_number}")
    return key, value.strip()


def _parse_scalar(value: str) -> object:
    value = value.strip()
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
        return value[1:-1]
    if value.isdigit():
        return int(value)
    return value
