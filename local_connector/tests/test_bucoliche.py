import json
import re
from datetime import datetime
from pathlib import Path
import sqlite3
import sys
from contextlib import closing
from zoneinfo import ZoneInfo

import pytest

from virgilio_connector.bucoliche import (
    BucolicheAppendOnlyAdapter, BucolicheConfig, BucolicheError,
    CONFLICT_COLUMNS, EVENT_COLUMNS, STATE_COLUMNS, GoogleOAuthLogin,
    build_google_sheets_client,
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
from virgilio_connector.operational_handoff import OperationalHandoffRunner
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
from test_operational_handoff import FakeIntake, FakeVerifier


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
    assert [call[0] for call in fake.calls] == ["bucoliche"]
    assert fake.calls[0][1] == EVENT_COLUMNS


def test_unified_register_keeps_human_bucoliche_schema_and_excludes_local_paths(tmp_path):
    fake = FakeSheets()
    adapter(state_with_event(tmp_path), fake).export(dry_run=False)
    assert EVENT_COLUMNS == (
        "timestamp", "origine", "cliente", "sito", "pratica", "anno", "tecnici",
        "note", "url_cartella", "id_drive", "mittente_dominio", "oggetto_email",
        "nome_file", "estensione", "dimensione_kb", "stato",
        "timestamp_archiviazione",
    )
    assert fake.calls[0][0] == "bucoliche"
    assert "staged_path" not in fake.calls[0][1]
    assert "manifest_path" not in fake.calls[0][1]


def test_gas_and_python_share_the_exact_bucoliche_columns():
    gas_source = (
        Path(__file__).parents[2] / "apps_script" / "src" / "bucoliche.gs"
    ).read_text(encoding="utf-8")
    header_block = re.search(
        r"const intestazioni = \[(.*?)\];", gas_source, flags=re.DOTALL
    )
    assert header_block is not None
    gas_columns = tuple(re.findall(r"'([^']+)'", header_block.group(1)))
    assert gas_columns == EVENT_COLUMNS


def test_failed_event_is_recorded_and_retried(tmp_path):
    db = state_with_event(tmp_path)
    failed = adapter(db, FakeSheets(fail=True)).export(dry_run=False)
    good = FakeSheets(); retried = adapter(db, good).export(dry_run=False)
    assert failed.status == "completed_with_errors"
    assert retried.events_exported == 1
    assert [call[0] for call in good.calls] == ["bucoliche"]
    with closing(sqlite3.connect(db)) as conn:
        assert conn.execute("SELECT export_result FROM local_export_status").fetchone()[0] == "exported"


def test_conflicts_are_appended_once_to_the_unified_register(tmp_path):
    fake = FakeSheets()
    result = adapter(state_with_event(tmp_path, "conflict_hash_mismatch"), fake).export(dry_run=False)
    assert result.conflicts_pending == 1
    assert [call[0] for call in fake.calls] == ["bucoliche"]
    assert fake.calls[0][1] == EVENT_COLUMNS


def test_conflict_retry_does_not_duplicate_unified_register_append(tmp_path):
    db = state_with_event(tmp_path, "conflict_hash_mismatch")
    first = FakeSheets(); adapter(db, first).export(dry_run=False)
    retry = FakeSheets(); adapter(db, retry).export(dry_run=False)
    assert [call[0] for call in first.calls] == ["bucoliche"]
    assert retry.calls == []


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
    assert [call[0] for call in fake.calls] == ["bucoliche", "bucoliche"]


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
    assert fake.calls == []


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


def test_local_state_consolidates_same_fingerprint_from_two_machine_ids(tmp_path):
    db = tmp_path / "state.db"
    store = ReadonlyStateStore(db); store.initialize()
    for machine_id, suffix, action, status in (
        ("machine-a", "1", "attachment_quarantined", "ready_for_caronte"),
        ("machine-b", "2", "message_completed", "ready_for_caronte"),
    ):
        with closing(sqlite3.connect(db)) as conn:
            conn.execute("""INSERT INTO runs(started_at,dry_run,status,account_alias)
                VALUES('now',0,'completed','box')""")
            run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("""INSERT INTO messages(run_id,account_alias,mailbox,uidvalidity,message_uid,
                message_id,subject,sender,message_date) VALUES(?,?,?,?,?,?,?,?,?)""",
                (run_id, "box", "INBOX", "1", f"9{suffix}", f"<m-{suffix}@example.invalid>", "Subject",
                 "sender@example.invalid", f"2026-06-30T00:00:0{suffix}+00:00"))
            message_row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("""INSERT INTO attachments(message_id,account_alias,attachment_id,source_email,
                ordinal,original_filename,sanitized_filename,declared_mime_type,size_bytes,sha256,
                status,reason,fingerprint,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (message_row_id, "box", f"att-{suffix}", "box@example.invalid", 1, f"a-{suffix}.pdf",
                 f"a-{suffix}.pdf", "application/pdf", 1, "a" * 64, status,
                 "test", "f" * 64, f"2026-06-30T00:00:0{suffix}+00:00"))
            conn.commit()
        store.add_audit_event(machine_id=machine_id, account_alias="box",
            entity_type="attachment", entity_id=f"att-{suffix}", fingerprint="f" * 64,
            action=action, status=status, details={"machine": machine_id})
    fake = FakeSheets()
    state = adapter(db, fake).refresh_state(dry_run=False)
    assert state.status == "local_only" and len(state.preview) == 1
    assert fake.calls == []
    row = state.preview[0]
    assert row["fingerprint"] == "f" * 64
    assert row["machine_id"] == "machine-a,machine-b"
    assert row["current_global_state"] == "completed"
    assert json.loads(row["notes"]) == {
        "machine": "machine-b",
        "machine_ids": ["machine-a", "machine-b"],
        "cross_machine": True,
    }


def test_local_state_marks_cross_machine_conflict_for_terminal_state_collision(tmp_path):
    db = tmp_path / "state.db"
    store = ReadonlyStateStore(db); store.initialize()
    for machine_id, suffix, action, status in (
        ("machine-a", "1", "message_completed", "ready_for_caronte"),
        ("machine-b", "2", "failed", "error"),
    ):
        with closing(sqlite3.connect(db)) as conn:
            conn.execute("""INSERT INTO runs(started_at,dry_run,status,account_alias)
                VALUES('now',0,'completed','box')""")
            run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("""INSERT INTO messages(run_id,account_alias,mailbox,uidvalidity,message_uid,
                message_id,subject,sender,message_date) VALUES(?,?,?,?,?,?,?,?,?)""",
                (run_id, "box", "INBOX", "1", f"7{suffix}", f"<m-{suffix}@example.invalid>", "Subject",
                 "sender@example.invalid", f"2026-06-30T00:00:0{suffix}+00:00"))
            message_row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("""INSERT INTO attachments(message_id,account_alias,attachment_id,source_email,
                ordinal,original_filename,sanitized_filename,declared_mime_type,size_bytes,sha256,
                status,reason,fingerprint,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (message_row_id, "box", f"att-{suffix}", "box@example.invalid", 1, f"a-{suffix}.pdf",
                 f"a-{suffix}.pdf", "application/pdf", 1, "a" * 64, status,
                 "test", "f" * 64, f"2026-06-30T00:00:0{suffix}+00:00"))
            conn.commit()
        store.add_audit_event(machine_id=machine_id, account_alias="box",
            entity_type="attachment", entity_id=f"att-{suffix}", fingerprint="f" * 64,
            action=action, status=status, details={"machine": machine_id})
    fake = FakeSheets()
    state = adapter(db, fake).refresh_state(dry_run=False)
    assert state.status == "local_only" and fake.calls == []
    row = state.preview[0]
    assert row["current_global_state"] == "conflict"
    assert row["conflict_type"] == "conflict_cross_machine"
    assert row["machine_id"] == "machine-a,machine-b"
    assert json.loads(row["notes"]) == {
        "machine": "machine-b",
        "machine_ids": ["machine-a", "machine-b"],
        "cross_machine": True,
        "cross_machine_conflict": True,
        "machine_states": {
            "machine-a": "completed",
            "machine-b": "failed",
        },
    }


def test_refresh_state_uses_latest_event_so_staged_wins_on_acquired(tmp_path):
    db = tmp_path / "state.db"
    store = ReadonlyStateStore(db); store.initialize()
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("""INSERT INTO runs(started_at,dry_run,status,account_alias)
            VALUES('now',0,'completed','box')""")
        run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""INSERT INTO messages(run_id,account_alias,mailbox,uidvalidity,message_uid,
            message_id,subject,sender,message_date) VALUES(?,?,?,?,?,?,?,?,?)""",
            (run_id, "box", "INBOX", "1", "42", "<m@example.invalid>", "Subject",
             "sender@example.invalid", "2026-06-30T08:00:00+00:00"))
        message_row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""INSERT INTO attachments(message_id,account_alias,attachment_id,source_email,
            ordinal,original_filename,sanitized_filename,declared_mime_type,size_bytes,sha256,
            status,reason,fingerprint,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (message_row_id, "box", "att-1", "box@example.invalid", 1, "doc.pdf", "doc.pdf",
             "application/pdf", 1, "a" * 64, "staged_storage", "test", "f" * 64,
             "2026-06-30T08:00:00+00:00"))
        conn.commit()
    store.add_audit_event(machine_id="machine-test", account_alias="box",
        entity_type="attachment", entity_id="att-1", fingerprint="f" * 64,
        action="attachment_quarantined", status="queued", details={"step": "acquired"})
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("""UPDATE audit_events SET created_at=? WHERE entity_id=? AND action=?""",
            ("2026-06-30T08:00:00+00:00", "att-1", "attachment_quarantined"))
        conn.commit()
    store.add_audit_event(machine_id="machine-test", account_alias="box",
        entity_type="attachment", entity_id="att-1", fingerprint="f" * 64,
        action="attachment_staged", status="ok", details={"step": "staged"})
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("""UPDATE audit_events SET created_at=? WHERE entity_id=? AND action=?""",
            ("2026-06-30T09:00:00+00:00", "att-1", "attachment_staged"))
        conn.commit()
    row = adapter(db, FakeSheets(), enabled=False).refresh_state(dry_run=True).preview[0]
    assert row["current_global_state"] == "staged"
    assert row["last_result"] == "ok"


def test_refresh_state_uses_latest_event_so_completed_wins_on_staged(tmp_path):
    db = tmp_path / "state.db"
    store = ReadonlyStateStore(db); store.initialize()
    store.add_audit_event(machine_id="machine-test", account_alias="box",
        entity_type="attachment", entity_id="att-1", fingerprint="f" * 64,
        action="attachment_staged", status="ok", details={"step": "staged"})
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("""UPDATE audit_events SET created_at=? WHERE entity_id=? AND action=?""",
            ("2026-06-30T09:00:00+00:00", "att-1", "attachment_staged"))
        conn.commit()
    store.add_audit_event(machine_id="machine-test", account_alias="box",
        entity_type="attachment", entity_id="att-1", fingerprint="f" * 64,
        action="message_completed", status="ok", details={"step": "completed"})
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("""UPDATE audit_events SET created_at=? WHERE entity_id=? AND action=?""",
            ("2026-06-30T10:00:00+00:00", "att-1", "message_completed"))
        conn.commit()
    row = adapter(db, FakeSheets(), enabled=False).refresh_state(dry_run=True).preview[0]
    assert row["current_global_state"] == "completed"
    assert row["notes"] == '{"step":"completed"}'


def test_end_to_end_transitions_export_once_and_unchanged_retry_is_stable(tmp_path):
    class IsolatedScanMailbox(FakeMailbox):
        instances = []

    class IsolatedProcessMailbox(FakeProcessMailbox):
        instances = []

    class IsolatedAckMailbox(FakeAckMailbox):
        instances = []

    class ArchivedStatus:
        @staticmethod
        def statuses(inbox_ids):
            return {inbox_id: "archiviato" for inbox_id in inbox_ids}

    staging = tmp_path / "staging"
    staging.mkdir()
    config = write_storage_config(tmp_path, staging)
    accounts = load_multi_account_config(config)[:1]
    storage_config = load_storage_config(config)
    paths = LocalDataPaths(tmp_path / ".local_data")

    fake = FakeSheets()

    def runner():
        return LocalPipelineRunner(
            accounts,
            paths=paths,
            config_path=config,
            scanner_factory=lambda: MultiAccountReadonlyScanner(
                accounts,
                paths=paths,
                environ={
                    "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "user@example.invalid",
                    "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "secret",
                },
                mailbox_factory=lambda account, root: IsolatedScanMailbox(account, root),
            ),
            processor_factory=lambda: MultiAccountImapProcessor(
                accounts,
                paths=paths,
                environ={
                    "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "user@example.invalid",
                    "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "secret",
                },
                mailbox_factory=lambda account, root: IsolatedProcessMailbox(account, root),
                scanner=FakeScanner(ScanVerdict.CLEAN),
            ),
            storage_factory=lambda: LocalFilesystemStorageAdapter(
                state_db=paths.state_db,
                local_data_root=paths.root,
                config=storage_config,
            ),
            handoff_factory=lambda: OperationalHandoffRunner(
                paths=paths,
                staging_root=staging,
                verifier=FakeVerifier(),
                intake=FakeIntake(),
            ),
            registry_export_factory=lambda: BucolicheAppendOnlyAdapter(
                state_db=paths.state_db,
                config=BucolicheConfig(enabled=True),
                client=fake,
                environ={},
            ),
            completion_factory=lambda: LocalCompletionRunner(
                accounts,
                paths=paths,
                environ={
                    "VIRGILIO_IMAP_ACCOUNT_1_USERNAME": "user@example.invalid",
                    "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD": "secret",
                },
                mailbox_factory=lambda account: IsolatedAckMailbox(account),
                require_da_archiviare=True,
                archive_status_client=ArchivedStatus(),
            ),
        )

    first_pipeline = runner().run(dry_run=False)
    with sqlite3.connect(paths.state_db) as db:
        after_first = db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
    second_pipeline = runner().run(dry_run=False)
    with sqlite3.connect(paths.state_db) as db:
        after_second = db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
    third_pipeline = runner().run(dry_run=False)
    with sqlite3.connect(paths.state_db) as db:
        after_third = db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
        actions = [row[0] for row in db.execute(
            "SELECT action FROM audit_events ORDER BY id"
        )]

    assert first_pipeline.status == "completed"
    assert second_pipeline.status == "completed"
    assert third_pipeline.status == "completed"
    assert after_first == after_second == after_third == 10
    assert actions.count("message_scanned") == 2
    assert actions.count("attachment_quarantined") == 2
    assert actions.count("attachment_staged") == 2
    assert actions.count("da_archiviare_intake") == 2
    assert actions.count("message_completed") == 2
    assert [call[0] for call in fake.calls].count("bucoliche") == 8


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
  events_sheet: Bucoliche_Eventi
  state_sheet: Bucoliche_Stato
  conflicts_sheet: Bucoliche_Conflitti
""", encoding="utf-8")
    config = load_bucoliche_config(path)
    assert config.enabled is False and config.append_only is True
    assert config.events_sheet == "bucoliche"
    assert not hasattr(config, "state_sheet") and not hasattr(config, "conflicts_sheet")


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


def test_refresh_bucoliche_state_dry_run_returns_state_preview_without_event_append(tmp_path):
    db = tmp_path / "state.db"
    store = ReadonlyStateStore(db); store.initialize()
    store.add_audit_event(machine_id="machine-test", account_alias="box",
        entity_type="attachment", entity_id="att-1", fingerprint="f" * 64,
        action="message_completed", status="ok", details={"step": "done"})
    fake = FakeSheets()
    result = adapter(db, fake, enabled=False).refresh_state(dry_run=True)
    assert result.status == "dry_run"
    assert result.state_rows_total == 1
    assert result.preview[0]["current_global_state"] == "completed"
    assert fake.calls == []


def test_refresh_bucoliche_state_real_run_stays_local(tmp_path):
    db = state_with_event(tmp_path)
    fake = FakeSheets()
    result = adapter(db, fake).refresh_state(dry_run=False)
    assert result.status == "local_only"
    assert result.state_rows_total == 1
    assert fake.calls == []
    with closing(sqlite3.connect(db)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM local_export_status").fetchone()[0] == 0


def test_refresh_bucoliche_state_exposes_local_timestamp_and_state_paths(tmp_path):
    db = tmp_path / "state.db"
    store = ReadonlyStateStore(db); store.initialize()
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("""INSERT INTO runs(started_at,dry_run,status,account_alias)
            VALUES('now',0,'completed','box')""")
        run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""INSERT INTO messages(run_id,account_alias,mailbox,uidvalidity,message_uid,
            message_id,subject,sender,message_date,source_email) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (run_id, "box", "INBOX", "1", "42", "<m@example.invalid>", "Subject",
             "sender@example.invalid", "2026-06-30T10:00:00+00:00", "box@example.invalid"))
        message_row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""INSERT INTO attachments(message_id,account_alias,attachment_id,source_email,
            ordinal,original_filename,sanitized_filename,declared_mime_type,size_bytes,sha256,
            status,reason,fingerprint,staged_filename,staged_path,manifest_path,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (message_row_id, "box", "att-1", "box@example.invalid", 1, "doc.pdf", "doc.pdf",
             "application/pdf", 1, "a" * 64, "staged_storage", "test", "f" * 64,
             "doc-final.pdf", "C:/tmp/doc-final.pdf", "C:/tmp/doc-final.json",
             "2026-06-30T10:00:00+00:00"))
        conn.execute("""INSERT INTO audit_events(created_at,machine_id,account_alias,entity_type,
            entity_id,fingerprint,action,status,details_json) VALUES(?,?,?,?,?,?,?,?,?)""",
            ("2026-06-30T10:00:00+00:00", "machine-test", "box", "attachment", "att-1",
             "f" * 64, "attachment_staged", "ok", '{"step":"staged"}'))
        conn.commit()
    row = adapter(db, FakeSheets(), enabled=False).refresh_state(dry_run=True).preview[0]
    rome = ZoneInfo("Europe/Rome")
    expected = datetime.fromisoformat("2026-06-30T10:00:00+00:00").astimezone(rome)
    actual = datetime.fromisoformat(row["last_event_at"])
    assert actual.tzinfo is not None
    assert actual.utcoffset() == expected.utcoffset()
    assert actual.astimezone(rome).replace(microsecond=0) == expected.replace(microsecond=0)
    assert row["staged_filename"] == "doc-final.pdf"
    assert row["staged_path"] == "C:/tmp/doc-final.pdf"
    assert row["manifest_path"] == "C:/tmp/doc-final.json"


def test_refresh_bucoliche_state_cli_dry_run(tmp_path, monkeypatch, capsys):
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
    monkeypatch.setattr(sys, "argv", ["virgilio_connector", "refresh-bucoliche-state",
        "--config", str(config), "--dry-run"])
    from virgilio_connector.__main__ import main
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["state_rows_total"] == 1
    assert payload["preview"][0]["fingerprint"] == "f" * 64


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


def test_build_google_sheets_client_reports_clear_oauth_refresh_error(tmp_path, monkeypatch):
    secret = tmp_path / "client.json"; secret.write_text("{}", encoding="utf-8")
    token = tmp_path / "token.json"; token.write_text("{}", encoding="utf-8")

    class FailingCredentials:
        expired = True
        refresh_token = "refresh-secret"
        valid = False

        @classmethod
        def from_authorized_user_file(cls, *_args, **_kwargs):
            return cls()

        def refresh(self, _request):
            raise RuntimeError("offline")

    monkeypatch.setitem(sys.modules, "google.oauth2.credentials",
        type("CredentialsModule", (), {"Credentials": FailingCredentials}))
    monkeypatch.setitem(sys.modules, "google.auth.transport.requests",
        type("RequestsModule", (), {"Request": object}))
    with pytest.raises(BucolicheError, match="OAuth token refresh failed"):
        build_google_sheets_client(BucolicheConfig(credentials_mode="user_oauth_local"), {
            "VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "sheet-id",
            "VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH": str(secret),
            "VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH": str(token),
        })
