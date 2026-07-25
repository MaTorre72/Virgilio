from hashlib import sha256
import json
from pathlib import Path
import sqlite3

import pytest

from virgilio_connector.local_paths import LocalDataPaths
from virgilio_connector.ports import MessageReference
from virgilio_connector.readonly_state import ReadonlyStateStore
from virgilio_connector.staging_transport import (
    LocalDriveStagingConfig,
    LocalDriveStagingTransport,
    NoReadyFilesError,
    StagingDirectoryError,
    StagingDisabledError,
    StagingTransportError,
)


PAYLOAD = b"synthetic-ready-file"
DIGEST = sha256(PAYLOAD).hexdigest()


def fixture(tmp_path: Path, *, status="ready_for_caronte", enabled=True,
            staging_exists=True, writable_check=None):
    paths = LocalDataPaths(tmp_path / ".local_data")
    paths.create()
    source_dir = paths.ready / "123-42"
    source_dir.mkdir()
    source = source_dir / "001-report.pdf"
    source.write_bytes(PAYLOAD)
    store = ReadonlyStateStore(paths.state_db)
    store.initialize()
    run_id = store.start_run()
    message_id = store.add_message(run_id, MessageReference(
        "Virgilio/da-traghettare", "123", "42", "<test@example.invalid>",
        "Synthetic", "sender@example.invalid", "2026-06-23T10:00:00+02:00"))
    attachment_id = store.add_attachment(
        message_id, ordinal=1, original_filename="report.pdf",
        sanitized_filename="report.pdf", declared_mime_type="application/pdf",
        size_bytes=len(PAYLOAD), sha256=DIGEST, status=status,
        relative_path=source.relative_to(paths.root).as_posix(), duplicate_of_id=None,
        reason="synthetic", scanner_engine="windows_defender", scan_result="clean")
    store.complete_run(run_id, messages_seen=1, attachments_seen=1)
    staging = tmp_path / "Drive Desktop" / "Virgilio Limbo"
    if staging_exists:
        staging.mkdir(parents=True)
    kwargs = {}
    if writable_check is not None:
        kwargs["writable_check"] = writable_check
    transport = LocalDriveStagingTransport(
        state_db=paths.state_db, local_data_root=paths.root,
        config=LocalDriveStagingConfig(enabled, staging), **kwargs)
    return transport, paths, staging, source, attachment_id


def test_staging_disabled(tmp_path):
    transport, *_ = fixture(tmp_path, enabled=False)
    with pytest.raises(StagingDisabledError):
        transport.stage_ready_files(dry_run=True)


def test_staging_directory_not_configured(tmp_path):
    transport, paths, _, _, _ = fixture(tmp_path)
    transport = LocalDriveStagingTransport(
        state_db=paths.state_db, local_data_root=paths.root,
        config=LocalDriveStagingConfig(True, None))
    with pytest.raises(StagingDirectoryError, match="not configured"):
        transport.stage_ready_files(dry_run=True)


def test_staging_directory_missing(tmp_path):
    transport, *_ = fixture(tmp_path, staging_exists=False)
    with pytest.raises(StagingDirectoryError, match="does not exist"):
        transport.stage_ready_files(dry_run=True)


def test_staging_directory_must_be_absolute(tmp_path):
    _, paths, _, _, _ = fixture(tmp_path)
    transport = LocalDriveStagingTransport(
        state_db=paths.state_db, local_data_root=paths.root,
        config=LocalDriveStagingConfig(True, Path("relative-staging")))
    with pytest.raises(StagingDirectoryError, match="absolute"):
        transport.stage_ready_files(dry_run=True)


def test_staging_directory_cannot_be_inside_quarantine(tmp_path):
    _, paths, _, _, _ = fixture(tmp_path)
    transport = LocalDriveStagingTransport(
        state_db=paths.state_db, local_data_root=paths.root,
        config=LocalDriveStagingConfig(True, paths.ready))
    with pytest.raises(StagingDirectoryError, match="outside"):
        transport.stage_ready_files(dry_run=True)


def test_staging_directory_not_writable(tmp_path):
    transport, *_ = fixture(tmp_path, writable_check=lambda path, mode: False)
    with pytest.raises(StagingDirectoryError, match="not writable"):
        transport.stage_ready_files(dry_run=True)


def test_non_ready_file_is_ignored(tmp_path):
    transport, *_ = fixture(tmp_path, status="quarantined_unverified")
    with pytest.raises(NoReadyFilesError):
        transport.stage_ready_files(dry_run=True)


