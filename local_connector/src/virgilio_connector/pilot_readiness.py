"""Read-only readiness checks for Bucoliche and a controlled local pilot."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import sqlite3
from typing import Callable, Mapping

from .bucoliche import (BucolicheConfig, BucolicheError, CONFLICT_COLUMNS,
                        EVENT_COLUMNS, STATE_COLUMNS, BucolicheAppendOnlyAdapter,
                        GoogleSheetsAppendClient,
                        build_google_sheets_client)
from .local_paths import LocalDataPaths
from .multi_account import LocalImapAccount, LocalStorageConfig
from .pipeline import LocalPipelineRunner
from .traceability import load_rules
from .traceability import central_event_rows
from .readonly_state import ensure_state_db


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
        self.client_factory = client_factory

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
        if not spreadsheet_id: errors.append(f"missing env: {self.config.spreadsheet_id_env}")
        checks.append(_check("spreadsheet_env", bool(spreadsheet_id)))
        credential_value = self._check_credentials(checks, errors)
        if not errors:
            try:
                client = (self.client_factory(spreadsheet_id, credential_value)
                          if self.client_factory else
                          build_google_sheets_client(self.config, self.environ))
                sheets = client.inspect_sheets()
                checks.append(_check("spreadsheet_read", True))
                self._check_sheets(sheets, checks, errors, warnings)
            except Exception as exc:
                errors.append(f"spreadsheet read failed: {type(exc).__name__}")
                checks.append(_check("spreadsheet_read", False))
        warnings.append("append capability not verified in read-only doctor")
        return _result(checks, errors, warnings)

    def _check_credentials(self, checks, errors):
        if self.config.credentials_mode == "service_account_json_env":
            value = self.environ.get(self.config.service_account_json_env, "")
            if not value: errors.append(f"missing env: {self.config.service_account_json_env}")
            checks.append(_check("service_account_env", bool(value)))
            if value:
                try:
                    if not isinstance(json.loads(value), dict): raise ValueError
                    checks.append(_check("service_account_json", True))
                except (ValueError, TypeError, json.JSONDecodeError):
                    errors.append("service account JSON is invalid")
                    checks.append(_check("service_account_json", False))
            return value
        client_value = self.environ.get(self.config.oauth_client_secrets_path_env, "").strip()
        token_value = self.environ.get(self.config.oauth_token_path_env, "").strip()
        client_path, token_path = Path(client_value), Path(token_value)
        if not client_value: errors.append(f"missing env: {self.config.oauth_client_secrets_path_env}")
        elif not client_path.is_file(): errors.append("OAuth client secret file missing")
        else:
            try:
                if not isinstance(json.loads(client_path.read_text(encoding="utf-8")), dict): raise ValueError
            except (OSError, ValueError, json.JSONDecodeError): errors.append("OAuth client secret JSON invalid")
        if not token_value: errors.append(f"missing env: {self.config.oauth_token_path_env}")
        elif not token_path.is_file(): errors.append("OAuth token missing; run google-oauth-login")
        checks.extend((_check("oauth_client_secret", bool(client_value) and client_path.is_file()),
                       _check("oauth_token", bool(token_value) and token_path.is_file())))
        return token_value

    def _check_sheets(self, sheets, checks, errors, warnings):
        required = ((self.config.events_sheet, EVENT_COLUMNS),
                    (self.config.conflicts_sheet, CONFLICT_COLUMNS))
        for name, expected in required:
            if name not in sheets:
                warnings.append(f"sheet missing: {name}; run setup-bucoliche-test-sheet")
                checks.append(_check(f"sheet:{name}", False)); continue
            checks.append(_check(f"sheet:{name}", True))
            self._check_header(name, tuple(sheets[name]), expected, errors, warnings)
        if self.config.state_sheet not in sheets:
            warnings.append(f"optional sheet missing: {self.config.state_sheet}")
        else:
            self._check_header(self.config.state_sheet, tuple(sheets[self.config.state_sheet]),
                               STATE_COLUMNS, errors, warnings)

    @staticmethod
    def _check_header(name, header, expected, errors, warnings):
        if not header:
            warnings.append(f"header absent: {name}")
        elif header[:len(expected)] != tuple(expected):
            errors.append(f"header mismatch: {name}")
        elif len(header) > len(expected):
            warnings.append(f"extra header columns: {name}")


@dataclass(frozen=True, slots=True)
class SheetSetupResult:
    status: str
    dry_run: bool
    actions: tuple[dict[str, str], ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_json(self):
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))


class BucolicheSheetSetup:
    def __init__(self, config: BucolicheConfig, *, environ: Mapping[str, str] | None = None,
                 client_factory: Callable[[str, str], object] | None = None) -> None:
        self.config = config
        self.environ = os.environ if environ is None else environ
        self.client_factory = client_factory

    def run(self, *, dry_run: bool) -> SheetSetupResult:
        errors, warnings = [], []
        spreadsheet_id = self.environ.get(self.config.spreadsheet_id_env, "").strip()
        try: self.config.validate()
        except BucolicheError as exc: errors.append(str(exc))
        if not spreadsheet_id: errors.append(f"missing env: {self.config.spreadsheet_id_env}")
        credential_value = ""
        if self.config.credentials_mode == "service_account_json_env":
            credential_value = self.environ.get(self.config.service_account_json_env, "")
            if not credential_value: errors.append(f"missing env: {self.config.service_account_json_env}")
            else:
                try:
                    if not isinstance(json.loads(credential_value), dict): raise ValueError
                except (ValueError, TypeError, json.JSONDecodeError):
                    errors.append("service account JSON is invalid")
        else:
            client_value = self.environ.get(self.config.oauth_client_secrets_path_env, "").strip()
            credential_value = self.environ.get(self.config.oauth_token_path_env, "").strip()
            if not client_value or not Path(client_value).is_file(): errors.append("OAuth client secret file missing")
            if not credential_value or not Path(credential_value).is_file():
                errors.append("OAuth token missing; run google-oauth-login")
        definitions = ((self.config.events_sheet, EVENT_COLUMNS),
                       (self.config.conflicts_sheet, CONFLICT_COLUMNS),
                       (self.config.state_sheet, STATE_COLUMNS))
        if dry_run:
            actions = tuple({"sheet": name, "action": "would_verify_or_create",
                             "header": ",".join(columns)} for name, columns in definitions)
            return SheetSetupResult("BLOCKED" if errors else "DRY_RUN", True,
                                    actions, tuple(errors), tuple(warnings))
        if not self.config.enabled:
            errors.append("Bucoliche adapter disabled; enable only for the test Sheet")
        if errors:
            return SheetSetupResult("BLOCKED", False, (), tuple(errors), tuple(warnings))
        client = (self.client_factory(spreadsheet_id, credential_value)
                  if self.client_factory else build_google_sheets_client(self.config, self.environ))
        try: existing = client.inspect_sheets()
        except Exception as exc:
            return SheetSetupResult("BLOCKED", False, (),
                                    (f"spreadsheet read failed: {type(exc).__name__}",), ())
        mismatches = [name for name, columns in definitions
                      if name in existing and existing[name]
                      and tuple(existing[name])[:len(columns)] != tuple(columns)]
        if mismatches:
            actions = tuple({"sheet": name, "action": "blocked_header_mismatch"}
                            for name in mismatches)
            errors = tuple(f"header_mismatch: {name}" for name in mismatches)
            return SheetSetupResult("BLOCKED", False, actions, errors, ())
        actions = []
        for name, columns in definitions:
            header = tuple(existing.get(name, ()))
            if name not in existing:
                client.create_sheet(name)
                client.write_header(name, columns)
                actions.append({"sheet": name, "action": "created_with_header"})
            elif not header:
                client.write_header(name, columns)
                actions.append({"sheet": name, "action": "header_written"})
            else:
                if len(header) > len(columns): warnings.append(f"extra header columns: {name}")
                actions.append({"sheet": name, "action": "unchanged"})
        return SheetSetupResult("BLOCKED" if errors else "READY_WITH_WARNINGS" if warnings else "READY",
                                False, tuple(actions), tuple(errors), tuple(warnings))


class PilotPreview:
    NEXT_COMMANDS = (
        "python -m virgilio_connector setup-bucoliche-test-sheet --config accounts.local.yaml --dry-run",
        "python -m virgilio_connector doctor-bucoliche --config accounts.local.yaml",
        "python -m virgilio_connector run-local-pipeline --config accounts.local.yaml --dry-run",
        "python -m virgilio_connector export-to-bucoliche --config accounts.local.yaml --dry-run",
        "python -m virgilio_connector export-to-bucoliche --config accounts.local.yaml",
    )

    def __init__(self, accounts, *, storage, bucoliche, paths, pilot_status,
                 environ: Mapping[str, str] | None = None):
        self.accounts, self.storage, self.bucoliche = accounts, storage, bucoliche
        self.paths, self.pilot_status = paths, pilot_status
        self.environ = os.environ if environ is None else environ

    def run(self) -> dict:
        events = central_event_rows(self.paths.state_db) if self.paths.state_db.is_file() else []
        conflicts = [row for row in events if row.get("conflict_type") or
                     row.get("global_state_suggestion") == "conflict"]
        target = self.environ.get(self.bucoliche.spreadsheet_id_env, "")
        masked = "" if not target else f"{target[:4]}...{target[-4:]}"
        warnings = [f"{a.account_alias}: ack_enabled=true" for a in self.accounts
                    if a.enabled and a.ack_enabled]
        return {"accounts": [{"account_alias": a.account_alias, "ack_enabled": a.ack_enabled}
                             for a in self.accounts if a.enabled],
                "storage_dir": str(self.storage.staging_dir or ""),
                "bucoliche_enabled": self.bucoliche.enabled,
                "credentials_mode": self.bucoliche.credentials_mode,
                "oauth_token_present": self._oauth_token_present(),
                "sheet_target": masked, "events_exportable": len(events),
                "local_conflicts": len(conflicts), "pilot_check": self.pilot_status,
                "doctor_bucoliche": "RUN_SEPARATELY_READ_ONLY", "warnings": warnings,
                "next_commands": self.NEXT_COMMANDS}

    def _oauth_token_present(self):
        if self.bucoliche.credentials_mode != "user_oauth_local": return None
        value = self.environ.get(self.bucoliche.oauth_token_path_env, "").strip()
        return bool(value and Path(value).is_file())


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
        _, state_warnings = ensure_state_db(self.paths.root)
        warnings.extend(state_warnings)
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
                if self.bucoliche.credentials_mode == "service_account_json_env":
                    if not self.environ.get(self.bucoliche.service_account_json_env):
                        raise BucolicheError("service account env missing")
                else:
                    client = self.environ.get(self.bucoliche.oauth_client_secrets_path_env, "")
                    token = self.environ.get(self.bucoliche.oauth_token_path_env, "")
                    if not client or not Path(client).is_file():
                        raise BucolicheError("OAuth client secret missing")
                    if not token or not Path(token).is_file():
                        raise BucolicheError("OAuth token missing")
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


@dataclass(frozen=True, slots=True)
class PilotSafeResult:
    status: str
    dry_run: bool
    stopped_at: str | None
    pilot_check: str
    pipeline_status: str | None
    export_status: str | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    suggested_next_commands: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))


class PilotSafeRunner:
    def __init__(self, *, pilot_check_runner: PilotCheck,
                 pipeline_factory: Callable[[], LocalPipelineRunner],
                 export_factory: Callable[[], BucolicheAppendOnlyAdapter]) -> None:
        self.pilot_check_runner = pilot_check_runner
        self.pipeline_factory = pipeline_factory
        self.export_factory = export_factory

    def run(self) -> PilotSafeResult:
        pilot = self.pilot_check_runner.run()
        warnings = list(pilot.warnings)
        if pilot.status == "BLOCKED":
            return PilotSafeResult(
                status="BLOCKED",
                dry_run=True,
                stopped_at="pilot_check",
                pilot_check=pilot.status,
                pipeline_status=None,
                export_status=None,
                errors=pilot.errors,
                warnings=tuple(warnings),
                suggested_next_commands=pilot.suggested_next_commands,
            )

        pipeline = self.pipeline_factory().run(dry_run=True)
        warnings.extend(pipeline.warnings)
        if pipeline.errors:
            return PilotSafeResult(
                status="BLOCKED",
                dry_run=True,
                stopped_at="pipeline",
                pilot_check=pilot.status,
                pipeline_status=pipeline.status,
                export_status=None,
                errors=tuple(pipeline.errors),
                warnings=tuple(warnings),
                suggested_next_commands=("python -m virgilio_connector run-local-pipeline --config accounts.local.yaml --dry-run",),
            )

        export = self.export_factory().export(dry_run=True)
        warnings.extend(export.errors)
        return PilotSafeResult(
            status="READY_WITH_WARNINGS" if warnings else "READY",
            dry_run=True,
            stopped_at=None,
            pilot_check=pilot.status,
            pipeline_status=pipeline.status,
            export_status=export.status,
            errors=(),
            warnings=tuple(warnings),
            suggested_next_commands=(
                "python -m virgilio_connector run-local-pipeline --config accounts.local.yaml",
                "python -m virgilio_connector export-to-bucoliche --config accounts.local.yaml",
            ),
        )


def _check(name: str, ok: bool) -> dict[str, str]:
    return {"name": name, "status": "OK" if ok else "MISSING"}


def _result(checks, errors, warnings, commands=()) -> ReadinessResult:
    status = "BLOCKED" if errors else "READY_WITH_WARNINGS" if warnings else "READY"
    return ReadinessResult(status, tuple(checks), tuple(errors), tuple(warnings), tuple(commands))
