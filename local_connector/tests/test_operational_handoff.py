import json
import sqlite3
from dataclasses import replace
from types import SimpleNamespace

from virgilio_connector.da_archiviare_intake import (
    DA_ARCHIVIARE_INTAKE_ACTION,
    DaArchiviareIntakeClientError,
    DaArchiviareIntakeResponse,
)
from virgilio_connector.local_paths import LocalDataPaths
from virgilio_connector.operational_handoff import OperationalHandoffRunner
from virgilio_connector.readonly_state import ensure_state_db
from virgilio_connector.storage_adapter import StorageStageResult


def _staged(tmp_path, *, ordinal="0001"):
    staging_root = tmp_path / "Limbo"
    filename = f"documento-{ordinal}.pdf"
    attachment_id = f"att-{ordinal}"
    manifest_path = staging_root / "account_1" / f"{filename}.manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({
        "connector_type": "local_imap",
        "account_alias": "account_1",
        "source_message_id": "<message@example.invalid>",
        "source_message_uid": "42",
        "attachment_id": attachment_id,
        "fingerprint": ordinal[-1] * 64,
        "original_filename": filename,
        "staged_filename": filename,
        "sha256": "a" * 64,
        "size_bytes": 4,
        "scan_result": "clean",
        "quarantine_status": "ready_for_caronte",
        "dry_run": False,
    }), encoding="utf-8")
    result = StorageStageResult(
        attachment_id=attachment_id,
        account_alias="account_1",
        source_relative_path="quarantine/documento.pdf",
        staged_path=f"account_1/{filename}",
        staged_manifest_path=f"account_1/{filename}.manifest.json",
        sha256="a" * 64,
        size_bytes=4,
        dry_run=False,
        copied=True,
        status="staged_storage",
        message="staged",
    )
    return staging_root, result


class FakeVerifier:
    def __init__(self, *, visible=True, error=None):
        self.visible = visible
        self.error = error
        self.calls = []

    def verify_manifest(self, manifest_path):
        self.calls.append(manifest_path)
        if self.error:
            raise self.error
        return SimpleNamespace(
            cloud_visible=self.visible,
            drive_file_id="drive-123" if self.visible else "",
            manifest_file_id="manifest-123" if self.visible else "",
            message="visible" if self.visible else "not visible",
            errors=() if self.visible else ({"code": "NOT_FOUND"},),
        )


class FakeIntake:
    def __init__(self, *, response=None, error=None):
        self.response = response or DaArchiviareIntakeResponse(
            ok=True,
            action=DA_ARCHIVIARE_INTAKE_ACTION,
            inbox_id="inbox-123",
            created=True,
            updated=False,
            idempotent=False,
            row=2,
            message="created",
            errors=(),
            form_url="https://example.invalid/exec?inbox_id=inbox-123",
            notification_status="sent",
        )
        self.error = error
        self.calls = []

    def create_record(self, manifest_path, *, drive_file_id, manifest_file_id, form_url=""):
        self.calls.append((manifest_path, drive_file_id, manifest_file_id, form_url))
        if self.error:
            raise self.error
        return self.response


def _runner(tmp_path, verifier, intake, **runner_options):
    paths = LocalDataPaths(tmp_path / "local-data")
    ensure_state_db(paths.root)
    staging_root, staged = _staged(tmp_path)
    options = {"verify_timeout_seconds": 0, **runner_options}
    return (
        OperationalHandoffRunner(
            paths=paths,
            staging_root=staging_root,
            verifier=verifier,
            intake=intake,
            **options,
        ),
        paths,
        staged,
    )


def test_handoff_verifies_then_intakes_and_retry_is_local_idempotent(tmp_path):
    verifier = FakeVerifier()
    intake = FakeIntake()
    runner, paths, staged = _runner(tmp_path, verifier, intake)

    first = runner.deliver((staged,), dry_run=False)
    second = runner.deliver((staged,), dry_run=False)

    assert first[0].status == "created"
    assert first[0].inbox_id == "inbox-123"
    assert first[0].form_url == "https://example.invalid/exec?inbox_id=inbox-123"
    assert first[0].notification_status == "sent"
    assert second[0].status == "already_delivered"
    assert len(verifier.calls) == 1
    assert len(intake.calls) == 1
    assert intake.calls[0][1:3] == ("drive-123", "manifest-123")
    with sqlite3.connect(paths.state_db) as db:
        rows = db.execute(
            """SELECT status,details_json FROM audit_events
               WHERE action='da_archiviare_intake' ORDER BY id"""
        ).fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "created"
    assert json.loads(rows[0][1])["inbox_id"] == "inbox-123"
    assert json.loads(rows[0][1])["form_url"] == "https://example.invalid/exec?inbox_id=inbox-123"


