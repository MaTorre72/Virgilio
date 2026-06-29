import json
from pathlib import Path
import sys
import pytest

from virgilio_connector.bucoliche import BucolicheConfig, CONFLICT_COLUMNS, EVENT_COLUMNS
from virgilio_connector.local_paths import LocalDataPaths
from virgilio_connector.multi_account import LocalImapAccount, LocalStorageConfig
from virgilio_connector.pilot_readiness import (BucolicheDoctor, BucolicheSheetSetup,
                                                PilotCheck, PilotPreview, PilotSafeRunner)
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
    def create_sheet(self, name): self.calls.append(("create_sheet", name))
    def write_header(self, name, columns): self.calls.append(("write_header", name, tuple(columns)))


class FakePipelineResult:
    def __init__(self, status="completed", errors=(), warnings=()):
        self.status = status
        self.errors = tuple(errors)
        self.warnings = tuple(warnings)


class FakePipelineRunner:
    def __init__(self, result, log):
        self.result = result
        self.log = log

    def run(self, *, dry_run):
        self.log.append(("pipeline", dry_run))
        return self.result


class FakeExportRunner:
    def __init__(self, log, status="dry_run", errors=()):
        self.log = log
        self.status = status
        self.errors = tuple(errors)

    def export(self, *, dry_run):
        self.log.append(("export", dry_run))
        return type("ExportResult", (), {
            "status": self.status,
            "errors": self.errors,
        })()


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
    assert unreachable.status == "BLOCKED"
    assert absent.status == "READY_WITH_WARNINGS"
    assert any("setup-bucoliche-test-sheet" in item for item in absent.warnings)


def test_doctor_output_has_no_secrets():
    result, _ = doctor({"VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "x",
                        "VIRGILIO_GOOGLE_SERVICE_ACCOUNT_JSON":
                        '{"private_key":"TOP_SECRET","token":"NOPE"}'})
    text = result.to_json()
    assert "TOP_SECRET" not in text and "NOPE" not in text and "private_key" not in text


def test_doctor_header_absent_warns_and_mismatch_blocks():
    env = setup_env()
    absent, _ = doctor(env, client=FakeReadClient({
        "Bucoliche_Eventi": (), "Bucoliche_Conflitti": CONFLICT_COLUMNS}))
    mismatch, _ = doctor(env, client=FakeReadClient({
        "Bucoliche_Eventi": ("wrong",), "Bucoliche_Conflitti": CONFLICT_COLUMNS}))
    assert absent.status == "READY_WITH_WARNINGS"
    assert mismatch.status == "BLOCKED"


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


def test_pilot_run_safe_stops_on_gate_without_pipeline_or_export(tmp_path):
    log = []
    runner = PilotSafeRunner(
        pilot_check_runner=pilot_fixture(tmp_path / "missing", storage=False),
        pipeline_factory=lambda: FakePipelineRunner(FakePipelineResult(), log),
        export_factory=lambda: FakeExportRunner(log),
    )
    result = runner.run()
    assert result.status == "BLOCKED"
    assert result.stopped_at == "pilot_check"
    assert log == []


def test_pilot_run_safe_runs_dry_sequence_until_export(tmp_path):
    log = []
    runner = PilotSafeRunner(
        pilot_check_runner=pilot_fixture(tmp_path),
        pipeline_factory=lambda: FakePipelineRunner(
            FakePipelineResult(status="completed_with_warnings",
                               warnings=("storage: skipped_no_ready_attachments",)),
            log,
        ),
        export_factory=lambda: FakeExportRunner(log),
    )
    result = runner.run()
    assert result.status == "READY_WITH_WARNINGS"
    assert result.pipeline_status == "completed_with_warnings"
    assert result.export_status == "dry_run"
    assert log == [("pipeline", True), ("export", True)]


def test_pilot_run_safe_stops_before_export_on_pipeline_error(tmp_path):
    log = []
    runner = PilotSafeRunner(
        pilot_check_runner=pilot_fixture(tmp_path),
        pipeline_factory=lambda: FakePipelineRunner(
            FakePipelineResult(status="completed_with_errors",
                               errors=("process: RuntimeError: boom",)),
            log,
        ),
        export_factory=lambda: FakeExportRunner(log),
    )
    result = runner.run()
    assert result.status == "BLOCKED"
    assert result.stopped_at == "pipeline"
    assert result.errors == ("process: RuntimeError: boom",)
    assert log == [("pipeline", True)]


def test_cli_commands_exist_and_missing_config_blocked(tmp_path, monkeypatch, capsys):
    from virgilio_connector.__main__ import main
    for command in ("doctor-bucoliche", "pilot-check", "pilot-run-safe"):
        monkeypatch.setattr(sys, "argv", ["virgilio_connector", command,
                                          "--config", str(tmp_path / "missing.yaml")])
        assert main() == 2
        assert json.loads(capsys.readouterr().out)["status"] == "BLOCKED"


def test_new_cli_commands_are_registered(tmp_path, monkeypatch):
    from virgilio_connector.__main__ import main
    for command in ("setup-bucoliche-test-sheet", "pilot-preview", "google-oauth-login"):
        monkeypatch.setattr(sys, "argv", ["virgilio_connector", command,
                                          "--config", str(tmp_path / "missing.yaml")])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 2


