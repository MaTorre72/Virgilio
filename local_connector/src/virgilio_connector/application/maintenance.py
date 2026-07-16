"""Application services for the separate Caronte maintenance presentation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shutil
import sqlite3
from typing import Any, Callable, Mapping
import uuid

from ..reset_local_state import reset_local_state
from ..state_db import StateStore
from ..time_utils import rome_isoformat, rome_timestamp


@dataclass(frozen=True, slots=True)
class BackupResult:
    status: str
    backup_path: Path | None
    files_copied: int
    message: str


@dataclass(frozen=True, slots=True)
class IntegrityResult:
    status: str
    database_present: bool
    message: str


@dataclass(frozen=True, slots=True)
class DiagnosticReportResult:
    report_path: Path
    message: str


@dataclass(frozen=True, slots=True)
class MaintenanceResetResult:
    status: str
    backup_path: Path | None
    message: str


class MaintenanceService:
    """Coordinate local maintenance without depending on a presentation toolkit."""

    _SENSITIVE_KEYS = ("password", "secret", "token", "credential")

    def __init__(
        self,
        data_root: str | Path,
        *,
        details_provider: Callable[[], Mapping[str, Any]] = lambda: {},
        redact: Callable[[str], str] = lambda value: value,
    ) -> None:
        self.data_root = Path(data_root)
        self._details_provider = details_provider
        self._redact = redact

    def create_backup(self) -> BackupResult:
        if not self.data_root.exists():
            return BackupResult("noop", None, 0, "Nessun dato locale da salvare.")
        if not self.data_root.is_dir():
            raise ValueError("La cartella dati locale non e` valida.")

        target = self._backup_path()
        shutil.copytree(self.data_root, target)
        files_copied = sum(1 for item in target.rglob("*") if item.is_file())
        return BackupResult(
            "completed", target, files_copied,
            f"Backup completato: {files_copied} file salvati.",
        )

    def verify_integrity(self) -> IntegrityResult:
        database = self.data_root / "state.db"
        if not database.is_file():
            return IntegrityResult("missing", False, "Archivio locale non ancora presente.")
        try:
            valid = StateStore(database).integrity_check()
        except (sqlite3.DatabaseError, OSError):
            valid = False
        if valid:
            return IntegrityResult("valid", True, "Integrita` verificata.")
        return IntegrityResult("corrupt", True, "Integrita` non valida: usa il backup prima del reset.")

    def create_diagnostic_report(self) -> DiagnosticReportResult:
        integrity = self.verify_integrity()
        payload = {
            "application": "Caronte Manutenzione",
            "generated_at": rome_isoformat(),
            "data_root_present": self.data_root.is_dir(),
            "integrity": asdict(integrity),
            "details": self._sanitize(self._details_provider()),
        }
        reports = self.data_root / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        target = reports / f"diagnostic_{rome_timestamp()}_{uuid.uuid4().hex[:8]}.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(target)
        return DiagnosticReportResult(target, "Report diagnostico creato.")

    def reset(self, *, confirmed: bool) -> MaintenanceResetResult:
        if not confirmed:
            return MaintenanceResetResult(
                "cancelled", None, "Reset annullato: serve la conferma esplicita.",
            )
        result = reset_local_state(self.data_root, backup=True, confirm=True)
        return MaintenanceResetResult(
            result.status,
            Path(result.backup_path) if result.backup_path else None,
            "Reset completato con backup verificabile."
            if result.backup_path else "Nessun dato locale da azzerare.",
        )

    def _sanitize(self, value: Any, *, key: str = "") -> Any:
        if any(marker in key.lower() for marker in self._SENSITIVE_KEYS):
            return "<redacted>"
        if isinstance(value, Mapping):
            return {str(item_key): self._sanitize(item, key=str(item_key)) for item_key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._sanitize(item) for item in value]
        if isinstance(value, str):
            return self._redact(value)
        if value is None or isinstance(value, (bool, int, float)):
            return value
        return self._redact(str(value))

    def _backup_path(self) -> Path:
        return self.data_root.parent / (
            f"{self.data_root.name}.backup-{rome_timestamp()}-{uuid.uuid4().hex[:8]}"
        )
