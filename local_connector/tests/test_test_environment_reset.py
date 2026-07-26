import json
from pathlib import Path
import sqlite3

import pytest

from virgilio_connector.application.maintenance import MaintenanceService
from virgilio_connector.test_environment_reset import (
    TEST_ENVIRONMENT_RESET_ACTION,
    TestEnvironmentResetError as ResetError,
    TestEnvironmentResetHttpClient as ResetHttpClient,
    TestEnvironmentResetResponse as ResetResponse,
    TestEnvironmentResetService as ResetService,
)


def response(reset_id, mode, *, phase=None, completed=None, targets=None):
    phase = phase or {"preview": "preview", "prepare": "prepared", "execute": "completed"}[mode]
    return {
        "ok": True, "test_mode": True, "action": TEST_ENVIRONMENT_RESET_ACTION,
        "mode": mode, "reset_id": reset_id, "phase": phase,
        "completed": completed if completed is not None else phase == "completed",
        "targets": targets or {
            "environment": "TEST",
            "registry": {"id": "registry-test", "name": "Registro TEST", "rows": [],
                         "schema": [{"sheet": "Eventi", "header": ["id"]}]},
            "inbox": {"id": "inbox-test", "name": "Da archiviare TEST", "rows": [],
                      "schema": [{"sheet": "Inbox TEST", "header": ["id"]}]},
            "limbo": {"id": "limbo-test", "name": "Limbo TEST", "files": []},
        },
        "backups": {"registry_file_id": "registry-backup", "limbo_folder_id": "limbo-backup"},
        "errors": [],
    }


class FakeHttpResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")
    def read(self):
        return self.payload
    def close(self):
        pass


class FakeRemote:
    def __init__(self):
        self.calls = []
    def request(self, reset_id, mode):
        self.calls.append(mode)
        raw = response(reset_id, mode)
        return ResetResponse.from_mapping(raw, mode=mode, reset_id=reset_id)


def seed_local(root):
    root.mkdir()
    (root / "machine_id").write_text("machine-test\n", encoding="utf-8")
    ready = root / "quarantine" / "ready"
    ready.mkdir(parents=True)
    (ready / "document.pdf").write_bytes(b"synthetic")
    connection = sqlite3.connect(root / "state.db")
    try:
        connection.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, state TEXT)")
        connection.execute("INSERT INTO events(state) VALUES ('test')")
        connection.commit()
    finally:
        connection.close()


def test_preview_lists_exact_local_rows_files_and_remote_targets(tmp_path):
    root = tmp_path / "data"
    seed_local(root)
    service = ResetService(MaintenanceService(root), FakeRemote())

    preview = service.preview("reset-test-12345678")

    assert preview.local_rows == {"events": 1}
    assert preview.local_files == (
        "machine_id", "quarantine/ready/document.pdf", "state.db",
    )
    assert preview.remote.targets["registry"]["name"] == "Registro TEST"


def test_coordinated_reset_orders_remote_backups_before_local_and_empties_local(tmp_path):
    root = tmp_path / "data"
    seed_local(root)
    remote = FakeRemote()
    result = ResetService(MaintenanceService(root), remote).reset(
        "reset-test-12345678", confirmed=True
    )

    assert remote.calls == ["preview", "prepare", "execute"]
    assert result.status == "completed" and result.remote.completed
    assert result.local.backup_path is not None
    assert not (root / "quarantine" / "ready" / "document.pdf").exists()
    with sqlite3.connect(root / "state.db") as connection:
        assert connection.execute("SELECT COUNT(*) FROM attachments").fetchone()[0] == 0


def test_same_reset_id_reuses_local_and_remote_backups_without_duplication(tmp_path):
    root = tmp_path / "data"
    seed_local(root)
    remote = FakeRemote()
    service = ResetService(MaintenanceService(root), remote)

    first = service.reset("reset-test-12345678", confirmed=True)
    second = service.reset("reset-test-12345678", confirmed=True)

    assert second.local.status == "idempotent"
    assert second.local.backup_path == first.local.backup_path
    assert len(tuple(tmp_path.glob("data.backup-*"))) == 1


def test_http_client_sends_metadata_only_and_rejects_path_in_response():
    captured = {}
    reset_id = "reset-test-12345678"
    def opener(request, *, timeout):
        captured["payload"] = json.loads(request.data)
        return FakeHttpResponse(response(reset_id, "preview"))

    result = ResetHttpClient(
        "https://example.invalid/exec", "synthetic-token", opener=opener
    ).request(reset_id, "preview")

    assert result.ok
    assert set(captured["payload"]) == {"action", "test_mode", "reset_id", "mode", "token"}
    unsafe = response(reset_id, "preview")
    unsafe["targets"]["limbo"]["path"] = "C:/local"
    with pytest.raises(ResetError, match="forbidden"):
        ResetHttpClient(
            "https://example.invalid/exec", "synthetic-token",
            opener=lambda request, timeout: FakeHttpResponse(unsafe),
        ).request(reset_id, "preview")


