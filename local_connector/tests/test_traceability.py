import json
from pathlib import Path
import sqlite3

from virgilio_connector.readonly_state import ReadonlyStateStore, ensure_state_db
from virgilio_connector.traceability import (
    LocalConflictChecker, audit_entry, export_central_events, global_fingerprint,
    load_machine_id, load_rules,
)


def test_fingerprint_is_deterministic_and_path_free():
    first = global_fingerprint("box", "<m>", "1", "a-1", "f" * 64)
    second = global_fingerprint("box", "<m>", "1", "a-1", "f" * 64)
    assert first == second
    assert "path" not in first


def test_machine_id_is_stable(tmp_path):
    assert load_machine_id(tmp_path) == load_machine_id(tmp_path)


def test_rules_include_and_exclude(tmp_path):
    config = tmp_path / "a.yaml"
    config.write_text('''rules:
  default_action: exclude
  include:
    - name: invoices
      subject_contains: ["invoice"]
      filename_extensions: [".pdf"]
  exclude:
    - name: newsletter
      from_contains: ["noreply"]
''', encoding="utf-8")
    rules = load_rules(config)
    assert rules.decide(subject="Invoice 1", sender="x", filename="a.pdf", size_bytes=20)[0]
    decision = rules.decide(subject="x", sender="noreply@test", filename="a.pdf", size_bytes=20)
    assert decision[:2] == (False, "newsletter")


def test_audit_sqlite_export_and_no_secrets(tmp_path):
    db = tmp_path / "state.db"
    store = ReadonlyStateStore(db); store.initialize()
    machine = load_machine_id(tmp_path)
    with sqlite3.connect(db) as conn:
        conn.execute("""INSERT INTO runs(started_at,dry_run,status,account_alias)
            VALUES('now',0,'completed','box')""")
        run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""INSERT INTO messages(run_id,account_alias,mailbox,uidvalidity,message_uid,
            message_id,subject,sender,message_date) VALUES(?,?,?,?,?,?,?,?,?)""",
            (run_id, "box", "INBOX", "1", "42", "<m@example.invalid>", "Subject",
             "sender@example.invalid", "2026-06-30T00:00:00+00:00"))
        message_row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""INSERT INTO attachments(message_id,account_alias,attachment_id,source_email,
            ordinal,original_filename,sanitized_filename,declared_mime_type,size_bytes,sha256,
            status,reason,fingerprint,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (message_row_id, "box", "a1", "box@example.invalid", 1, "a.pdf", "a.pdf",
             "application/pdf", 1, "a" * 64, "ready_for_caronte", "test", "f" * 64, "now"))
        conn.commit()
    store.add_audit_event(machine_id=machine, account_alias="box", entity_type="attachment",
        entity_id="a1", fingerprint="f" * 64, action="attachment_quarantined",
        status="quarantined_unverified", details={"reason": "test"})
    target = export_central_events(db, tmp_path, "jsonl")
    payload = json.loads(target.read_text(encoding="utf-8").splitlines()[0])
    assert payload["machine_id"] == machine
    assert payload["fingerprint"] == "f" * 64
    text = json.dumps(payload).lower()
    assert not any(word in text for word in ("password", "token", "base64", "file_bytes"))


def test_export_skips_legacy_attachment_without_attachment_id(tmp_path):
    root = tmp_path / ".local_data"
    db = root / "state.db"
    store = ReadonlyStateStore(db); store.initialize()
    machine = load_machine_id(root)
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
    warnings = ensure_state_db(root)[1]
    store.add_audit_event(machine_id=machine, account_alias="box", entity_type="attachment",
        entity_id="legacy-missing-id", fingerprint="f" * 64, action="attachment_quarantined",
        status="ready_for_caronte", details={"reason": "legacy"})
    target = export_central_events(db, root, "jsonl")
    assert warnings and warnings[0].startswith("legacy_incomplete")
    assert target.read_text(encoding="utf-8") == ""


def test_conflict_checker_empty_database_ok(tmp_path):
    db = tmp_path / "state.db"
    ReadonlyStateStore(db).initialize()
    assert LocalConflictChecker(db).check()["status"] == "OK"


def test_audit_entry_shape_has_machine_and_is_safe():
    item = audit_entry("machine", "manifest_created", "created", "box", "attachment", "a1")
    assert item["machine_id"] == "machine"
    assert "password" not in json.dumps(item).lower()
