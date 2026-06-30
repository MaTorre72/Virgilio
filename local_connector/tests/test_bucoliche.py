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
from virgilio_connector.completion import LocalCompletionRunner
from virgilio_connector.local_paths import LocalDataPaths
from virgilio_connector.multi_account import (
    MultiAccountImapProcessor,
    MultiAccountReadonlyScanner,
    load_multi_account_config,
    load_storage_config,
)
from virgilio_connector.pipeline import LocalPipelineRunner
from virgilio_connector.readonly_state import ReadonlyStateStore
from virgilio_connector.storage_adapter import LocalFilesystemStorageAdapter

from test_multi_account import (
    FakeAckMailbox,
    FakeMailbox,
    FakeProcessMailbox,
    FakeScanner,
    ScanVerdict,
    write_storage_config,
)


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


def test_second_export_of_already_exported_event_skips_append_and_rebuilds_state(tmp_path):
    db = state_with_event(tmp_path)
    event_row = BucolicheAppendOnlyAdapter(
        state_db=db,
        config=BucolicheConfig(enabled=True),
        client=FakeSheets(),
        environ={},
    ).export(dry_run=True).preview[0]
    store = ReadonlyStateStore(db); store.initialize()
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("""INSERT INTO local_export_status(
            event_id,target_adapter,exported_at,export_result,error_type
        ) VALUES(?,?,?,?,?)""", (
            event_row["event_id"],
            BucolicheAppendOnlyAdapter.TARGET,
            "2026-06-30T00:00:00+00:00",
            "exported",
            None,
        ))
        conn.commit()
    fake = FakeSheets()
    result = adapter(db, fake).export(dry_run=False)
    assert result.events_pending == 0
    assert result.events_exported == 0
    assert result.already_exported == 1
    assert len(fake.calls) == 1
    replace = fake.calls[0]
    assert replace[:3] == ("replace", "Bucoliche_Stato", STATE_COLUMNS)
    assert len(replace[3]) == 1
    assert replace[3][0]["fingerprint"] == "f" * 64


