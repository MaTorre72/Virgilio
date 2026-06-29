"""Read-only readiness checks for Bucoliche and a controlled local pilot."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import sqlite3
from typing import Callable, Mapping

from .bucoliche import (BucolicheConfig, BucolicheError, CONFLICT_COLUMNS,
                        EVENT_COLUMNS, GoogleSheetsAppendClient)
from .local_paths import LocalDataPaths
from .multi_account import LocalImapAccount, LocalStorageConfig
from .traceability import load_rules


@dataclass(frozen=True, slots=True)
class ReadinessResult:
    status: str
    checks: tuple[dict[str, str], ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    suggested_next_commands: tuple[str, ...] = ()

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))


class BucolicheDoctor:
    def __init__(self, config: BucolicheConfig, *, config_has_section: bool,
                 environ: Mapping[str, str] | None = None,
                 client_factory: Callable[[str, str], object] | None = None) -> None:
        self.config, self.config_has_section = config, config_has_section
        self.environ = os.environ if environ is None else environ
        self.client_factory = client_factory or GoogleSheetsAppendClient

    def run(self) -> ReadinessResult:
        checks, errors, warnings = [], [], []
        if not self.config_has_section:
            errors.append("bucoliche section missing")
        checks.append(_check("config_section", self.config_has_section))
        try: self.config.validate(); checks.append(_check("adapter", True))
        except BucolicheError as exc: errors.append(str(exc)); checks.append(_check("adapter", False))
        if not self.config.enabled:
            warnings.append("Bucoliche adapter disabled; real export remains blocked")
        checks.append({"name": "enabled", "status": str(self.config.enabled).upper()})
        spreadsheet_id = self.environ.get(self.config.spreadsheet_id_env, "").strip()
        credentials_json = self.environ.get(self.config.service_account_json_env, "")
        if not spreadsheet_id: errors.append(f"missing env: {self.config.spreadsheet_id_env}")
        if not credentials_json: errors.append(f"missing env: {self.config.service_account_json_env}")
        checks.extend((_check("spreadsheet_env", bool(spreadsheet_id)),
                       _check("service_account_env", bool(credentials_json))))
        if credentials_json:
            try:
                parsed = json.loads(credentials_json)
                if not isinstance(parsed, dict): raise ValueError
                checks.append(_check("service_account_json", True))
            except (ValueError, TypeError, json.JSONDecodeError):
                errors.append("service account JSON is invalid")
                checks.append(_check("service_account_json", False))
        if not errors:
            try:
                client = self.client_factory(spreadsheet_id, credentials_json)
                sheets = client.inspect_sheets()
                checks.append(_check("spreadsheet_read", True))
                self._check_sheets(sheets, checks, errors, warnings)
            except Exception as exc:
                errors.append(f"spreadsheet read failed: {type(exc).__name__}")
                checks.append(_check("spreadsheet_read", False))
        warnings.append("append capability not verified in read-only doctor")
        return _result(checks, errors, warnings)

    def _check_sheets(self, sheets, checks, errors, warnings):
        required = ((self.config.events_sheet, EVENT_COLUMNS),
                    (self.config.conflicts_sheet, CONFLICT_COLUMNS))
        for name, expected in required:
            if name not in sheets:
                errors.append(f"required sheet missing: {name}")
                checks.append(_check(f"sheet:{name}", False)); continue
            checks.append(_check(f"sheet:{name}", True))
            header = tuple(sheets[name])
            if not header:
                warnings.append(f"header absent: {name}")
            elif header[:len(expected)] != tuple(expected):
                errors.append(f"header mismatch: {name}")
        if self.config.state_sheet not in sheets:
            warnings.append(f"optional sheet missing: {self.config.state_sheet}")


class PilotCheck:
    COMMANDS = (
        "python -m virgilio_connector doctor-bucoliche --config accounts.local.yaml",
        "python -m virgilio_connector scan-imap-accounts --config accounts.local.yaml --dry-run",
        "python -m virgilio_connector run-local-pipeline --config accounts.local.yaml --dry-run",
        "python -m virgilio_connector run-local-pipeline --config accounts.local.yaml",
        "python -m virgilio_connector export-to-bucoliche --config accounts.local.yaml --dry-run",
        "python -m virgilio_connector export-to-bucoliche --config accounts.local.yaml",
    )

    def __init__(self, accounts: tuple[LocalImapAccount, ...], *, storage: LocalStorageConfig,
                 bucoliche: BucolicheConfig, config_path: Path, paths: LocalDataPaths,
                 environ: Mapping[str, str] | None = None) -> None:
        self.accounts, self.storage, self.bucoliche = accounts, storage, bucoliche
        self.config_path, self.paths = config_path, paths
        self.environ = os.environ if environ is None else environ

    def run(self) -> ReadinessResult:
        checks, errors, warnings = [], [], []
        enabled = [account for account in self.accounts if account.enabled]
        checks.append(_check("enabled_accounts", bool(enabled)))
        if not enabled: errors.append("no enabled account configured")
        for account in enabled:
            if not self.environ.get(account.username_env): errors.append(f"{account.account_alias}: username env missing")
            if not self.environ.get(account.password_env): errors.append(f"{account.account_alias}: password env missing")
            if account.ack_enabled: warnings.append(f"{account.account_alias}: ack_enabled=true; disable for first pilot")
        checks.append(_check("imap_env", not any("env missing" in item for item in errors)))
        staging = self.storage.staging_dir
        storage_ok = bool(staging and staging.is_dir() and os.access(staging, os.W_OK))
        checks.append(_check("storage", storage_ok))
        if not storage_ok: errors.append("storage staging_dir missing or not writable")
        db_ok = self._sqlite_readable()
        checks.append(_check("sqlite", db_ok))
        if not db_ok: errors.append("SQLite missing or not readable")
        machine_ok = (self.paths.root / "machine_id").is_file()
        checks.append(_check("machine_id", machine_ok))
        if not machine_ok: errors.append("machine_id missing; run doctor or pipeline setup first")
        try: load_rules(self.config_path); checks.append(_check("rules", True))
        except Exception: errors.append("rules configuration invalid"); checks.append(_check("rules", False))
        if not self.bucoliche.enabled:
            warnings.append("Bucoliche disabled; local pilot can run but central export cannot")
        else:
            try:
                self.bucoliche.validate()
                if not self.environ.get(self.bucoliche.spreadsheet_id_env):
                    raise BucolicheError("spreadsheet env missing")
                if not self.environ.get(self.bucoliche.service_account_json_env):
                    raise BucolicheError("service account env missing")
                checks.append(_check("bucoliche", True))
            except BucolicheError: errors.append("Bucoliche configuration invalid"); checks.append(_check("bucoliche", False))
        if db_ok and not self._has_events():
            warnings.append("no central events yet; dry-run scan can verify available messages")
        return _result(checks, errors, warnings, self.COMMANDS)

    def _sqlite_readable(self) -> bool:
        if not self.paths.state_db.is_file(): return False
        try:
            with sqlite3.connect(f"{self.paths.state_db.resolve().as_uri()}?mode=ro", uri=True) as db:
                db.execute("SELECT 1").fetchone()
            return True
        except sqlite3.Error: return False

    def _has_events(self) -> bool:
        try:
            with sqlite3.connect(f"{self.paths.state_db.resolve().as_uri()}?mode=ro", uri=True) as db:
                return db.execute("SELECT 1 FROM audit_events LIMIT 1").fetchone() is not None
        except sqlite3.Error: return False


def has_bucoliche_section(path: Path) -> bool:
    return any(line.strip() == "bucoliche:" for line in path.read_text(encoding="utf-8").splitlines())


def _check(name: str, ok: bool) -> dict[str, str]:
    return {"name": name, "status": "OK" if ok else "MISSING"}


def _result(checks, errors, warnings, commands=()) -> ReadinessResult:
    status = "BLOCKED" if errors else "READY_WITH_WARNINGS" if warnings else "READY"
    return ReadinessResult(status, tuple(checks), tuple(errors), tuple(warnings), tuple(commands))
