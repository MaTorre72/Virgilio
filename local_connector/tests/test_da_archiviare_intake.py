import json
import sqlite3
import socket
import sys

import pytest

from virgilio_connector.da_archiviare_intake import (
    DA_ARCHIVIARE_INTAKE_ACTION,
    DA_ARCHIVIARE_STATUS_ACTION,
    DaArchiviareIntakeClientError,
    DaArchiviareIntakeError,
    DaArchiviareIntakeHttpClient,
    DaArchiviareIntakeResponse,
    DaArchiviareIntakeTokenNotConfigured,
    DaArchiviareIntakeUrlNotConfigured,
    DaArchiviareStatusHttpClient,
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
        "fingerprint": "f" * 64,
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


class FakeResponse:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self.body

    def close(self):
        pass


def response_payload(*, ok=True, inbox_id="inbox-fixed-1", created=True, updated=False,
                     idempotent=False, row=2, message="registrato",
                     form_url="https://example.invalid/exec?inbox_id=inbox-fixed-1",
                     notification_status="sent"):
    return {
        "ok": ok,
        "action": DA_ARCHIVIARE_INTAKE_ACTION,
        "inbox_id": inbox_id if ok else "",
        "created": created if ok else False,
        "updated": updated if ok else False,
        "idempotent": idempotent if ok else False,
        "row": row if ok else 0,
        "form_url": form_url if ok else "",
        "notification_status": notification_status if ok else "",
        "message": message if ok else "rifiutato",
        "errors": [] if ok else [{"code": "INVALID", "message": "rifiutato"}],
    }


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


def test_create_record_sends_metadata_only_envelope_with_token(tmp_path):
    captured = {}

    def opener(request, *, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(response_payload())

    result = DaArchiviareIntakeHttpClient(
        "https://example.invalid/exec",
        "token-123",
        timeout_seconds=11,
        opener=opener,
    ).create_record(
        write_manifest(tmp_path),
        drive_file_id="drive-123",
        manifest_file_id="manifest-123",
        form_url="https://example.invalid/form",
    )
    envelope = json.loads(captured["request"].data.decode("utf-8"))
    serialized = captured["request"].data.decode("utf-8")
    assert result.ok is True
    assert result.inbox_id == "inbox-fixed-1"
    assert captured["timeout"] == 11
    assert envelope["action"] == DA_ARCHIVIARE_INTAKE_ACTION
    assert envelope["token"] == "token-123"
    assert envelope["drive_file_id"] == "drive-123"
    assert envelope["manifest_file_id"] == "manifest-123"
    assert envelope["manifest"]["attachment_id"] == "att-123-42-1-aaaaaaaaaaaa"
    for forbidden in ("local_path", "file_path", "file_bytes", "base64", '"content"', '"raw"'):
        assert forbidden not in serialized


def test_status_client_reads_final_states_with_one_metadata_only_request():
    captured = {}

    def opener(request, *, timeout):
        captured["payload"] = json.loads(request.data)
        return FakeResponse({
            "ok": True,
            "action": DA_ARCHIVIARE_STATUS_ACTION,
            "records": [
                {"inbox_id": "inbox-1", "found": True, "status": "archiviato"},
                {"inbox_id": "inbox-2", "found": True, "status": "in_lavorazione"},
            ],
        })

    result = DaArchiviareStatusHttpClient(
        "https://example.invalid/exec", "token-123", opener=opener
    ).statuses(("inbox-1", "inbox-2"))

    assert result == {"inbox-1": "archiviato", "inbox-2": "in_lavorazione"}
    assert captured["payload"] == {
        "action": DA_ARCHIVIARE_STATUS_ACTION,
        "token": "token-123",
        "inbox_ids": ["inbox-1", "inbox-2"],
    }


def test_status_client_rejects_missing_or_duplicate_records():
    client = DaArchiviareStatusHttpClient(
        "https://example.invalid/exec", "token-123",
        opener=lambda request, timeout: FakeResponse({
            "ok": True,
            "action": DA_ARCHIVIARE_STATUS_ACTION,
            "records": [
                {"inbox_id": "inbox-1", "found": True, "status": "archiviato"},
                {"inbox_id": "inbox-1", "found": True, "status": "archiviato"},
            ],
        }),
    )

    with pytest.raises(DaArchiviareIntakeClientError, match="records"):
        client.statuses(("inbox-1", "inbox-2"))


def test_url_not_configured_never_attempts_network(tmp_path):
    calls = []
    client = DaArchiviareIntakeHttpClient(
        None,
        "token-123",
        opener=lambda *args, **kwargs: calls.append(args),
    )
    with pytest.raises(DaArchiviareIntakeUrlNotConfigured, match="not configured"):
        client.create_record(
            write_manifest(tmp_path),
            drive_file_id="drive-123",
            manifest_file_id="manifest-123",
        )
    assert calls == []


def test_token_not_configured_never_attempts_network(tmp_path):
    calls = []
    client = DaArchiviareIntakeHttpClient(
        "https://example.invalid/exec",
        None,
        opener=lambda *args, **kwargs: calls.append(args),
    )
    with pytest.raises(DaArchiviareIntakeTokenNotConfigured, match="not configured"):
        client.create_record(
            write_manifest(tmp_path),
            drive_file_id="drive-123",
            manifest_file_id="manifest-123",
        )
    assert calls == []


def test_response_parsing_accepts_idempotent_retry(tmp_path):
    client = DaArchiviareIntakeHttpClient(
        "https://example.invalid/exec",
        "token-123",
        opener=lambda request, timeout: FakeResponse(
            response_payload(created=False, updated=False, idempotent=True)
        ),
    )
    result = client.create_record(
        write_manifest(tmp_path),
        drive_file_id="drive-123",
        manifest_file_id="manifest-123",
    )
    assert isinstance(result, DaArchiviareIntakeResponse)
    assert result.idempotent is True
    assert result.created is False
    assert result.updated is False


def test_response_requires_reachable_form_url_and_observable_notification(tmp_path):
    client = DaArchiviareIntakeHttpClient(
        "https://example.invalid/exec",
        "token-123",
        opener=lambda request, timeout: FakeResponse(response_payload()),
    )

    result = client.create_record(
        write_manifest(tmp_path),
        drive_file_id="drive-123",
        manifest_file_id="manifest-123",
    )

    assert result.form_url == "https://example.invalid/exec?inbox_id=inbox-fixed-1"
    assert result.notification_status == "sent"


def test_response_accepts_url_encoded_inbox_id(tmp_path):
    inbox_id = "inbox fixed&1"
    client = DaArchiviareIntakeHttpClient(
        "https://example.invalid/exec",
        "token-123",
        opener=lambda request, timeout: FakeResponse(response_payload(
            inbox_id=inbox_id,
            form_url="https://example.invalid/exec?inbox_id=inbox%20fixed%261",
        )),
    )

    assert client.create_record(
        write_manifest(tmp_path),
        drive_file_id="drive-123",
        manifest_file_id="manifest-123",
    ).inbox_id == inbox_id


@pytest.mark.parametrize(
    "changes",
    [
        {"form_url": ""},
        {"form_url": "https://example.invalid/exec"},
        {"notification_status": ""},
    ],
)
def test_response_rejects_missing_operational_link_or_notification_state(tmp_path, changes):
    client = DaArchiviareIntakeHttpClient(
        "https://example.invalid/exec",
        "token-123",
        opener=lambda request, timeout: FakeResponse(response_payload(**changes)),
    )

    with pytest.raises(DaArchiviareIntakeClientError, match="operational"):
        client.create_record(
            write_manifest(tmp_path),
            drive_file_id="drive-123",
            manifest_file_id="manifest-123",
        )


def test_invalid_response_action_is_rejected(tmp_path):
    client = DaArchiviareIntakeHttpClient(
        "https://example.invalid/exec",
        "token-123",
        opener=lambda request, timeout: FakeResponse({**response_payload(), "action": "other"}),
    )
    with pytest.raises(DaArchiviareIntakeClientError, match="intake result"):
        client.create_record(
            write_manifest(tmp_path),
            drive_file_id="drive-123",
            manifest_file_id="manifest-123",
        )


def test_timeout_has_no_retry(tmp_path):
    calls = 0

    def opener(request, *, timeout):
        nonlocal calls
        calls += 1
        raise socket.timeout()

    client = DaArchiviareIntakeHttpClient("https://example.invalid/exec", "token-123", opener=opener)
    with pytest.raises(DaArchiviareIntakeClientError, match="timed out"):
        client.create_record(
            write_manifest(tmp_path),
            drive_file_id="drive-123",
            manifest_file_id="manifest-123",
        )
    assert calls == 1


def test_cli_intake_da_archiviare_uses_env_and_prints_json(tmp_path, monkeypatch, capsys):
    manifest_path = write_manifest(tmp_path)
    monkeypatch.setenv("VIRGILIO_LOCAL_DATA_DIR", str(tmp_path / "local-data"))
    monkeypatch.setenv("VIRGILIO_CARONTE_INTAKE_URL", "https://example.invalid/exec")
    monkeypatch.setenv("VIRGILIO_TOKEN", "token-123")
    captured = {}

    class FakeClient:
        def __init__(self, url, token, *, timeout_seconds=15.0, opener=None):
            captured["url"] = url
            captured["token"] = token
            captured["timeout"] = timeout_seconds

        def create_record(self, manifest_path, *, drive_file_id, manifest_file_id, form_url=""):
            captured["manifest_path"] = manifest_path
            captured["drive_file_id"] = drive_file_id
            captured["manifest_file_id"] = manifest_file_id
            captured["form_url"] = form_url
            return DaArchiviareIntakeResponse(
                ok=True,
                action=DA_ARCHIVIARE_INTAKE_ACTION,
                inbox_id="inbox-fixed-1",
                created=True,
                updated=False,
                idempotent=False,
                row=2,
                message="registrato",
                errors=(),
                form_url="https://example.invalid/exec?inbox_id=inbox-fixed-1",
                notification_status="sent",
            )

    monkeypatch.setattr(sys, "argv", [
        "virgilio",
        "intake-da-archiviare",
        "--manifest",
        str(manifest_path),
        "--drive-file-id",
        "drive-123",
        "--manifest-file-id",
        "manifest-123",
    ])
    import virgilio_connector.__main__ as cli

    monkeypatch.setattr(cli, "DaArchiviareIntakeHttpClient", FakeClient)

    assert cli.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["inbox_id"] == "inbox-fixed-1"
    assert captured["url"] == "https://example.invalid/exec"
    assert captured["token"] == "token-123"
    assert captured["manifest_path"] == manifest_path
    assert captured["drive_file_id"] == "drive-123"
    assert captured["manifest_file_id"] == "manifest-123"


def test_cli_intake_da_archiviare_writes_audit_event(tmp_path, monkeypatch, capsys):
    manifest_path = write_manifest(tmp_path)
    local_root = tmp_path / "local_data"
    monkeypatch.setenv("VIRGILIO_LOCAL_DATA_DIR", str(local_root))
    monkeypatch.setenv("VIRGILIO_CARONTE_INTAKE_URL", "https://example.invalid/exec")
    monkeypatch.setenv("VIRGILIO_TOKEN", "token-123")

    class FakeClient:
        def __init__(self, url, token, *, timeout_seconds=15.0, opener=None):
            pass

        def create_record(self, manifest_path, *, drive_file_id, manifest_file_id, form_url=""):
            return DaArchiviareIntakeResponse(
                ok=True,
                action=DA_ARCHIVIARE_INTAKE_ACTION,
                inbox_id="inbox-fixed-1",
                created=True,
                updated=False,
                idempotent=False,
                row=2,
                message="registrato",
                errors=(),
                form_url="https://example.invalid/exec?inbox_id=inbox-fixed-1",
                notification_status="sent",
            )

    monkeypatch.setattr(sys, "argv", [
        "virgilio",
        "intake-da-archiviare",
        "--manifest",
        str(manifest_path),
        "--drive-file-id",
        "drive-123",
        "--manifest-file-id",
        "manifest-123",
    ])
    import virgilio_connector.__main__ as cli

    monkeypatch.setattr(cli, "DaArchiviareIntakeHttpClient", FakeClient)

    assert cli.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True

    with sqlite3.connect(local_root / "state.db") as conn:
        row = conn.execute(
            """SELECT machine_id, account_alias, entity_type, entity_id, fingerprint,
                      action, status, details_json
                 FROM audit_events ORDER BY id DESC LIMIT 1"""
        ).fetchone()

    assert row[0].startswith("caronte-")
    assert row[1] == "test-account"
    assert row[2] == "attachment"
    assert row[3] == "att-123-42-1-aaaaaaaaaaaa"
    assert row[4] == "f" * 64
    assert row[5] == "da_archiviare_intake"
    assert row[6] == "created"
    details = json.loads(row[7])
    assert details["inbox_id"] == "inbox-fixed-1"
    assert details["drive_file_id"] == "drive-123"
    assert details["manifest_file_id"] == "manifest-123"