def test_handoff_waits_for_cloud_without_calling_intake(tmp_path):
    verifier = FakeVerifier(visible=False)
    intake = FakeIntake()
    runner, paths, staged = _runner(tmp_path, verifier, intake)

    result = runner.deliver((staged,), dry_run=False)

    assert result[0].status == "waiting"
    assert intake.calls == []
    with sqlite3.connect(paths.state_db) as db:
        status = db.execute(
            "SELECT status FROM audit_events ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
    assert status == "waiting"


def test_handoff_retries_with_bounded_backoff_and_never_repeats_intake(tmp_path):
    class Clock:
        now = 0.0
        sleeps = []

        def __call__(self):
            return self.now

        def sleep(self, seconds):
            self.sleeps.append(seconds)
            self.now += seconds

    class EventuallyVisible(FakeVerifier):
        def verify_manifest(self, manifest_path):
            self.calls.append(manifest_path)
            visible = len(self.calls) >= 3
            return SimpleNamespace(
                cloud_visible=visible,
                drive_file_id="drive-123" if visible else "",
                manifest_file_id="manifest-123" if visible else "",
                message="visible" if visible else "not visible",
                errors=() if visible else ({"code": "NOT_FOUND"},),
            )

    clock = Clock()
    verifier = EventuallyVisible()
    intake = FakeIntake()
    runner, _, staged = _runner(
        tmp_path, verifier, intake,
        verify_timeout_seconds=10,
        initial_backoff_seconds=1,
        max_backoff_seconds=4,
        clock=clock,
        sleeper=clock.sleep,
    )

    first = runner.deliver((staged,), dry_run=False)
    second = runner.deliver((staged,), dry_run=False)

    assert first[0].status == "created"
    assert second[0].status == "already_delivered"
    assert clock.sleeps == [1, 2]
    assert len(verifier.calls) == 3
    assert len(intake.calls) == 1


def test_waiting_already_staged_document_is_resumed_on_next_cycle(tmp_path):
    verifier = FakeVerifier(visible=False)
    intake = FakeIntake()
    runner, _, staged = _runner(tmp_path, verifier, intake)

    waiting = runner.deliver((staged,), dry_run=False)
    verifier.visible = True
    resumed = runner.deliver((replace(staged, status="already_staged"),), dry_run=False)
    repeated = runner.deliver((replace(staged, status="already_staged"),), dry_run=False)

    assert waiting[0].status == "waiting"
    assert resumed[0].status == "created"
    assert repeated[0].status == "already_delivered"
    assert len(intake.calls) == 1


def test_handoff_delivers_each_staged_attachment_once(tmp_path):
    verifier = FakeVerifier()
    intake = FakeIntake()
    runner, _, first = _runner(tmp_path, verifier, intake)
    _, second = _staged(tmp_path, ordinal="0002")

    results = runner.deliver((first, second), dry_run=False)

    assert [item.attachment_id for item in results] == ["att-0001", "att-0002"]
    assert [item.status for item in results] == ["created", "created"]
    assert len(verifier.calls) == 2
    assert len(intake.calls) == 2


def test_handoff_rejected_intake_is_a_failure(tmp_path):
    verifier = FakeVerifier()
    intake = FakeIntake(response=DaArchiviareIntakeResponse(
        ok=False,
        action=DA_ARCHIVIARE_INTAKE_ACTION,
        inbox_id="",
        created=False,
        updated=False,
        idempotent=False,
        row=0,
        message="rejected",
        errors=({"code": "REJECTED"},),
        form_url="",
        notification_status="failed",
    ))
    runner, _, staged = _runner(tmp_path, verifier, intake)

    result = runner.deliver((staged,), dry_run=False)

    assert result[0].status == "failed"


def test_handoff_failure_is_recorded_and_can_be_retried(tmp_path):
    verifier = FakeVerifier()
    intake = FakeIntake(error=DaArchiviareIntakeClientError("temporary failure"))
    runner, paths, staged = _runner(tmp_path, verifier, intake)

    failed = runner.deliver((staged,), dry_run=False)
    intake.error = None
    retried = runner.deliver((staged,), dry_run=False)

    assert failed[0].status == "failed"
    assert retried[0].status == "created"
    with sqlite3.connect(paths.state_db) as db:
        statuses = [
            row[0] for row in db.execute(
                """SELECT status FROM audit_events
                   WHERE action='da_archiviare_intake' ORDER BY id"""
            )
        ]
    assert statuses == ["failed", "created"]


def test_handoff_dry_run_does_not_use_network_or_write_audit(tmp_path):
    verifier = FakeVerifier(error=AssertionError("network not allowed"))
    intake = FakeIntake(error=AssertionError("network not allowed"))
    runner, paths, staged = _runner(tmp_path, verifier, intake)

    result = runner.deliver((staged,), dry_run=True)

    assert result[0].status == "planned"
    assert verifier.calls == []
    assert intake.calls == []
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0] == 0
