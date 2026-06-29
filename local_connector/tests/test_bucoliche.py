import json
from pathlib import Path
import sqlite3
import sys
from contextlib import closing

import pytest

from virgilio_connector.bucoliche import (
    BucolicheAppendOnlyAdapter, BucolicheConfig, BucolicheError,
    CONFLICT_COLUMNS, EVENT_COLUMNS, STATE_COLUMNS, GoogleOAuthLogin,
    load_bucoliche_config,
)
from virgilio_connector.readonly_state import ReadonlyStateStore


class FakeSheets:
    def __init__(self, fail=False): self.fail, self.calls = fail, []
    def append_rows(self, sheet_name, columns, rows):
        self.calls.append((sheet_name, tuple(columns), tuple(rows)))
        if self.fail: raise RuntimeError("fake api failure")
    def replace_rows(self, sheet_name, columns, rows):
        self.calls.append(("replace", sheet_name, tuple(columns), tuple(rows)))
        if self.fail: raise RuntimeError("fake api failure")


class FailConflictOnce(FakeSheets):
    def append_rows(self, sheet_name, columns, rows):
        self.calls.append((sheet_name, tuple(columns), tuple(rows)))
        if sheet_name == "Bucoliche_Conflitti": raise RuntimeError("conflict append failed")


def state_with_event(tmp_path, action="attachment_quarantined"):
    db = tmp_path / "state.db"
    store = ReadonlyStateStore(db); store.initialize()
    store.add_audit_event(machine_id="machine-test", account_alias="box",
        entity_type="attachment", entity_id="att-1", fingerprint="f" * 64,
        action=action, status="test", details={"safe": True})
    return db


def adapter(db, client, enabled=True):
    return BucolicheAppendOnlyAdapter(state_db=db,
        config=BucolicheConfig(enabled=enabled), client=client, environ={})