def test_ready_file_and_manifest_are_copied_with_verified_hash(tmp_path):
    transport, paths, staging, source, attachment_row_id = fixture(tmp_path)
    result = transport.stage_ready_files(dry_run=False)[0]
    staged = staging / result.staged_filename
    manifest_path = staging / result.manifest_filename
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert staged.read_bytes() == PAYLOAD
    assert sha256(staged.read_bytes()).hexdigest() == DIGEST == result.sha256
    assert manifest["attachment_id"] == result.attachment_id
    assert manifest["staged_filename"] == result.staged_filename
    assert manifest["sha256"] == DIGEST
    assert manifest["source_message_uid"] == "42"
    assert manifest["account_alias"] == "default"
    assert manifest["dry_run"] is False
    assert "sync cloud non verificata" in manifest["note"]
    assert source.exists(), "quarantine source must never be deleted"
    with sqlite3.connect(paths.state_db) as db:
        row = db.execute("SELECT status,staged_filename FROM attachments WHERE id=?",
                         (attachment_row_id,)).fetchone()
    assert row == ("staged_local_drive", result.staged_filename)


def test_existing_name_is_not_overwritten(tmp_path):
    transport, _, staging, _, _ = fixture(tmp_path)
    existing = staging / "att-123-42-1-report.pdf"
    existing.write_bytes(b"keep-me")
    result = transport.stage_ready_files(dry_run=False)[0]
    assert existing.read_bytes() == b"keep-me"
    assert result.staged_filename != existing.name


def test_dry_run_writes_nothing_and_does_not_modify_sqlite(tmp_path):
    transport, paths, staging, source, _ = fixture(tmp_path)
    before = sha256(paths.state_db.read_bytes()).hexdigest()
    result = transport.stage_ready_files(dry_run=True)[0]
    after = sha256(paths.state_db.read_bytes()).hexdigest()
    assert result.dry_run is True
    assert result.copied is False
    assert not list(staging.iterdir())
    assert source.exists()
    assert before == after


def test_hash_mismatch_marks_staging_failed_without_deleting_source(tmp_path):
    transport, paths, _, source, attachment_row_id = fixture(tmp_path)
    source.write_bytes(b"changed-after-scan")
    with pytest.raises(StagingTransportError):
        transport.stage_ready_files(dry_run=False)
    assert source.exists()
    with sqlite3.connect(paths.state_db) as db:
        status = db.execute("SELECT status FROM attachments WHERE id=?",
                            (attachment_row_id,)).fetchone()[0]
    assert status == "staging_failed"


def test_stage_ready_files_uses_each_attachment_account_alias_and_all_completed_runs(tmp_path):
    transport, paths, staging, _, _ = fixture(tmp_path)
    source_dir = paths.root / "accounts" / "account_2" / "quarantine" / "ready" / "222-99"
    source_dir.mkdir(parents=True)
    source = source_dir / "001-second.pdf"
    source.write_bytes(PAYLOAD)
    store = ReadonlyStateStore(paths.state_db)
    run_id = store.start_run(account_alias="account_2")
    message_id = store.add_message(run_id, MessageReference(
        "INBOX", "222", "99", "<second@example.invalid>",
        "Synthetic second", "sender@example.invalid", "2026-06-23T10:05:00+02:00"),
        account_alias="account_2")
    store.add_attachment(
        message_id, ordinal=1, original_filename="second.pdf",
        sanitized_filename="second.pdf", declared_mime_type="application/pdf",
        size_bytes=len(PAYLOAD), sha256=DIGEST, status="ready_for_caronte",
        relative_path=source.relative_to(paths.root).as_posix(), duplicate_of_id=None,
        reason="synthetic", scanner_engine="windows_defender", scan_result="clean",
        account_alias="account_2", attachment_id="account_2-222-99-1")
    store.complete_run(run_id, messages_seen=1, attachments_seen=1)

    results = transport.stage_ready_files(dry_run=False)
    assert len(results) == 2
    manifests = {}
    for result in results:
        manifest = json.loads((staging / result.manifest_filename).read_text(encoding="utf-8"))
        manifests[manifest["account_alias"]] = manifest

    assert set(manifests) == {"default", "account_2"}
    assert manifests["default"]["source_message_uid"] == "42"
    assert manifests["account_2"]["source_message_uid"] == "99"


def test_module_has_no_network_caronte_or_gmail_dependency():
    source = Path(__file__).parents[1] / "src" / "virgilio_connector" / "staging_transport.py"
    text = source.read_text(encoding="utf-8")
    for forbidden in ("urllib", "requests", "httpx", "Caronte", "Gmail", "imaplib"):
        assert forbidden not in text
