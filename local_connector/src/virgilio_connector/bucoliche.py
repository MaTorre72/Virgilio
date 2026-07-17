"""Append-only Google Sheets adapter for central Bucoliche event views."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3
from contextlib import closing
from typing import Mapping, Protocol, Sequence
from urllib.parse import quote

from .readonly_state import ReadonlyStateStore, ensure_state_db
from .traceability import central_event_rows
from .time_utils import ROME_TZ, rome_isoformat, rome_min


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
    "conflict_type", "staged_filename", "staged_path", "manifest_path", "notes",
)


class BucolicheError(RuntimeError): pass


@dataclass(frozen=True, slots=True)
class BucolicheConfig:
    enabled: bool = False
    adapter: str = "google_sheets_append_only"
    spreadsheet_id: str = ""
    spreadsheet_id_env: str = "VIRGILIO_BUCOLICHE_SPREADSHEET_ID"
    events_sheet: str = "Bucoliche_Eventi"
    state_sheet: str = "Bucoliche_Stato"
    conflicts_sheet: str = "Bucoliche_Conflitti"
    credentials_mode: str = "service_account_json_env"
    service_account_json_env: str = "VIRGILIO_GOOGLE_SERVICE_ACCOUNT_JSON"
    oauth_client_secrets_path_env: str = "VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH"
    oauth_token_path_env: str = "VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH"
    append_only: bool = True
    dry_run_default: bool = True

    def validate(self) -> None:
        if self.adapter != "google_sheets_append_only":
            raise BucolicheError("unsupported Bucoliche adapter")
        if self.credentials_mode not in {"service_account_json_env", "user_oauth_local"}:
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
    def replace_rows(self, sheet_name: str, columns: Sequence[str],
                     rows: Sequence[Mapping[str, object]]) -> None: ...


SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"


class GoogleSheetsAppendClient:
    """Small REST client; credentials are read only from environment variables."""
    def __init__(self, spreadsheet_id: str, service_account_json: str | None = None,
                 *, credentials=None) -> None:
        try:
            from google.auth.transport.requests import AuthorizedSession
            if credentials is None:
                from google.oauth2 import service_account
                info = json.loads(service_account_json or "")
                credentials = service_account.Credentials.from_service_account_info(
                    info, scopes=(SHEETS_SCOPE,))
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

    def replace_rows(self, sheet_name: str, columns: Sequence[str],
                     rows: Sequence[Mapping[str, object]]) -> None:
        base = (f"https://sheets.googleapis.com/v4/spreadsheets/"
                f"{quote(self.spreadsheet_id, safe='')}/values/"
                f"{quote(sheet_name, safe='')}")
        clear = self._session.post(f"{base}!A:Z:clear", timeout=20)
        if clear.status_code >= 400:
            raise BucolicheError(f"Google Sheets clear failed: HTTP {clear.status_code}")
        values = [list(columns)] + [[row.get(column, "") if row.get(column) is not None else ""
                                     for column in columns] for row in rows]
        write = self._session.put(f"{base}!A1", params={"valueInputOption": "RAW"},
                                  json={"values": values}, timeout=20)
        if write.status_code >= 400:
            raise BucolicheError(f"Google Sheets replace failed: HTTP {write.status_code}")

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


@dataclass(frozen=True, slots=True)
class BucolicheStateRefreshResult:
    status: str
    dry_run: bool
    state_rows_total: int
    preview: tuple[dict[str, object], ...]
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
        ensure_state_db(self.state_db.parent)
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
        state_result = self.refresh_state(dry_run=False, client=client)
        errors.extend(state_result.errors)
        return BucolicheExportResult("completed_with_errors" if errors else "completed",
            False, len(events), len(pending), done, len(events) - len(pending),
            len(conflicts), (), tuple(errors))

    def refresh_state(self, *, dry_run: bool,
                      client: SheetsAppendClient | None = None) -> BucolicheStateRefreshResult:
        self.config.validate()
        ensure_state_db(self.state_db.parent)
        state_rows = _state_rows([
            _event_row(row) for row in central_event_rows(self.state_db)
        ])
        if dry_run:
            return BucolicheStateRefreshResult(
                status="dry_run",
                dry_run=True,
                state_rows_total=len(state_rows),
                preview=state_rows[:5],
                errors=(),
            )
        if not self.config.enabled:
            raise BucolicheError("Bucoliche adapter is disabled; set bucoliche.enabled=true")
        active_client = client or self.client or self._client_from_env()
        try:
            active_client.replace_rows(self.config.state_sheet, STATE_COLUMNS, state_rows)
        except Exception as exc:
            return BucolicheStateRefreshResult(
                status="completed_with_errors",
                dry_run=False,
                state_rows_total=len(state_rows),
                preview=(),
                errors=(f"state {self.config.state_sheet}: {type(exc).__name__}",),
            )
        return BucolicheStateRefreshResult(
            status="completed",
            dry_run=False,
            state_rows_total=len(state_rows),
            preview=(),
            errors=(),
        )

    def _client_from_env(self) -> SheetsAppendClient:
        return build_google_sheets_client(self.config, self.environ)

    def _successful_event_ids(self, target: str) -> set[str]:
        with closing(sqlite3.connect(self.state_db)) as db:
            exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_export_status'").fetchone()
            if not exists: return set()
            return {row[0] for row in db.execute("""SELECT event_id FROM local_export_status
                WHERE target_adapter=? AND export_result='exported'""", (target,))}

    def _record(self, event_id: str, target: str, result: str,
                error_type: str | None = None) -> None:
        ReadonlyStateStore(self.state_db).initialize()
        now = rome_isoformat() if result == "exported" else None
        with closing(sqlite3.connect(self.state_db)) as db:
            db.execute("""INSERT INTO local_export_status(event_id,target_adapter,exported_at,
                export_result,error_type) VALUES(?,?,?,?,?) ON CONFLICT(event_id,target_adapter)
                DO UPDATE SET exported_at=excluded.exported_at,export_result=excluded.export_result,
                error_type=excluded.error_type""", (event_id, target, now, result, error_type))
            db.commit()


def _event_row(row: Mapping[str, object]) -> dict:
    exported_at = rome_isoformat()
    return {column: (exported_at if column == "exported_at" else row.get(column, ""))
            for column in EVENT_COLUMNS}


def _conflict_row(row: Mapping[str, object]) -> dict:
    values = dict(row); values["detected_at"] = row.get("created_at", "")
    return {column: values.get(column, "") for column in CONFLICT_COLUMNS}


def _state_rows(events: Sequence[Mapping[str, object]]) -> tuple[dict[str, object], ...]:
    by_fingerprint: dict[str, list[Mapping[str, object]]] = {}
    for row in events:
        fingerprint = str(row.get("fingerprint", "")).strip()
        if not fingerprint:
            continue
        by_fingerprint.setdefault(fingerprint, []).append(row)
    rows = []
    for fingerprint in sorted(by_fingerprint):
        grouped = sorted(by_fingerprint[fingerprint], key=_event_sort_key)
        latest = grouped[-1]
        machine_ids = sorted({str(row.get("machine_id", "")).strip()
                              for row in grouped if str(row.get("machine_id", "")).strip()})
        machine_states = _machine_states(grouped)
        cross_machine_conflict = _has_cross_machine_conflict(machine_states)
        current_state = _resolved_global_state(latest)
        rows.append({
            "fingerprint": fingerprint,
            "last_event_at": _to_local_timestamp(latest.get("created_at", "")),
            "machine_id": ",".join(machine_ids) if len(machine_ids) > 1 else latest.get("machine_id", ""),
            "account_alias": latest.get("account_alias", ""),
            "source_email": latest.get("source_email", ""),
            "attachment_id": latest.get("attachment_id", ""),
            "sha256": latest.get("sha256", ""),
            "current_global_state": "conflict" if cross_machine_conflict else current_state,
            "last_result": latest.get("result", ""),
            "conflict_type": ("conflict_cross_machine" if cross_machine_conflict
                              else str(latest.get("conflict_type", "") or "")),
            "staged_filename": latest.get("staged_filename", ""),
            "staged_path": latest.get("staged_path", ""),
            "manifest_path": latest.get("manifest_path", ""),
            "notes": _state_notes(latest, machine_ids, machine_states, cross_machine_conflict),
        })
    return tuple(rows)

def _event_sort_key(row: Mapping[str, object]) -> tuple[datetime, str]:
    return (_parse_timestamp(row.get("created_at", "")), str(row.get("event_id", "")))


def _parse_timestamp(value: object) -> datetime:
    text = str(value or "").strip()
    if not text:
        return rome_min()
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return rome_min()
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=ROME_TZ)
    return parsed.astimezone(ROME_TZ)


def _to_local_timestamp(value: object) -> str:
    parsed = _parse_timestamp(value)
    if parsed == rome_min():
        return ""
    return parsed.astimezone(ROME_TZ).isoformat()


def _resolved_global_state(row: Mapping[str, object]) -> str:
    if str(row.get("conflict_type", "") or "").strip():
        return "conflict"
    value = str(row.get("global_state_suggestion", "") or "").strip()
    if value in {"completed", "staged", "acquired", "failed", "duplicate_seen"}:
        return value
    return "unknown"


def _machine_states(grouped: Sequence[Mapping[str, object]]) -> dict[str, str]:
    by_machine: dict[str, list[Mapping[str, object]]] = {}
    for row in grouped:
        machine_id = str(row.get("machine_id", "")).strip()
        if machine_id:
            by_machine.setdefault(machine_id, []).append(row)
    return {machine_id: _resolved_global_state(sorted(rows, key=_event_sort_key)[-1])
            for machine_id, rows in sorted(by_machine.items())}


def _has_cross_machine_conflict(machine_states: Mapping[str, str]) -> bool:
    terminal = {state for state in machine_states.values() if state in {
        "completed", "failed", "duplicate_seen", "skipped", "conflict",
    }}
    return len(machine_states) > 1 and len(terminal) > 1


def _state_notes(current: Mapping[str, object], machine_ids: Sequence[str],
                 machine_states: Mapping[str, str] | None = None,
                 cross_machine_conflict: bool = False) -> str:
    raw = str(current.get("notes", "") or "")
    if len(machine_ids) <= 1:
        return raw
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {"latest_note": raw}
    if not isinstance(payload, dict):
        payload = {"latest_note": payload}
    payload["machine_ids"] = list(machine_ids)
    payload["cross_machine"] = True
    if cross_machine_conflict:
        payload["cross_machine_conflict"] = True
        payload["machine_states"] = dict(machine_states or {})
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def build_google_sheets_client(config: BucolicheConfig,
                               environ: Mapping[str, str]) -> GoogleSheetsAppendClient:
    spreadsheet_id = config.spreadsheet_id.strip() or environ.get(
        config.spreadsheet_id_env, ""
    ).strip()
    if not spreadsheet_id:
        raise BucolicheError(f"missing env: {config.spreadsheet_id_env}")
    if config.credentials_mode == "service_account_json_env":
        payload = environ.get(config.service_account_json_env, "")
        if not payload: raise BucolicheError(f"missing env: {config.service_account_json_env}")
        return GoogleSheetsAppendClient(spreadsheet_id, payload)
    client_path = _configured_path(environ, config.oauth_client_secrets_path_env)
    token_path = _configured_path(environ, config.oauth_token_path_env)
    if not client_path.is_file(): raise BucolicheError("OAuth client secret file missing")
    if not token_path.is_file():
        raise BucolicheError("OAuth token missing; run google-oauth-login")
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        credentials = Credentials.from_authorized_user_file(str(token_path), (SHEETS_SCOPE,))
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except Exception:
                raise BucolicheError("OAuth token refresh failed; verify local network access or run google-oauth-login again") from None
            _write_private_json(token_path, credentials.to_json())
        if not credentials.valid:
            raise BucolicheError("OAuth token invalid; run google-oauth-login")
        return GoogleSheetsAppendClient(spreadsheet_id, credentials=credentials)
    except ImportError:
        raise BucolicheError("Google OAuth dependencies unavailable") from None
    except (ValueError, json.JSONDecodeError):
        raise BucolicheError("OAuth token invalid; run google-oauth-login") from None


@dataclass(frozen=True, slots=True)
class GoogleOAuthLoginResult:
    status: str
    errors: tuple[str, ...] = ()

    def to_json(self) -> str:
        return json.dumps({"status": self.status, "errors": self.errors},
                          ensure_ascii=False, separators=(",", ":"))


class GoogleOAuthLogin:
    def __init__(self, config: BucolicheConfig, *, environ: Mapping[str, str] | None = None,
                 flow_factory=None, credentials_loader=None, request_factory=None) -> None:
        self.config = config
        self.environ = os.environ if environ is None else environ
        self.flow_factory = flow_factory
        self.credentials_loader = credentials_loader
        self.request_factory = request_factory

    def run(self) -> GoogleOAuthLoginResult:
        if self.config.credentials_mode != "user_oauth_local":
            return GoogleOAuthLoginResult("blocked", ("credentials_mode must be user_oauth_local",))
        try:
            client_path = _configured_path(self.environ, self.config.oauth_client_secrets_path_env)
            token_path = _configured_path(self.environ, self.config.oauth_token_path_env)
        except BucolicheError as exc:
            return GoogleOAuthLoginResult("blocked", (str(exc),))
        if not client_path.is_file():
            return GoogleOAuthLoginResult("blocked", ("OAuth client secret file missing",))
        try:
            parsed = json.loads(client_path.read_text(encoding="utf-8"))
            if not isinstance(parsed, dict): raise ValueError
        except (OSError, ValueError, json.JSONDecodeError):
            return GoogleOAuthLoginResult("blocked", ("OAuth client secret JSON invalid",))
        try:
            if token_path.is_file():
                credentials = self._load_credentials(token_path)
                if credentials.expired and credentials.refresh_token:
                    credentials.refresh(self._request())
                if credentials.valid:
                    _write_private_json(token_path, credentials.to_json())
                    return GoogleOAuthLoginResult("token_refreshed")
            flow = self._flow(client_path)
            credentials = flow.run_local_server(port=0)
            _write_private_json(token_path, credentials.to_json())
            return GoogleOAuthLoginResult("token_created")
        except Exception as exc:
            return GoogleOAuthLoginResult("error", (f"OAuth login failed: {type(exc).__name__}",))

    def _flow(self, path):
        if self.flow_factory: return self.flow_factory(path, (SHEETS_SCOPE,))
        from google_auth_oauthlib.flow import InstalledAppFlow
        return InstalledAppFlow.from_client_secrets_file(str(path), scopes=(SHEETS_SCOPE,))

    def _load_credentials(self, path):
        if self.credentials_loader: return self.credentials_loader(path, (SHEETS_SCOPE,))
        from google.oauth2.credentials import Credentials
        return Credentials.from_authorized_user_file(str(path), (SHEETS_SCOPE,))

    def _request(self):
        if self.request_factory: return self.request_factory()
        from google.auth.transport.requests import Request
        return Request()


def _configured_path(environ: Mapping[str, str], name: str) -> Path:
    value = environ.get(name, "").strip()
    if not value: raise BucolicheError(f"missing env: {name}")
    return Path(value)


def _write_private_json(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)
