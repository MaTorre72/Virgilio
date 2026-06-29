import json
from pathlib import Path
import sqlite3

from virgilio_connector.readonly_state import ReadonlyStateStore
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
    store.add_audit_event(machine_id=machine, account_alias="box", entity_type="attachment",
        entity_id="a1", fingerprint="f" * 64, action="attachment_quarantined",
        status="quarantined_unverified", details={"reason": "test"})
    target = export_central_events(db, tmp_path, "jsonl")
    payload = json.loads(target.read_text(encoding="utf-8").splitlines()[0])
    assert payload["machine_id"] == machine
    assert payload["fingerprint"] == "f" * 64
    text = json.dumps(payload).lower()
    assert not any(word in text for word in ("password", "token", "base64", "file_bytes"))


def test_conflict_checker_empty_database_ok(tmp_path):
    db = tmp_path / "state.db"
    ReadonlyStateStore(db).initialize()
    assert LocalConflictChecker(db).check()["status"] == "OK"


def test_audit_entry_shape_has_machine_and_is_safe():
    item = audit_entry("machine", "manifest_created", "created", "box", "attachment", "a1")
    assert item["machine_id"] == "machine"
    assert "password" not in json.dumps(item).lower()