def test_dry_run_has_preview_without_google_or_sqlite_write(tmp_path):
    db = state_with_event(tmp_path); fake = FakeSheets()
    result = adapter(db, fake, enabled=False).export(dry_run=True)
    assert result.events_pending == 1 and len(result.preview) == 1
    assert fake.calls == []
    with closing(sqlite3.connect(db)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM local_export_status").fetchone()[0] == 0


def test_disabled_blocks_real_export(tmp_path):
    fake = FakeSheets()
    with pytest.raises(BucolicheError, match="disabled"):
        adapter(state_with_event(tmp_path), fake, enabled=False).export(dry_run=False)
    assert fake.calls == []


def test_append_and_event_id_idempotency(tmp_path):
    db = state_with_event(tmp_path); fake = FakeSheets()
    first = adapter(db, fake).export(dry_run=False)
    retry = adapter(db, fake).export(dry_run=False)
    assert first.events_exported == 1 and retry.already_exported == 1
    assert [call[0] for call in fake.calls] == ["Bucoliche_Eventi", "replace", "replace"]
    assert fake.calls[0][1] == EVENT_COLUMNS
    assert fake.calls[1][2] == STATE_COLUMNS


def test_failed_event_is_recorded_and_retried(tmp_path):
    db = state_with_event(tmp_path)
    failed = adapter(db, FakeSheets(fail=True)).export(dry_run=False)
    good = FakeSheets(); retried = adapter(db, good).export(dry_run=False)
    assert failed.status == "completed_with_errors"
    assert retried.events_exported == 1
    assert [call[0] for call in good.calls] == ["Bucoliche_Eventi", "replace"]
    with closing(sqlite3.connect(db)) as conn:
        assert conn.execute("SELECT export_result FROM local_export_status").fetchone()[0] == "exported"


def test_conflicts_are_appended_to_conflicts_sheet(tmp_path):
    fake = FakeSheets()
    result = adapter(state_with_event(tmp_path, "conflict_hash_mismatch"), fake).export(dry_run=False)
    assert result.conflicts_pending == 1
    assert [call[0] for call in fake.calls] == ["Bucoliche_Eventi", "Bucoliche_Conflitti", "replace"]
    assert fake.calls[1][1] == CONFLICT_COLUMNS


def test_partial_conflict_failure_does_not_duplicate_event_append(tmp_path):
    db = state_with_event(tmp_path, "conflict_hash_mismatch")
    first = FailConflictOnce(); adapter(db, first).export(dry_run=False)
    retry = FakeSheets(); adapter(db, retry).export(dry_run=False)
    assert [call[0] for call in first.calls] == ["Bucoliche_Eventi", "Bucoliche_Conflitti", "replace"]
    assert [call[0] for call in retry.calls] == ["Bucoliche_Conflitti", "replace"]


def test_state_sheet_is_rebuilt_from_latest_event_without_reappending_events(tmp_path):
    db = tmp_path / "state.db"
    store = ReadonlyStateStore(db); store.initialize()
    store.add_audit_event(machine_id="machine-test", account_alias="box",
        entity_type="attachment", entity_id="att-1", fingerprint="f" * 64,
        action="attachment_quarantined", status="queued", details={"step": "start"})
    store.add_audit_event(machine_id="machine-test", account_alias="box",
        entity_type="attachment", entity_id="att-1", fingerprint="f" * 64,
        action="message_completed", status="ok", details={"step": "done"})
    fake = FakeSheets()
    adapter(db, fake).export(dry_run=False)
    retry = adapter(db, fake).export(dry_run=False)
    assert retry.already_exported == 2
    replace = fake.calls[-1]
    assert replace[:3] == ("replace", "Bucoliche_Stato", STATE_COLUMNS)
    assert len(replace[3]) == 1
    row = replace[3][0]
    assert row["current_global_state"] == "completed"
    assert row["last_result"] == "ok"
    assert row["notes"] == '{"step":"done"}'


def test_output_never_contains_credentials(tmp_path):
    result = adapter(state_with_event(tmp_path), FakeSheets(), enabled=False).export(dry_run=True)
    text = json.dumps(result.preview).lower()
    assert not any(value in text for value in ("password", "token", "service_account", "private_key", "base64"))


def test_load_config_defaults_and_explicit_values(tmp_path):
    path = tmp_path / "accounts.yaml"
    path.write_text("""bucoliche:
  enabled: false
  append_only: true
  dry_run_default: true
""", encoding="utf-8")
    config = load_bucoliche_config(path)
    assert config.enabled is False and config.append_only is True


def test_export_to_bucoliche_cli_dry_run(tmp_path, monkeypatch, capsys):
    local_root = tmp_path / ".local_data"
    state_with_event(local_root)
    config = tmp_path / "accounts.yaml"
    config.write_text("""accounts:
  - account_alias: test_box
    email: test@example.invalid
    provider_hint: generic_imap
    imap_host: imap.example.invalid
    imap_port: 993
    username_env: TEST_USER
    password_env: TEST_PASS
    input_folder: INBOX
    done_folder: done
    error_folder: error
bucoliche:
  enabled: false
""", encoding="utf-8")
    monkeypatch.setenv("VIRGILIO_LOCAL_DATA_DIR", str(local_root))
    monkeypatch.setattr(sys, "argv", ["virgilio_connector", "export-to-bucoliche",
        "--config", str(config), "--dry-run"])
    from virgilio_connector.__main__ import main
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["events_pending"] == 1


class FakeOAuthCredentials:
    def __init__(self, *, valid=True, expired=False, refresh_token="refresh-secret"):
        self.valid, self.expired, self.refresh_token = valid, expired, refresh_token
    def refresh(self, request): self.valid, self.expired = True, False
    def to_json(self): return '{"access_token":"token-secret"}'


class FakeOAuthFlow:
    def __init__(self, credentials): self.credentials = credentials; self.calls = []
    def run_local_server(self, port):
        self.calls.append(port)
        return self.credentials


def oauth_config():
    return BucolicheConfig(credentials_mode="user_oauth_local")


def test_user_oauth_config_is_valid():
    oauth_config().validate()


def test_google_oauth_login_creates_token_without_printing_it(tmp_path):
    secret = tmp_path / "client.json"; secret.write_text('{"installed":{}}', encoding="utf-8")
    token = tmp_path / "token.json"; flow = FakeOAuthFlow(FakeOAuthCredentials())
    result = GoogleOAuthLogin(oauth_config(), environ={
        "VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH": str(secret),
        "VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH": str(token)},
        flow_factory=lambda *_: flow).run()
    assert result.status == "token_created" and token.is_file()
    assert flow.calls == [0]
    assert "token-secret" not in result.to_json()


def test_google_oauth_login_refreshes_existing_token(tmp_path):
    secret = tmp_path / "client.json"; secret.write_text('{}', encoding="utf-8")
    token = tmp_path / "token.json"; token.write_text('{}', encoding="utf-8")
    credentials = FakeOAuthCredentials(valid=False, expired=True)
    result = GoogleOAuthLogin(oauth_config(), environ={
        "VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH": str(secret),
        "VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH": str(token)},
        credentials_loader=lambda *_: credentials, request_factory=lambda: object()).run()
    assert result.status == "token_refreshed" and credentials.valid


def test_google_oauth_login_missing_secret_is_blocked_and_safe(tmp_path):
    result = GoogleOAuthLogin(oauth_config(), environ={
        "VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH": str(tmp_path / "missing.json"),
        "VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH": str(tmp_path / "token.json")}).run()
    assert result.status == "blocked"
    assert not any(word in result.to_json() for word in ("access_token", "refresh_token", "client_secret"))
