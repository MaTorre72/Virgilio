"""Administrative selection of the shared activity register."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import tempfile


@dataclass(frozen=True, slots=True)
class RegistryConfigurationStatus:
    configured: bool
    message: str
    spreadsheet_id: str = ""


class RegistryConfigurationService:
    """Persist one administrator-selected Google Sheet per installation."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = Path(config_path)

    def load(self) -> RegistryConfigurationStatus:
        identifier = _read_spreadsheet_id(self.config_path)
        if identifier:
            return RegistryConfigurationStatus(
                True, "Registro configurato dall'amministratore.", identifier
            )
        return RegistryConfigurationStatus(
            False, "Registro non ancora configurato dall'amministratore."
        )

    def select_register(self, reference: str) -> RegistryConfigurationStatus:
        identifier = _extract_spreadsheet_id(reference)
        if not identifier:
            return RegistryConfigurationStatus(
                False, "Inserisci l'indirizzo del Registro Google scelto dall'amministratore."
            )
        _write_spreadsheet_id(self.config_path, identifier)
        return RegistryConfigurationStatus(
            True, "Registro configurato dall'amministratore.", identifier
        )

    def ensure_enabled(self) -> None:
        """Migrate an already selected Register to the operational enabled state."""

        identifier = _read_spreadsheet_id(self.config_path)
        if identifier and not _read_enabled(self.config_path):
            _write_spreadsheet_id(self.config_path, identifier)


def _extract_spreadsheet_id(reference: str) -> str:
    value = reference.strip()
    match = re.search(r"docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]{20,})", value)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{20,}", value):
        return value
    return ""


def _read_spreadsheet_id(path: Path) -> str:
    if not path.is_file():
        return ""
    active = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        text = raw.split("#", 1)[0].strip()
        if text == "bucoliche:":
            active = True
            continue
        if active and raw[:1] not in {" ", "\t"}:
            break
        if active and text.startswith("spreadsheet_id:"):
            return text.split(":", 1)[1].strip().strip("'\"")
    return ""


def _read_enabled(path: Path) -> bool:
    if not path.is_file():
        return False
    active = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        text = raw.split("#", 1)[0].strip()
        if text == "bucoliche:":
            active = True
            continue
        if active and raw[:1] not in {" ", "\t"}:
            break
        if active and text.startswith("enabled:"):
            return text.split(":", 1)[1].strip().casefold() == "true"
    return False


def _write_spreadsheet_id(path: Path, identifier: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    section = re.search(r"(?ms)^bucoliche:\s*\n(?P<body>(?:^[ \t]+.*\n?)*)", text)
    line = f"  spreadsheet_id: {json.dumps(identifier)}\n"
    if section:
        body = section.group("body")
        if re.search(r"(?m)^[ \t]+spreadsheet_id:\s*.*$", body):
            body = re.sub(r"(?m)^[ \t]+spreadsheet_id:\s*.*$", line.rstrip(), body, count=1)
            if not body.endswith("\n"):
                body += "\n"
        else:
            body = line + body
        if re.search(r"(?m)^[ \t]+enabled:\s*.*$", body):
            body = re.sub(
                r"(?m)^([ \t]+enabled:)\s*.*$",
                r"\1 true",
                body,
                count=1,
            )
        else:
            body = "  enabled: true\n" + body
        text = text[:section.start("body")] + body + text[section.end("body"):]
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += "bucoliche:\n  enabled: true\n" + line
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(text, encoding="utf-8", newline="\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