def test_reset_requires_confirmation_and_remote_prepare_success(tmp_path):
    root = tmp_path / "data"
    seed_local(root)
    service = ResetService(MaintenanceService(root), FakeRemote())
    with pytest.raises(ResetError, match="confirmation"):
        service.reset("reset-test-12345678", confirmed=False)
    assert (root / "quarantine" / "ready" / "document.pdf").is_file()


def test_gas_reset_is_authenticated_but_not_blocked_by_form_rate_limit():
    source = (Path(__file__).parents[2] / "apps_script" / "src" / "caronte.gs").read_text(
        encoding="utf-8"
    )
    token_gate = source.index("dati.token !== CONFIG.VIRGILIO_TOKEN")
    reset_route = source.index("dati.action === TEST_ENVIRONMENT_RESET_ACTION")
    form_rate_limit = source.index("_verificaRateLimit()")
    assert token_gate < reset_route < form_rate_limit


def test_gas_reset_targets_operational_assets_and_one_shared_register_tab():
    root = Path(__file__).parents[2] / "apps_script" / "src"
    reset_source = (root / "test_environment_reset.gs").read_text(encoding="utf-8")
    caronte_source = (root / "caronte.gs").read_text(encoding="utf-8")
    bucoliche_source = (root / "bucoliche.gs").read_text(encoding="utf-8")
    verify_source = (root / "drive_staging_verify.gs").read_text(encoding="utf-8")
    local_source = (Path(__file__).parents[1] / "src" / "virgilio_connector" /
                    "bucoliche.py").read_text(encoding="utf-8")

    inspect = reset_source[reset_source.index("function _testResetInspectGas_"):]
    assert "VIRGILIO_INBOX_SPREADSHEET_PROPERTY" in inspect
    assert "VIRGILIO_INBOX_SHEET_PROPERTY" in inspect
    assert "props.getProperty('VIRGILIO_LIMBO_ID')" in inspect
    assert "INTAKE_TEST_SPREADSHEET_PROPERTY" not in inspect
    assert "INTAKE_TEST_SHEET_PROPERTY" not in inspect
    assert "BUCOLICHE_TAB" in caronte_source
    assert "BUCOLICHE_EVENTS_SHEET" not in caronte_source
    assert "BUCOLICHE_STATE_SHEET" not in caronte_source
    assert "BUCOLICHE_CONFLICTS_SHEET" not in caronte_source
    assert "getSheetByName(CONFIG.BUCOLICHE_TAB)" in bucoliche_source
    update_body = bucoliche_source[
        bucoliche_source.index("function aggiornaRigheAllegati"):
        bucoliche_source.index("function registraErrore")
    ]
    assert "range.setValues" not in update_body
    assert "registraSuBucoliche" in update_body
    assert 'events_sheet: str = "bucoliche"' in local_source
    assert "client.append_rows(self.config.conflicts_sheet" not in local_source
    assert "active_client.replace_rows" not in local_source
    assert "const DRIVE_STAGING_FOLDER_PROPERTY = 'VIRGILIO_LIMBO_ID'" in verify_source
    assert "VIRGILIO_DRIVE_STAGING_FOLDER_ID" not in verify_source


def test_gas_reset_backs_up_and_removes_legacy_limbo_subfolders():
    source = (Path(__file__).parents[2] / "apps_script" / "src" /
              "test_environment_reset.gs").read_text(encoding="utf-8")

    assert "deve contenere soltanto file" not in source
    assert "_testResetCollectFiles_(child, childPrefix, values)" in source
    assert "_testResetCopyFolderContents_(sourceChild, targetChild)" in source
    assert "_testResetClearFolderContents_(child)" in source
    assert "child.setTrashed(true)" in source


def test_completed_remote_reset_must_be_empty_and_preserve_schema(tmp_path):
    class InconsistentRemote(FakeRemote):
        def request(self, reset_id, mode):
            raw = response(reset_id, mode)
            if mode == "execute":
                raw["targets"]["inbox"]["rows"] = [{"sheet": "Inbox TEST", "row": 2}]
            return ResetResponse.from_mapping(raw, mode=mode, reset_id=reset_id)

    root = tmp_path / "data"
    seed_local(root)
    with pytest.raises(ResetError, match="left data"):
        ResetService(MaintenanceService(root), InconsistentRemote()).reset(
            "reset-test-12345678", confirmed=True
        )
