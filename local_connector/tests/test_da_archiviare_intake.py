import json

import pytest

from virgilio_connector.da_archiviare_intake import (
    DA_ARCHIVIARE_INTAKE_ACTION,
    DaArchiviareIntakeError,
    build_da_archiviare_intake_payload,
)


def staged_manifest_payload():
    return {
        "schema_version": "1.0",
        "connector_type": "local_imap",
        "account_alias": "test-account",
        "source_message_id": "<test@example.invalid>",
        "source_message_uid": "42",
        "attachment_id": "att-123-42-1-aaaaaaaaaaaa",
        "original_filename": "report.pdf",
        "staged_filename": "att-123-42-1-aaaaaaaaaaaa-report.pdf",
        "sha256": "a" * 64,
        "size_bytes": 4,
        "mime_type": "application/pdf",
        "scan_engine": "windows_defender",
        "scan_result": "clean",
        "quarantine_status": "ready_for_caronte",
        "staged_at": "2026-07-03T10:00:00+00:00",
        "dry_run": False,
        "note": "sync cloud non verificata",
    }


def write_manifest(tmp_path, payload=None):
    path = tmp_path / "file.pdf.manifest.json"
    path.write_text(json.dumps(payload or staged_manifest_payload()), encoding="utf-8")
    return path


def test_builds_metadata_only_payload_without_test_mode(tmp_path):
    manifest_path = write_manifest(tmp_path)
    payload = build_da_archiviare_intake_payload(
        manifest_path,
        drive_file_id="drive-123",
        manifest_file_id="manifest-123",
    )

    assert payload["action"] == DA_ARCHIVIARE_INTAKE_ACTION
    assert payload["drive_file_id"] == "drive-123"
    assert payload["manifest_file_id"] == "manifest-123"
    assert payload["form_url"] == ""
    assert payload["manifest"]["attachment_id"] == "att-123-42-1-aaaaaaaaaaaa"
    assert payload["manifest"]["quarantine_status"] == "ready_for_caronte"
    assert payload["manifest"]["scan_result"] == "clean"
    serialized = json.dumps(payload, ensure_ascii=False)
    for forbidden in ("test_mode", "local_path", "file_path", "file_bytes", "base64", '"content"', '"raw"'):
        assert forbidden not in serialized


def test_build_is_stable_for_same_manifest(tmp_path):
    manifest_path = write_manifest(tmp_path)
    first = build_da_archiviare_intake_payload(
        manifest_path,
        drive_file_id="drive-123",
        manifest_file_id="manifest-123",
        form_url="https://example.invalid/form",
    )
    second = build_da_archiviare_intake_payload(
        manifest_path,
        drive_file_id="drive-123",
        manifest_file_id="manifest-123",
        form_url="https://example.invalid/form",
    )

    assert first == second
    assert first["manifest"]["staged_at"] == "2026-07-03T10:00:00+00:00"


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("manifest_path", "C:/tmp/file.pdf.manifest.json", "forbidden fields"),
        ("local_path", "C:/tmp/file.pdf", "forbidden fields"),
    ],
)
def test_rejects_forbidden_manifest_fields(tmp_path, field, value, message):
    manifest = staged_manifest_payload()
    manifest[field] = value
    with pytest.raises(DaArchiviareIntakeError, match=message):
        build_da_archiviare_intake_payload(
            write_manifest(tmp_path, manifest),
            drive_file_id="drive-123",
            manifest_file_id="manifest-123",
        )


@pytest.mark.parametrize("drive_file_id,manifest_file_id", [("", "manifest-123"), ("drive-123", "")])
def test_requires_drive_ids(tmp_path, drive_file_id, manifest_file_id):
    with pytest.raises(DaArchiviareIntakeError, match="required"):
        build_da_archiviare_intake_payload(
            write_manifest(tmp_path),
            drive_file_id=drive_file_id,
            manifest_file_id=manifest_file_id,
        )