def setup(environ, fake, *, dry_run=False, enabled=True):
    return BucolicheSheetSetup(BucolicheConfig(enabled=enabled), environ=environ,
        client_factory=lambda *_: fake).run(dry_run=dry_run)


def setup_env():
    return {"VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "sheet-test",
            "VIRGILIO_GOOGLE_SERVICE_ACCOUNT_JSON": "{}"}


def test_sheet_setup_dry_run_never_calls_google():
    fake = FakeReadClient()
    result = setup(setup_env(), fake, dry_run=True)
    assert result.status == "DRY_RUN" and len(result.actions) == 3
    assert fake.calls == []


def test_sheet_setup_creates_missing_and_writes_only_headers():
    fake = FakeReadClient({})
    result = setup(setup_env(), fake)
    assert result.status == "READY"
    assert [call[0] for call in fake.calls[1:]] == [
        "create_sheet", "write_header", "create_sheet", "write_header",
        "create_sheet", "write_header"]


def test_sheet_setup_empty_header_only_and_coherent_unchanged():
    fake = FakeReadClient({"Bucoliche_Eventi": (),
        "Bucoliche_Conflitti": CONFLICT_COLUMNS, "Bucoliche_Stato": ()})
    result = setup(setup_env(), fake)
    assert result.status == "READY"
    assert ("write_header", "Bucoliche_Eventi", EVENT_COLUMNS) in fake.calls
    assert not any(call[:2] == ("write_header", "Bucoliche_Conflitti") for call in fake.calls)


def test_sheet_setup_mismatch_blocks_without_any_write():
    fake = FakeReadClient({"Bucoliche_Eventi": ("wrong",),
        "Bucoliche_Conflitti": CONFLICT_COLUMNS})
    result = setup(setup_env(), fake)
    assert result.status == "BLOCKED"
    assert fake.calls == ["inspect_sheets"]


def test_pilot_preview_is_local_masks_target_and_warns_ack(tmp_path):
    runner = pilot_fixture(tmp_path, ack=True)
    pilot = runner.run()
    preview = PilotPreview(runner.accounts, storage=runner.storage,
        bucoliche=BucolicheConfig(enabled=True), paths=runner.paths,
        pilot_status=pilot.status,
        environ={"VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "1234567890SECRET"}).run()
    text = json.dumps(preview)
    assert preview["sheet_target"] == "1234...CRET"
    assert len(preview["next_commands"]) == 5
    assert preview["warnings"] == ["test_box: ack_enabled=true"]
    assert "1234567890SECRET" not in text and "private_key" not in text


def test_oauth_doctor_missing_token_blocks_with_login_hint(tmp_path):
    secret = tmp_path / "client.json"; secret.write_text('{}', encoding="utf-8")
    config = BucolicheConfig(enabled=True, credentials_mode="user_oauth_local")
    result = BucolicheDoctor(config, config_has_section=True, environ={
        "VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "sheet-test",
        "VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH": str(secret),
        "VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH": str(tmp_path / "missing-token.json")}).run()
    assert result.status == "BLOCKED"
    assert any("google-oauth-login" in error for error in result.errors)


def test_oauth_doctor_with_token_uses_read_only_fake(tmp_path):
    secret = tmp_path / "client.json"; secret.write_text('{}', encoding="utf-8")
    token = tmp_path / "token.json"; token.write_text('{}', encoding="utf-8")
    fake = FakeReadClient(sheets())
    config = BucolicheConfig(enabled=True, credentials_mode="user_oauth_local")
    result = BucolicheDoctor(config, config_has_section=True, environ={
        "VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "sheet-test",
        "VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH": str(secret),
        "VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH": str(token)},
        client_factory=lambda *_: fake).run()
    assert result.status == "READY_WITH_WARNINGS"
    assert fake.calls == ["inspect_sheets"]


def test_oauth_sheet_setup_uses_existing_token_and_fake(tmp_path):
    secret = tmp_path / "client.json"; secret.write_text('{}', encoding="utf-8")
    token = tmp_path / "token.json"; token.write_text('{}', encoding="utf-8")
    fake = FakeReadClient(sheets())
    config = BucolicheConfig(enabled=True, credentials_mode="user_oauth_local")
    result = BucolicheSheetSetup(config, environ={
        "VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "sheet-test",
        "VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH": str(secret),
        "VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH": str(token)},
        client_factory=lambda *_: fake).run(dry_run=False)
    assert result.status == "READY"
    assert fake.calls[0] == "inspect_sheets"
    assert fake.calls[1][:2] == ("write_header", "Bucoliche_Stato")


def test_pilot_check_accepts_oauth_local_files(tmp_path):
    runner = pilot_fixture(tmp_path)
    secret = tmp_path / "client.json"; secret.write_text('{}', encoding="utf-8")
    token = tmp_path / "token.json"; token.write_text('{}', encoding="utf-8")
    runner = PilotCheck(runner.accounts, storage=runner.storage,
        bucoliche=BucolicheConfig(enabled=True, credentials_mode="user_oauth_local"),
        config_path=runner.config_path, paths=runner.paths, environ={
            "TEST_USER": "user", "TEST_PASS": "secret",
            "VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "sheet-test",
            "VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH": str(secret),
            "VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH": str(token)})
    assert runner.run().status == "READY_WITH_WARNINGS"
