import json
import socket

import pytest

from virgilio_connector.drive_staging_intake_test import (
    INTAKE_DRIVE_STAGING_TEST_ACTION,
    DriveStagingIntakeTestClient,
    DriveStagingIntakeTestError,
    DriveStagingIntakeTestUrlNotConfigured,
)


def manifest_payload():
    return {
        "connector_type": "local_imap", "account_alias": "test",
        "source_message_id": "<test@example.invalid>", "source_message_uid": "42",
        "attachment_id": "att-123-42-1-aaaaaaaaaaaa",
        "original_filename": "report.pdf",
        "staged_filename": "att-123-42-1-aaaaaaaaaaaa-report.pdf",
        "sha256": "a" * 64, "size_bytes": 4, "mime_type": "application/pdf",
        "scan_engine": "windows_defender", "scan_result": "clean",
        "quarantine_status": "ready_for_caronte", "note": "test staging",
    }


def response_payload(ok=True):
    manifest = manifest_payload()
    return {
        "ok": ok, "test_mode": True, "action": INTAKE_DRIVE_STAGING_TEST_ACTION,
        "attachment_id": manifest["attachment_id"],
        "staged_filename": manifest["staged_filename"],
        "drive_file_found": ok, "manifest_found": ok,
        "manifest_consistent": ok, "test_row_written": ok,
        "state": "presa_in_carico_test" if ok else "",
        "message": "written" if ok else "rejected",
        "errors": [] if ok else [{"code": "REJECTED", "message": "rejected"}],
    }


class FakeResponse:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode()
    def read(self):
        return self.body
    def close(self):
        pass


def write_manifest(tmp_path, payload=None):
    path = tmp_path / "file.pdf.manifest.json"
    path.write_text(json.dumps(payload or manifest_payload()), encoding="utf-8")
    return path


def test_valid_manifest_sends_test_metadata_only(tmp_path):
    captured = {}
    def opener(request, *, timeout):
        captured["body"] = request.data
        return FakeResponse(response_payload())
    result = DriveStagingIntakeTestClient(
        "https://example.invalid/exec", opener=opener
    ).intake_manifest(write_manifest(tmp_path))
    payload = json.loads(captured["body"])
    assert result.test_row_written is True
    assert payload["test_mode"] is True
    assert payload["action"] == INTAKE_DRIVE_STAGING_TEST_ACTION
    serialized = captured["body"].decode()
    for forbidden in ("local_path", "file_path", "file_bytes", "base64", '"content"', '"raw"'):
        assert forbidden not in serialized


def test_manifest_missing(tmp_path):
    with pytest.raises(DriveStagingIntakeTestError, match="not found"):
        DriveStagingIntakeTestClient("https://example.invalid/exec").intake_manifest(
            tmp_path / "missing.json"
        )


def test_url_not_configured_attempts_no_network(tmp_path):
    calls = []
    client = DriveStagingIntakeTestClient(None, opener=lambda *a, **k: calls.append(a))
    with pytest.raises(DriveStagingIntakeTestUrlNotConfigured, match="not configured"):
        client.intake_manifest(write_manifest(tmp_path))
    assert calls == []


@pytest.mark.parametrize("ok", [True, False])
def test_ok_and_error_responses(tmp_path, ok):
    result = DriveStagingIntakeTestClient(
        "https://example.invalid/exec",
        opener=lambda request, timeout: FakeResponse(response_payload(ok)),
    ).intake_manifest(write_manifest(tmp_path))
    assert result.ok is ok


def test_timeout_has_no_retry(tmp_path):
    calls = 0
    def opener(request, *, timeout):
        nonlocal calls
        calls += 1
        raise socket.timeout()
    with pytest.raises(DriveStagingIntakeTestError, match="timed out"):
        DriveStagingIntakeTestClient(
            "https://example.invalid/exec", opener=opener
        ).intake_manifest(write_manifest(tmp_path))
    assert calls == 1


def test_payload_has_no_gmail_or_drive_api_instructions(tmp_path):
    captured = {}
    def opener(request, *, timeout):
        captured["payload"] = json.loads(request.data)
        return FakeResponse(response_payload())
    DriveStagingIntakeTestClient(
        "https://example.invalid/exec", opener=opener
    ).intake_manifest(write_manifest(tmp_path))
    assert not ({"gmail", "drive_api", "ack", "move", "delete"} & set(captured["payload"]))
