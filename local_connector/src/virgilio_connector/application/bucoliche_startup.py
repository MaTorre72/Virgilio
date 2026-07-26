"""Guided Bucoliche and Windows background-start use cases."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import tempfile
from typing import Protocol

from ..bucoliche import EVENT_COLUMNS, BucolicheError, load_bucoliche_config
from .configuration import ConfigurationService
from .google_oauth import (
    GoogleOAuthConfigurationError,
    GoogleOAuthError,
    GoogleSheetsOAuthService,
    create_google_sheets_oauth_service,
)
from .registry_configuration import RegistryConfigurationService
from .operational_connection import (
    OperationalConnectionService,
    OperationalConnectionSnapshot,
)
from .credentials import CredentialStoreError
from .settings import SettingsValidationError
from .windows_startup import WindowsAutomaticControlAdapter


@dataclass(frozen=True, slots=True)
class GuidedStatus:
    ok: bool
    message: str


@dataclass(frozen=True, slots=True)
class BucolicheStartupSnapshot:
    register_configured: bool
    register_message: str
    automatic_control_installed: bool
    automatic_control_message: str
    connection_configured: bool = False
    connection_message: str = "Collegamento a Virgilio non configurato."
    connection_endpoint: str = ""


class BucolicheGateway(Protocol):
    def connect_google(self) -> GuidedStatus: ...
    def verify_register(self) -> GuidedStatus: ...


class AutomaticControlGateway(Protocol):
    def is_installed(self) -> bool: ...
    def install(self) -> None: ...
    def remove(self) -> None: ...


class ExistingBucolicheGateway:
    """Adapt the existing OAuth and read-only checks to user-facing outcomes."""

    def __init__(
        self,
        config_path: Path,
        sheets: GoogleSheetsOAuthService | None = None,
    ) -> None:
        self.config_path = Path(config_path)
        self.sheets = sheets or create_google_sheets_oauth_service()

    def connect_google(self) -> GuidedStatus:
        try:
            self.sheets.authorize()
        except GoogleOAuthConfigurationError:
            return GuidedStatus(
                False,
                "Collegamento Google non disponibile. Chiedi all'amministratore di completare la configurazione di Caronte.",
            )
        except (GoogleOAuthError, CredentialStoreError, OSError, PermissionError):
            return GuidedStatus(False, "Collegamento Google non completato. Riprova.")
        try:
            prepared = self._prepare_register()
        except Exception:
            return GuidedStatus(
                False,
                "Google collegato, ma il Registro non e` stato predisposto. "
                "Controlla di poter modificare il foglio.",
            )
        if not prepared:
            return GuidedStatus(
                False,
                "Google collegato, ma la struttura del Registro non e` compatibile.",
            )
        return GuidedStatus(True, "Google collegato. Registro pronto.")

    def verify_register(self) -> GuidedStatus:
        config = load_bucoliche_config(self.config_path)
        try:
            sheets = self.sheets.client(config.spreadsheet_id).inspect_sheets()
        except Exception:
            return GuidedStatus(
                False, "Registro non pronto. Completa prima il collegamento Google."
            )
        required = {config.events_sheet}
        if not required.issubset(sheets):
            return GuidedStatus(
                False,
                "Registro collegato, ma non ancora predisposto completamente.",
            )
        return GuidedStatus(True, "Registro verificato e pronto.")

    def _prepare_register(self) -> bool:
        config = load_bucoliche_config(self.config_path)
        client = self.sheets.client(config.spreadsheet_id)
        existing = client.inspect_sheets()
        definitions = ((config.events_sheet, EVENT_COLUMNS),)
        for name, columns in definitions:
            header = tuple(existing.get(name, ()))
            if header and header[: len(columns)] != tuple(columns):
                return False
        for name, columns in definitions:
            header = tuple(existing.get(name, ()))
            if name not in existing:
                client.create_sheet(name)
                client.write_header(name, columns)
            elif not header:
                client.write_header(name, columns)
        return True


class WindowsAutomaticControlGateway:
    """Use the current-user Windows Run key behind an injectable port."""

    def __init__(
        self,
        configuration: ConfigurationService,
        *,
        registry: object | None = None,
        executable: Path | None = None,
        frozen: bool | None = None,
    ) -> None:
        self.configuration = configuration
        self.registry = registry
        self.executable = executable
        self.frozen = frozen

    def _adapter(self) -> WindowsAutomaticControlAdapter:
        model = self.configuration.load()
        return WindowsAutomaticControlAdapter(
            self.configuration.store.source,
            model.preferences.interval_seconds,
            registry=self.registry,
            executable=self.executable,
            frozen=self.frozen,
        )

    def is_installed(self) -> bool:
        return self._adapter().is_installed()

    def install(self) -> None:
        self._adapter().install()

    def remove(self) -> None:
        self._adapter().remove()


class BucolicheStartupService:
    """Coordinate the guided view without exposing adapter details."""

    def __init__(
        self,
        configuration: ConfigurationService,
        bucoliche: BucolicheGateway,
        automatic_control: AutomaticControlGateway,
        operational_connection: OperationalConnectionService | None = None,
    ) -> None:
        self.configuration = configuration
        self.registry_configuration = RegistryConfigurationService(
            configuration.store.source
        )
        self.registry_configuration.ensure_enabled()
        self.bucoliche = bucoliche
        self.automatic_control = automatic_control
        self.operational_connection = operational_connection

    def load(self) -> BucolicheStartupSnapshot:
        register = self.registry_configuration.load()
        try:
            installed = self.automatic_control.is_installed()
            message = (
                "Controllo automatico attivo."
                if installed else "Controllo automatico non attivo."
            )
        except (OSError, SettingsValidationError):
            installed = False
            message = "Stato del controllo automatico non disponibile."
        connection = (
            self.operational_connection.load()
            if self.operational_connection is not None
            else OperationalConnectionSnapshot(
                False, "Collegamento a Virgilio non configurato."
            )
        )
        return BucolicheStartupSnapshot(
            register.configured,
            register.message,
            installed,
            message,
            connection.configured,
            connection.message,
            connection.endpoint_url,
        )

    def configure_operational_connection(
        self, endpoint_url: str, access_code: str
    ) -> GuidedStatus:
        if self.operational_connection is None:
            return GuidedStatus(
                False, "Configurazione non disponibile. Chiedi assistenza."
            )
        try:
            result = self.operational_connection.configure(endpoint_url, access_code)
        except (ValueError, CredentialStoreError, OSError) as exc:
            message = str(exc)
            if not message.startswith(("Inserisci ", "L'indirizzo ")):
                message = "Collegamento non salvato. Riprova o chiedi assistenza."
            return GuidedStatus(False, message)
        return GuidedStatus(True, result.message)

    def set_bucoliche_enabled(self, enabled: bool) -> GuidedStatus:
        _write_bucoliche_enabled(self.configuration.store.source, enabled)
        return GuidedStatus(
            True,
            "Bucoliche attivato." if enabled else "Bucoliche disattivato.",
        )

    def connect_google(self) -> GuidedStatus:
        if not self.registry_configuration.load().configured:
            return GuidedStatus(
                False,
                "Registro non ancora configurato dall'amministratore. Chiedi di configurarlo.",
            )
        try:
            result = self.bucoliche.connect_google()
            if result.ok:
                return result
            if result.message == (
                "Collegamento Google non disponibile. Chiedi all'amministratore di "
                "completare la configurazione di Caronte."
            ):
                return result
            return GuidedStatus(False, "Collegamento Google non completato. Riprova.")
        except (BucolicheError, OSError):
            return GuidedStatus(
                False, "Collegamento Google non completato. Riprova."
            )

    def verify_register(self) -> GuidedStatus:
        if not self.registry_configuration.load().configured:
            return GuidedStatus(
                False, "Registro non ancora configurato dall'amministratore."
            )
        try:
            return self.bucoliche.verify_register()
        except (BucolicheError, OSError):
            return GuidedStatus(
                False, "Registro non pronto. Completa prima il collegamento Google."
            )

    def install_automatic_control(self) -> GuidedStatus:
        try:
            self.automatic_control.install()
        except (OSError, SettingsValidationError):
            return GuidedStatus(False, "Attivazione non riuscita. Riprova da Windows.")
        return GuidedStatus(True, "Controllo automatico attivato.")

    def remove_automatic_control(self) -> GuidedStatus:
        try:
            self.automatic_control.remove()
        except (OSError, SettingsValidationError):
            return GuidedStatus(False, "Rimozione non riuscita. Riprova da Windows.")
        return GuidedStatus(True, "Controllo automatico rimosso.")


def _write_bucoliche_enabled(path: Path, enabled: bool) -> None:
    """Update only Bucoliche.enabled and preserve every other YAML section."""

    text = path.read_text(encoding="utf-8")
    value = "true" if enabled else "false"
    section = re.search(r"(?ms)^bucoliche:\s*\n(?P<body>(?:^[ \t]+.*\n?)*)", text)
    if section:
        body = section.group("body")
        if re.search(r"(?m)^[ \t]+enabled:\s*.*$", body):
            updated = re.sub(
                r"(?m)^([ \t]+enabled:)\s*.*$", rf"\1 {value}", body, count=1
            )
        else:
            updated = f"  enabled: {value}\n" + body
        text = text[:section.start("body")] + updated + text[section.end("body"):]
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += (
            "bucoliche:\n"
            f"  enabled: {value}\n"
            "  adapter: google_sheets_append_only\n"
            "  credentials_mode: user_oauth_local\n"
            "  append_only: true\n"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        temporary.write_text(text, encoding="utf-8", newline="\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
