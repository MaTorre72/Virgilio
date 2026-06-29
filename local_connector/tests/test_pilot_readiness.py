import json
from pathlib import Path
import sys

from virgilio_connector.bucoliche import BucolicheConfig, CONFLICT_COLUMNS, EVENT_COLUMNS
from virgilio_connector.local_paths import LocalDataPaths
from virgilio_connector.multi_account import LocalImapAccount, LocalStorageConfig
from virgilio_connector.pilot_readiness import BucolicheDoctor, PilotCheck
from virgilio_connector.readonly_state import ReadonlyStateStore


class FakeReadClient:
    def __init__(self, sheets=None, fail=False):
        self.sheets, self.fail, self.calls = sheets or {}, fail, []
    def inspect_sheets(self):
        self.calls.append("inspect_sheets")
        if self.fail: raise RuntimeError("unreachable")
        return self.sheets
    def append_rows(self, *args):
        raise AssertionError("doctor must never append")


def sheets():
    return {"Bucoliche_Eventi": EVENT_COLUMNS,
            "Bucoliche_Conflitti": CONFLICT_COLUMNS,
            "Bucoliche_Stato": ()}


def doctor(environ, *, enabled=True, client=None, has_section=True):
    fake = client or FakeReadClient(sheets())
    result = BucolicheDoctor(BucolicheConfig(enabled=enabled),
        config_has_section=has_section, environ=environ,
        client_factory=lambda *_: fake).run()
    return result, fake


def test_doctor_ready_read_only():
    result, fake = doctor({"VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "sheet-test",
                           "VIRGILIO_GOOGLE_SERVICE_ACCOUNT_JSON": "{}"})
    assert result.status == "READY_WITH_WARNINGS"
    assert fake.calls == ["inspect_sheets"]
    assert "append capability not verified" in result.warnings[-1]


def test_doctor_disabled_is_warning():
    result, _ = doctor({"VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "sheet-test",
                        "VIRGILIO_GOOGLE_SERVICE_ACCOUNT_JSON": "{}"}, enabled=False)
    assert result.status == "READY_WITH_WARNINGS"


def test_doctor_missing_env_and_invalid_json_blocked():
    missing, _ = doctor({})
    invalid, _ = doctor({"VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "x",
                         "VIRGILIO_GOOGLE_SERVICE_ACCOUNT_JSON": "not-json"})
    assert missing.status == invalid.status == "BLOCKED"


def test_doctor_unreachable_and_missing_sheet_blocked():
    env = {"VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "x",
           "VIRGILIO_GOOGLE_SERVICE_ACCOUNT_JSON": "{}"}
    unreachable, _ = doctor(env, client=FakeReadClient(fail=True))
    absent, _ = doctor(env, client=FakeReadClient({"Bucoliche_Eventi": EVENT_COLUMNS}))
    assert unreachable.status == absent.status == "BLOCKED"


def test_doctor_output_has_no_secrets():
    result, _ = doctor({"VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "x",
                        "VIRGILIO_GOOGLE_SERVICE_ACCOUNT_JSON":
                        '{"private_key":"TOP_SECRET","token":"NOPE"}'})
    text = result.to_json()
    assert "TOP_SECRET" not in text and "NOPE" not in text and "private_key" not in text


def account(ack=False):
    return LocalImapAccount("test_box", "test@example.invalid", "generic",
        "imap.example.invalid", 993, "TEST_USER", "TEST_PASS", "INBOX", "done", "error",
        ack_enabled=ack, ack_strategy="add_done_label_only")


def pilot_fixture(tmp_path, *, ack=False, storage=True):
    root = tmp_path / ".local_data"; paths = LocalDataPaths(root)
    ReadonlyStateStore(paths.state_db).initialize()
    (root / "machine_id").write_text("machine-test\n", encoding="utf-8")
    staging = tmp_path / "staging"
    if storage: staging.mkdir()
    config = tmp_path / "accounts.yaml"
    config.write_text("rules:\n  default_action: include\n", encoding="utf-8")
    return PilotCheck((account(ack),), storage=LocalStorageConfig("local_filesystem", staging),
        bucoliche=BucolicheConfig(enabled=False), config_path=config, paths=paths,
        environ={"TEST_USER": "user", "TEST_PASS": "secret"})


def test_pilot_check_valid_and_no_operational_effect(tmp_path):
    result = pilot_fixture(tmp_path).run()
    assert result.status == "READY_WITH_WARNINGS"
    assert len(result.suggested_next_commands) == 6
    assert (tmp_path / ".local_data" / "machine_id").read_text() == "machine-test\n"


def test_pilot_check_storage_missing_blocked_and_ack_warns(tmp_path):
    blocked = pilot_fixture(tmp_path / "missing", storage=False).run()
    warned = pilot_fixture(tmp_path / "ack", ack=True).run()
    assert blocked.status == "BLOCKED"
    assert any("ack_enabled=true" in item for item in warned.warnings)


def test_cli_commands_exist_and_missing_config_blocked(tmp_path, monkeypatch, capsys):
    from virgilio_connector.__main__ import main
    for command in ("doctor-bucoliche", "pilot-check"):
        monkeypatch.setattr(sys, "argv", ["virgilio_connector", command,
                                          "--config", str(tmp_path / "missing.yaml")])
        assert main() == 2
        assert json.loads(capsys.readouterr().out)["status"] == "BLOCKED"
