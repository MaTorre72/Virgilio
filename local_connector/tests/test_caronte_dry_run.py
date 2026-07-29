from hashlib import sha256
import json
from pathlib import Path

import pytest

from virgilio_connector.caronte_dry_run import (
    CaronteDryRunConfig,
    NoReadyAttachmentsError,
    generate_caronte_dry_run_files,
)
from virgilio_connector.contract import command_from_json
from virgilio_connector.ports import MessageReference
from virgilio_connector.readonly_state import ReadonlyStateStore


def create_state(tmp_path: Path, *, status="ready_for_caronte") -> Path:
    path = tmp_path / "state.db"
    store = ReadonlyStateStore(path)
    store.initialize()
    run_id = store.start_run()
    message_id = store.add_message(run_id, MessageReference(
        mailbox="Virgilio/da-traghettare", uidvalidity="123", message_uid="42",
        message_id="<test@example.invalid>", subject="Synthetic subject",
        sender="sender@example.invalid", date="2026-06-23T10:00:00+02:00"))
    store.add_attachment(message_id, ordinal=1, original_filename="report.pdf",
        sanitized_filename="report.pdf", declared_mime_type="application/pdf",
        size_bytes=4, sha256="a" * 64, status=status,
        relative_path="quarantine/ready/123-42/001-report.pdf",
        duplicate_of_id=None, reason="synthetic", scanner_engine="windows_defender",
        scan_result="clean")
    store.complete_run(run_id, messages_seen=1, attachments_seen=1)
    return path


def test_generates_strict_standard_dry_run_without_local_paths(tmp_path):
    state = create_state(tmp_path)
    before = sha256(state.read_bytes()).hexdigest()
    files = generate_caronte_dry_run_files(state, tmp_path / "commands",
        config=CaronteDryRunConfig("connector-test", "account-test", "gmail_imap"))
    after = sha256(state.read_bytes()).hexdigest()
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    command = command_from_json(files[0].read_bytes())
    assert command.dry_run is True
    assert command.user_confirmed_command is False
    assert command.attachments[0].scan_engine == "windows_defender"
    assert command.attachments[0].scan_result == "clean"
    assert payload["attachments"][0]["quarantine_status"] == "ready_for_caronte"
    assert "relative_path" not in files[0].read_text(encoding="utf-8")
    assert before == after


def test_unverified_attachments_are_never_emitted(tmp_path):
    state = create_state(tmp_path, status="quarantined_unverified")
    with pytest.raises(NoReadyAttachmentsError):
        generate_caronte_dry_run_files(state, tmp_path / "commands")
    assert not (tmp_path / "commands").exists()