def test_dry_run_can_preview_same_fingerprint_from_two_machine_ids(tmp_path):
    db = tmp_path / "state.db"
    store = ReadonlyStateStore(db); store.initialize()
    for machine_id, suffix in (("machine-a", "1"), ("machine-b", "2")):
        with closing(sqlite3.connect(db)) as conn:
            conn.execute("""INSERT INTO runs(started_at,dry_run,status,account_alias)
                VALUES('now',0,'completed','box')""")
            run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("""INSERT INTO messages(run_id,account_alias,mailbox,uidvalidity,message_uid,
                message_id,subject,sender,message_date) VALUES(?,?,?,?,?,?,?,?,?)""",
                (run_id, "box", "INBOX", "1", f"4{suffix}", f"<m-{suffix}@example.invalid>", "Subject",
                 "sender@example.invalid", "2026-06-30T00:00:00+00:00"))
            message_row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("""INSERT INTO attachments(message_id,account_alias,attachment_id,source_email,
                ordinal,original_filename,sanitized_filename,declared_mime_type,size_bytes,sha256,
                status,reason,fingerprint,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (message_row_id, "box", f"att-{suffix}", "box@example.invalid", 1, f"a-{suffix}.pdf",
                 f"a-{suffix}.pdf", "application/pdf", 1, "a" * 64, "ready_for_caronte",
                 "test", "f" * 64, f"2026-06-30T00:00:0{suffix}+00:00"))
            conn.commit()
        store.add_audit_event(machine_id=machine_id, account_alias="box",
            entity_type="attachment", entity_id=f"att-{suffix}", fingerprint="f" * 64,
            action="attachment_quarantined", status="ready_for_caronte",
            details={"machine": machine_id})
    preview = adapter(db, FakeSheets(), enabled=False).export(dry_run=True).preview
    assert len(preview) == 2
    assert {row["machine_id"] for row in preview} == {"machine-a", "machine-b"}
    assert len({row["event_id"] for row in preview}) == 2
    assert {row["fingerprint"] for row in preview} == {"f" * 64}


def test_end_to_end_retry_does_not_append_duplicate_bucoliche_events(tmp_path):
    class IsolatedScanMailbox(FakeMailbox):
        instances = []

    class IsolatedProcessMailbox(FakeProcessMailbox):
        instances = []

    class IsolatedAckMailbox(FakeAckMailbox):
        instances = []

    staging = tmp_path / "staging"
    staging.mkdir()
    config = write_storage_config(tmp_path, staging)
    accounts = load_multi_account_config(config)[:1]
    storage_config = load_storage_config(config)
    paths = LocalDataPaths(tmp_path / ".local_data")

    def runner():
        return LocalPipelineRunner(
            accounts,
            paths=paths,
            config_path=config,
            scanner_factory=lambda: MultiAccountReadonlyScanner(
                accounts,
                paths=paths,
                environ={
                    "VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME": "user@example.invalid",
                    "VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD": "secret",
                },
                mailbox_factory=lambda account, root: IsolatedScanMailbox(account, root),
            ),
            processor_factory=lambda: MultiAccountImapProcessor(
                accounts,
                paths=paths,
                environ={
                    "VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME": "user@example.invalid",
                    "VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD": "secret",
                },
                mailbox_factory=lambda account, root: IsolatedProcessMailbox(account, root),
                scanner=FakeScanner(ScanVerdict.CLEAN),
            ),
            storage_factory=lambda: LocalFilesystemStorageAdapter(
                state_db=paths.state_db,
                local_data_root=paths.root,
                config=storage_config,
            ),
            completion_factory=lambda: LocalCompletionRunner(
                accounts,
                paths=paths,
                environ={
                    "VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME": "user@example.invalid",
                    "VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD": "secret",
                },
                mailbox_factory=lambda account: IsolatedAckMailbox(account),
            ),
        )

    fake = FakeSheets()
    first_pipeline = runner().run(dry_run=False)
    first_export = BucolicheAppendOnlyAdapter(
        state_db=paths.state_db,
        config=BucolicheConfig(enabled=True),
        client=fake,
        environ={},
    ).export(dry_run=False)
    second_pipeline = runner().run(dry_run=False)
    second_export = BucolicheAppendOnlyAdapter(
        state_db=paths.state_db,
        config=BucolicheConfig(enabled=True),
        client=fake,
        environ={},
    ).export(dry_run=False)

    assert first_pipeline.status == "completed"
    assert second_pipeline.status == "completed"
    assert first_export.events_exported == 6
    assert second_export.events_exported == 0
    assert second_export.already_exported == 6
    assert [call[0] for call in fake.calls].count("Bucoliche_Eventi") == 6
    state_replace = fake.calls[-1]
    assert state_replace[:3] == ("replace", "Bucoliche_Stato", STATE_COLUMNS)
    assert len(state_replace[3]) == 2
    assert all(row["current_global_state"] == "completed" for row in state_replace[3])


def test_output_never_contains_credentials(tmp_path):
    result = adapter(state_with_event(tmp_path), FakeSheets(), enabled=False).export(dry_run=True)
    text = json.dumps(result.preview).lower()
    assert not any(value in text for value in ("password", "token", "service_account", "private_key", "base64"))


def test_bucoliche_dry_run_skips_legacy_attachment_without_attachment_id(tmp_path):
    local_root = tmp_path / ".local_data"
    db = local_root / "state.db"
    store = ReadonlyStateStore(db); store.initialize()
    with sqlite3.connect(db) as conn:
        conn.execute("""INSERT INTO runs(started_at,dry_run,status,account_alias)
            VALUES('now',0,'completed','box')""")
        run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""INSERT INTO messages(run_id,account_alias,mailbox,uidvalidity,message_uid,
            message_id,subject,sender,message_date) VALUES(?,?,?,?,?,?,?,?,?)""",
            (run_id, "box", "INBOX", "1", "42", "<m@example.invalid>", "Legacy",
             "sender@example.invalid", "2026-06-30T00:00:00+00:00"))
        message_row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""INSERT INTO attachments(message_id,account_alias,attachment_id,source_email,
            ordinal,original_filename,sanitized_filename,declared_mime_type,size_bytes,sha256,
            status,reason,fingerprint,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (message_row_id, "box", None, "box@example.invalid", 1, "legacy.pdf", "legacy.pdf",
             "application/pdf", 1, "b" * 64, "ready_for_caronte", "legacy", "f" * 64, "now"))
        conn.commit()
    store.add_audit_event(machine_id="machine-test", account_alias="box",
        entity_type="attachment", entity_id="legacy-missing-id", fingerprint="f" * 64,
        action="attachment_quarantined", status="ready_for_caronte", details={"legacy": True})
    result = adapter(db, FakeSheets(), enabled=False).export(dry_run=True)
    assert result.events_total == 0
    assert result.events_pending == 0
    assert result.preview == ()


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
