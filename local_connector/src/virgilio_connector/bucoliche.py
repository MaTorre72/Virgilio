"""Append-only Google Sheets adapter for central Bucoliche event views."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Mapping, Protocol, Sequence
from urllib.parse import quote

from .readonly_state import ReadonlyStateStore
from .traceability import central_event_rows


EVENT_COLUMNS = (
    "event_id", "created_at", "exported_at", "machine_id", "account_alias",
    "source_email", "source_message_id", "source_message_uid", "attachment_id",
    "fingerprint", "sha256", "event_type", "local_state",
    "global_state_suggestion", "staged_filename", "staged_path", "manifest_path",
    "result", "conflict_type", "notes",
)
CONFLICT_COLUMNS = (
    "event_id", "detected_at", "exported_at", "machine_id", "account_alias",
    "fingerprint", "conflict_type", "source_message_id", "attachment_id", "sha256",
    "staged_filename", "notes",
)
STATE_COLUMNS = (
    "fingerprint", "last_event_at", "machine_id", "account_alias", "source_email",
    "attachment_id", "sha256", "current_global_state", "last_result",
    "conflict_type", "staged_filename", "notes",
)


class BucolicheError(RuntimeError): pass


@dataclass(frozen=True, slots=True)
class BucolicheConfig:
    enabled: bool = False
    adapter: str = "google_sheets_append_only"
    spreadsheet_id_env: str = "VIRGILIO_BUCOLICHE_SPREADSHEET_ID"
    events_sheet: str = "Bucoliche_Eventi"
    state_sheet: str = "Bucoliche_Stato"
    conflicts_sheet: str = "Bucoliche_Conflitti"
    credentials_mode: str = "service_account_json_env"
    service_account_json_env: str = "VIRGILIO_GOOGLE_SERVICE_ACCOUNT_JSON"
    append_only: bool = True
    dry_run_default: bool = True

    def validate(self) -> None:
        if self.adapter != "google_sheets_append_only":
            raise BucolicheError("unsupported Bucoliche adapter")
        if self.credentials_mode != "service_account_json_env":
            raise BucolicheError("unsupported Bucoliche credentials_mode")
        if not self.append_only:
            raise BucolicheError("Bucoliche adapter must remain append-only")


def load_bucoliche_config(path: Path) -> BucolicheConfig:
    if not path.is_file():
        raise BucolicheError(f"configuration file not found: {path}")
    values: dict[str, object] = {}
    active = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        text = raw.split("#", 1)[0].strip()
        if not text: continue
        if text == "bucoliche:": active = True; continue
        if active and raw[:1] not in {" ", "\t"}: break
        if active and ":" in text:
            key, value = (item.strip() for item in text.split(":", 1))
            values[key] = _scalar(value)
    config = BucolicheConfig(**values)
    config.validate()
    return config


def _scalar(value: str):
    if value.lower() in {"true", "false"}: return value.lower() == "true"
    return value.strip("'\"")


class SheetsAppendClient(Protocol):
    def append_rows(self, sheet_name: str, columns: Sequence[str],
                    rows: Sequence[Mapping[str, object]]) -> None: ...


class GoogleSheetsAppendClient:
    """Small REST client; credentials are read only from environment variables."""
    def __init__(self, spreadsheet_id: str, service_account_json: str) -> None:
        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import AuthorizedSession
            info = json.loads(service_account_json)
            credentials = service_account.Credentials.from_service_account_info(
                info, scopes=("https://www.googleapis.com/auth/spreadsheets",))
            self._session = AuthorizedSession(credentials)
        except (ImportError, ValueError, KeyError, TypeError) as exc:
            raise BucolicheError(f"Google credentials unavailable or invalid: {type(exc).__name__}") from None
        self.spreadsheet_id = spreadsheet_id

    def append_rows(self, sheet_name: str, columns: Sequence[str],
                    rows: Sequence[Mapping[str, object]]) -> None:
        if not rows: return
        url = (f"https://sheets.googleapis.com/v4/spreadsheets/{quote(self.spreadsheet_id, safe='')}"
               f"/values/{quote(sheet_name, safe='')}!A:Z:append")
        response = self._session.post(url, params={"valueInputOption": "RAW",
            "insertDataOption": "INSERT_ROWS"}, json={"values": [
                [row.get(column, "") if row.get(column) is not None else "" for column in columns]
                for row in rows]}, timeout=20)
        if response.status_code >= 400:
            raise BucolicheError(f"Google Sheets append failed: HTTP {response.status_code}")

    def inspect_sheets(self) -> dict[str, tuple[str, ...]]:
        """Read spreadsheet metadata and first rows only; never writes."""
        base = (f"https://sheets.googleapis.com/v4/spreadsheets/"
                f"{quote(self.spreadsheet_id, safe='')}")
        response = self._session.get(base, params={"fields": "sheets.properties.title"}, timeout=20)
        if response.status_code >= 400:
            raise BucolicheError(f"Google Sheets read failed: HTTP {response.status_code}")
        result: dict[str, tuple[str, ...]] = {}
        for item in response.json().get("sheets", []):
            title = str(item.get("properties", {}).get("title", ""))
            if not title: continue
            header = self._session.get(f"{base}/values/{quote(title, safe='')}!1:1",
                                       timeout=20)
            if header.status_code >= 400:
                raise BucolicheError(f"Google Sheets header read failed: HTTP {header.status_code}")
            values = header.json().get("values", [])
            result[title] = tuple(str(value) for value in (values[0] if values else ()))
        return result

    def create_sheet(self, sheet_name: str) -> None:
        base = (f"https://sheets.googleapis.com/v4/spreadsheets/"
                f"{quote(self.spreadsheet_id, safe='')}:batchUpdate")
        response = self._session.post(base, json={"requests": [{"addSheet": {
            "properties": {"title": sheet_name}}}]}, timeout=20)
        if response.status_code >= 400:
            raise BucolicheError(f"Google Sheets create tab failed: HTTP {response.status_code}")

    def write_header(self, sheet_name: str, columns: Sequence[str]) -> None:
        base = (f"https://sheets.googleapis.com/v4/spreadsheets/"
                f"{quote(self.spreadsheet_id, safe='')}/values/"
                f"{quote(sheet_name, safe='')}!1:1")
        response = self._session.put(base, params={"valueInputOption": "RAW"},
            json={"values": [list(columns)]}, timeout=20)
        if response.status_code >= 400:
            raise BucolicheError(f"Google Sheets header write failed: HTTP {response.status_code}")


@dataclass(frozen=True, slots=True)
class BucolicheExportResult:
    status: str
    dry_run: bool
    events_total: int
    events_pending: int
    events_exported: int
    already_exported: int
    conflicts_pending: int
    preview: tuple[dict, ...]
    errors: tuple[str, ...]


class BucolicheAppendOnlyAdapter:
    TARGET = "google_sheets_append_only"
    CONFLICT_TARGET = "google_sheets_conflicts_append_only"

    def __init__(self, *, state_db: Path, config: BucolicheConfig,
                 environ: Mapping[str, str] | None = None,
                 client: SheetsAppendClient | None = None) -> None:
        self.state_db, self.config = state_db, config
        self.environ = os.environ if environ is None else environ
        self.client = client

    def export(self, *, dry_run: bool) -> BucolicheExportResult:
        self.config.validate()
        if not self.state_db.is_file(): raise BucolicheError("state database not found")
        events = [_event_row(row) for row in central_event_rows(self.state_db)]
        exported = self._successful_event_ids(self.TARGET)
        pending = [row for row in events if row["event_id"] not in exported]
        all_conflicts = [row for row in events if row["conflict_type"] or
                         row["global_state_suggestion"] == "conflict"]
        exported_conflicts = self._successful_event_ids(self.CONFLICT_TARGET)
        conflicts = [row for row in all_conflicts if row["event_id"] not in exported_conflicts]
        if dry_run:
            return BucolicheExportResult("dry_run", True, len(events), len(pending), 0,
                len(events) - len(pending), len(conflicts), tuple(pending[:5]), ())
        if not self.config.enabled:
            raise BucolicheError("Bucoliche adapter is disabled; set bucoliche.enabled=true")
        client = self.client or self._client_from_env()
        errors, done = [], 0
        for row in pending:
            try:
                client.append_rows(self.config.events_sheet, EVENT_COLUMNS, (row,))
                self._record(row["event_id"], self.TARGET, "exported")
                done += 1
            except Exception as exc:
                error_type = type(exc).__name__
                self._record(row["event_id"], self.TARGET, "export_failed", error_type)
                errors.append(f"{row['event_id']}: {error_type}")
        for row in conflicts:
            try:
                client.append_rows(self.config.conflicts_sheet, CONFLICT_COLUMNS,
                                   (_conflict_row(row),))
                self._record(row["event_id"], self.CONFLICT_TARGET, "exported")
            except Exception as exc:
                error_type = type(exc).__name__
                self._record(row["event_id"], self.CONFLICT_TARGET,
                             "export_failed", error_type)
                errors.append(f"conflict {row['event_id']}: {error_type}")
        return BucolicheExportResult("completed_with_errors" if errors else "completed",
            False, len(events), len(pending), done, len(events) - len(pending),
            len(conflicts), (), tuple(errors))

    def _client_from_env(self) -> SheetsAppendClient:
        spreadsheet_id = self.environ.get(self.config.spreadsheet_id_env, "").strip()
        credentials = self.environ.get(self.config.service_account_json_env, "")
        if not spreadsheet_id: raise BucolicheError(f"missing env: {self.config.spreadsheet_id_env}")
        if not credentials: raise BucolicheError(f"missing env: {self.config.service_account_json_env}")
        return GoogleSheetsAppendClient(spreadsheet_id, credentials)

    def _successful_event_ids(self, target: str) -> set[str]:
        with sqlite3.connect(self.state_db) as db:
            exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_export_status'").fetchone()
            if not exists: return set()
            return {row[0] for row in db.execute("""SELECT event_id FROM local_export_status
                WHERE target_adapter=? AND export_result='exported'""", (target,))}

    def _record(self, event_id: str, target: str, result: str,
                error_type: str | None = None) -> None:
        ReadonlyStateStore(self.state_db).initialize()
        now = datetime.now(timezone.utc).isoformat() if result == "exported" else None
        with sqlite3.connect(self.state_db) as db:
            db.execute("""INSERT INTO local_export_status(event_id,target_adapter,exported_at,
                export_result,error_type) VALUES(?,?,?,?,?) ON CONFLICT(event_id,target_adapter)
                DO UPDATE SET exported_at=excluded.exported_at,export_result=excluded.export_result,
                error_type=excluded.error_type""", (event_id, target, now, result, error_type))


def _event_row(row: Mapping[str, object]) -> dict:
    exported_at = datetime.now(timezone.utc).isoformat()
    return {column: (exported_at if column == "exported_at" else row.get(column, ""))
            for column in EVENT_COLUMNS}


def _conflict_row(row: Mapping[str, object]) -> dict:
    values = dict(row); values["detected_at"] = row.get("created_at", "")
    return {column: values.get(column, "") for column in CONFLICT_COLUMNS}
