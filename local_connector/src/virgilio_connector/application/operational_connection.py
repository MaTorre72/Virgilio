"""Secure configuration of the installed Caronte-to-Virgilio connection."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlparse

from .credentials import (
    CredentialAlreadyExistsError,
    CredentialNotFoundError,
    CredentialStore,
    CredentialStoreError,
)


CONNECTION_SECTION = "virgilio_connection"
CONNECTION_CREDENTIAL = "VIRGILIO_TOKEN"


@dataclass(frozen=True, slots=True)
class OperationalConnectionSnapshot:
    configured: bool
    message: str
    endpoint_url: str = ""


class OperationalConnectionService:
    """Store the endpoint structurally and the access code in protected storage."""

    def __init__(self, config_path: Path, credentials: CredentialStore) -> None:
        self.config_path = Path(config_path)
        self.credentials = credentials

    def load(self) -> OperationalConnectionSnapshot:
        endpoint = _read_endpoint(self.config_path)
        if not endpoint:
            return OperationalConnectionSnapshot(
                False, "Collegamento a Virgilio non configurato."
            )
        try:
            self.credentials.read(CONNECTION_CREDENTIAL)
        except CredentialNotFoundError:
            return OperationalConnectionSnapshot(
                False, "Codice di collegamento mancante.", endpoint
            )
        except CredentialStoreError:
            return OperationalConnectionSnapshot(
                False, "Collegamento protetto non disponibile.", endpoint
            )
        return OperationalConnectionSnapshot(
            True, "Collegamento a Virgilio configurato.", endpoint
        )

    def configure(self, endpoint_url: str, access_code: str) -> OperationalConnectionSnapshot:
        endpoint = _validated_endpoint(endpoint_url)
        code = access_code.strip()
        previous_endpoint = _read_endpoint(self.config_path)
        try:
            previous_code = self.credentials.read(CONNECTION_CREDENTIAL)
        except CredentialNotFoundError:
            previous_code = None
        if not code and previous_code is None:
            raise ValueError("Inserisci la chiave di accesso del servizio.")
        if code:
            self._put_code(code, previous_code is not None)
        try:
            _write_endpoint(self.config_path, endpoint)
        except Exception:
            if code:
                self._restore_code(previous_code)
            if previous_endpoint:
                _write_endpoint(self.config_path, previous_endpoint)
            raise
        return OperationalConnectionSnapshot(
            True, "Collegamento a Virgilio configurato.", endpoint
        )

    def runtime_environment(self) -> dict[str, str]:
        snapshot = self.load()
        if not snapshot.configured:
            return {}
        code = self.credentials.read(CONNECTION_CREDENTIAL)
        return {
            "VIRGILIO_CARONTE_DRIVE_VERIFY_URL": snapshot.endpoint_url,
            "VIRGILIO_CARONTE_INTAKE_URL": snapshot.endpoint_url,
            "VIRGILIO_TOKEN": code,
        }

    def _put_code(self, code: str, exists: bool) -> None:
        if exists:
            self.credentials.update(CONNECTION_CREDENTIAL, code)
            return
        try:
            self.credentials.save(CONNECTION_CREDENTIAL, code)
        except CredentialAlreadyExistsError:
            self.credentials.update(CONNECTION_CREDENTIAL, code)

    def _restore_code(self, previous: str | None) -> None:
        if previous is not None:
            try:
                self.credentials.update(CONNECTION_CREDENTIAL, previous)
            except CredentialNotFoundError:
                self.credentials.save(CONNECTION_CREDENTIAL, previous)
            return
        try:
            self.credentials.delete(CONNECTION_CREDENTIAL)
        except CredentialNotFoundError:
            pass


def create_operational_connection_service(
    config_path: Path,
) -> OperationalConnectionService:
    from .windows_credentials import NativeWindowsCredentialApi, WindowsCredentialStore

    return OperationalConnectionService(
        config_path, WindowsCredentialStore(NativeWindowsCredentialApi())
    )


def _validated_endpoint(value: str) -> str:
    endpoint = value.strip()
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Inserisci un indirizzo di collegamento HTTPS valido.")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("L'indirizzo di collegamento non e` valido.")
    return endpoint


def _read_endpoint(path: Path) -> str:
    if not path.is_file():
        return ""
    active = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        text = raw.split("#", 1)[0].strip()
        if text == f"{CONNECTION_SECTION}:":
            active = True
            continue
        if active and raw[:1] not in {" ", "\t"}:
            break
        if active and text.startswith("endpoint_url:"):
            raw_value = text.split(":", 1)[1].strip()
            try:
                value = json.loads(raw_value)
            except json.JSONDecodeError:
                return ""
            return value.strip() if isinstance(value, str) else ""
    return ""


def _write_endpoint(path: Path, endpoint: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    section = re.search(
        rf"(?ms)^{re.escape(CONNECTION_SECTION)}:\s*\n"
        r"(?P<body>(?:^[ \t]+.*\n?)*)",
        text,
    )
    line = f"  endpoint_url: {json.dumps(endpoint)}\n"
    if section:
        body = section.group("body")
        if re.search(r"(?m)^[ \t]+endpoint_url:\s*.*$", body):
            body = re.sub(
                r"(?m)^[ \t]+endpoint_url:\s*.*$",
                line.rstrip(),
                body,
                count=1,
            )
            if not body.endswith("\n"):
                body += "\n"
        else:
            body = line + body
        text = text[:section.start("body")] + body + text[section.end("body"):]
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += f"{CONNECTION_SECTION}:\n{line}"
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
