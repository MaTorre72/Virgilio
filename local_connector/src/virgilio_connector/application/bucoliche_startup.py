"""Guided Bucoliche and Windows background-start use cases."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Protocol

from ..bucoliche import BucolicheError, GoogleOAuthLogin, load_bucoliche_config
from ..pilot_readiness import BucolicheDoctor, has_bucoliche_section
from ..windows_task import (
    WindowsTaskError,
    build_windows_watch_task,
    query_windows_watch_task,
    register_windows_watch_task,
    unregister_windows_watch_task,
)
from .configuration import ConfigurationService


@dataclass(frozen=True, slots=True)
class GuidedStatus:
    ok: bool
    message: str


@dataclass(frozen=True, slots=True)
class BucolicheStartupSnapshot:
    bucoliche_enabled: bool
    automatic_control_installed: bool
    automatic_control_message: str


class BucolicheGateway(Protocol):
    def connect_google(self) -> GuidedStatus: ...
    def verify_register(self) -> GuidedStatus: ...


class AutomaticControlGateway(Protocol):
    def is_installed(self) -> bool: ...
    def install(self) -> None: ...
    def remove(self) -> None: ...


class ExistingBucolicheGateway:
    """Adapt the existing OAuth and read-only checks to user-facing outcomes."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = Path(config_path)

    def connect_google(self) -> GuidedStatus:
        result = GoogleOAuthLogin(load_bucoliche_config(self.config_path)).run()
        if result.status in {"token_created", "token_refreshed"}:
            return GuidedStatus(True, "Collegamento Google completato.")
        return GuidedStatus(False, "Collegamento non completato. Controlla il file Google scelto.")

    def verify_register(self) -> GuidedStatus:
        config = load_bucoliche_config(self.config_path)
        result = BucolicheDoctor(
            config,
            config_has_section=has_bucoliche_section(self.config_path),
        ).run()
        if result.status == "READY":
            return GuidedStatus(True, "Registro verificato e pronto.")
        return GuidedStatus(False, "Registro non pronto. Completa prima il collegamento Google.")


class WindowsAutomaticControlGateway:
    """Use the existing Task Scheduler functions behind an injectable port."""

    TASK_NAME = "Caronte - controllo automatico"

    def __init__(self, configuration: ConfigurationService) -> None:
        self.configuration = configuration

    def is_installed(self) -> bool:
        return query_windows_watch_task(self.TASK_NAME).installed

    def install(self) -> None:
        model = self.configuration.load()
        repo_root = Path(__file__).resolve().parents[4]
        plan = build_windows_watch_task(
            config_path=self.configuration.store.source,
            python_exe=Path(sys.executable),
            repo_root=repo_root,
            interval_seconds=model.preferences.interval_seconds,
            task_name=self.TASK_NAME,
            force=True,
        )
        register_windows_watch_task(plan)

    def remove(self) -> None:
        unregister_windows_watch_task(self.TASK_NAME)


class BucolicheStartupService:
    """Coordinate the guided view without exposing adapter details."""

    def __init__(
        self,
        configuration: ConfigurationService,
        bucoliche: BucolicheGateway,
        automatic_control: AutomaticControlGateway,
    ) -> None:
        self.configuration = configuration
        self.bucoliche = bucoliche
        self.automatic_control = automatic_control

    def load(self) -> BucolicheStartupSnapshot:
        enabled = load_bucoliche_config(self.configuration.store.source).enabled
        try:
            installed = self.automatic_control.is_installed()
            message = (
                "Controllo automatico attivo."
                if installed else "Controllo automatico non attivo."
            )
        except (OSError, WindowsTaskError):
            installed = False
            message = "Stato del controllo automatico non disponibile."
        return BucolicheStartupSnapshot(enabled, installed, message)

    def set_bucoliche_enabled(self, enabled: bool) -> GuidedStatus:
        _write_bucoliche_enabled(self.configuration.store.source, enabled)
        return GuidedStatus(
            True,
            "Bucoliche attivato." if enabled else "Bucoliche disattivato.",
        )

    def connect_google(self) -> GuidedStatus:
        try:
            return self.bucoliche.connect_google()
        except (BucolicheError, OSError):
            return GuidedStatus(
                False, "Collegamento non completato. Controlla il file Google scelto."
            )

    def verify_register(self) -> GuidedStatus:
        try:
            return self.bucoliche.verify_register()
        except (BucolicheError, OSError):
            return GuidedStatus(
                False, "Registro non pronto. Completa prima il collegamento Google."
            )

    def install_automatic_control(self) -> GuidedStatus:
        try:
            self.automatic_control.install()
        except (OSError, WindowsTaskError):
            return GuidedStatus(False, "Attivazione non riuscita. Riprova da Windows.")
        return GuidedStatus(True, "Controllo automatico attivato.")

    def remove_automatic_control(self) -> GuidedStatus:
        try:
            self.automatic_control.remove()
        except (OSError, WindowsTaskError):
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
