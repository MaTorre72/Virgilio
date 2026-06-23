from hashlib import sha256
import json
import socket

import pytest

from virgilio_connector.drive_staging_verify import (
    DRIVE_STAGING_VERIFY_ACTION,
    DriveStagingVerifyClient,
    DriveStagingVerifyError,
    DriveStagingVerifyUrlNotConfigured,
)


def manifest_payload():
    return {
        "schema_version": "1.0",
        "connector_type": "local_imap",
        "attachment_id": "att-123-42-1-aaaaaaaaaaaa",
        "original_filename": "report.pdf",
        "sanitized_filename": "report.pdf",
        "staged_filename": "att-123-42-1-aaaaaaaaaaaa-report.pdf",
        "sha256": "a" * 64,
        "size_bytes": 4,
        "mime_type": "application/pdf",
        "scan_engine": "windows_defender",
        "scan_result": "clean",
        "quarantine_status": "ready_for_caronte",
        "source_message_id": "<test@example.invalid>",
        "source_message_uid": "42",
        "account_alias": "test",
        "staged_at": "2026-06-23T10:00:00+00:00",
        "dry_run": False,
        "note": "sync cloud non verificata",
    }


def response_payload(*, ok=True):
    manifest = manifest_payload()
    return {
        "ok": ok,
        "dry_run": True,
        "action": DRIVE_STAGING_VERIFY_ACTION,
        "attachment_id": manifest["attachment_id"],
        "staged_filename": manifest["staged_filename"],
        "file_found": ok,
        "manifest_found": ok,
        "manifest_consistent": ok,
        "cloud_visible": ok,
        "message": "visible" if ok else "not visible",
        "errors": [] if ok else [{"code": "NOT_FOUND", "message": "not visible"}],
    }


class FakeResponse:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self.body

    def close(self):
        pass


def write_manifest(tmp_path, payload=None):
    path = tmp_path / "file.pdf.manifest.json"
    path.write_text(json.dumps(payload or manifest_payload()), encoding="utf-8")
    return path


def test_valid_manifest_sends_only_metadata(tmp_path):
    captured = {}

    def opener(request, *, timeout):
        captured["body"] = request.data
        captured["timeout"] = timeout
        return FakeResponse(response_payload())

    result = DriveStagingVerifyClient(
        "https://example.invalid/exec", timeout_seconds=9, opener=opener
    ).verify_manifest(write_manifest(tmp_path))
    payload = json.loads(captured["body"].decode("utf-8"))
    assert result.cloud_visible is True
    assert captured["timeout"] == 9
    assert set(payload) == {
        "action", "dry_run", "attachment_id", "staged_filename", "sha256", "size_bytes"
    }
    serialized = captured["body"].decode("utf-8")
    for forbidden in ("local_path", "file_path", "file_bytes", "base64", '"content"', '"raw"'):
        assert forbidden not in serialized


def test_manifest_missing(tmp_path):
    client = DriveStagingVerifyClient("https://example.invalid/exec")
    with pytest.raises(DriveStagingVerifyError, match="not found"):
        client.verify_manifest(tmp_path / "missing.json")


def test_url_not_configured_attempts_no_network(tmp_path):
    calls = []
    client = DriveStagingVerifyClient(None, opener=lambda *args, **kwargs: calls.append(args))
    with pytest.raises(DriveStagingVerifyUrlNotConfigured, match="not configured"):
        client.verify_manifest(write_manifest(tmp_path))
    assert calls == []


@pytest.mark.parametrize("ok", [True, False])
def test_ok_and_error_responses_are_printable(tmp_path, ok):
    client = DriveStagingVerifyClient(
        "https://example.invalid/exec",
        opener=lambda request, timeout: FakeResponse(response_payload(ok=ok)),
    )
    result = client.verify_manifest(write_manifest(tmp_path))
    assert result.ok is ok
    assert result.cloud_visible is ok


def test_timeout_has_no_retry(tmp_path):
    calls = 0

    def opener(request, *, timeout):
        nonlocal calls
        calls += 1
        raise socket.timeout()

    client = DriveStagingVerifyClient("https://example.invalid/exec", opener=opener)
    with pytest.raises(DriveStagingVerifyError, match="timed out"):
        client.verify_manifest(write_manifest(tmp_path))
    assert calls == 1


def test_client_does_not_modify_sqlite(tmp_path):
    database = tmp_path / "state.db"
    database.write_bytes(b"synthetic-state")
    before = sha256(database.read_bytes()).hexdigest()
    client = DriveStagingVerifyClient(
        "https://example.invalid/exec",
        opener=lambda request, timeout: FakeResponse(response_payload()),
    )
    client.verify_manifest(write_manifest(tmp_path))
    assert sha256(database.read_bytes()).hexdigest() == before
