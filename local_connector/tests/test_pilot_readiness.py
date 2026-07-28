from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
import tomllib
import pytest
from types import SimpleNamespace

from virgilio_connector.__main__ import _poll_pending_completion
from virgilio_connector.bucoliche import BucolicheConfig, CONFLICT_COLUMNS, EVENT_COLUMNS
from virgilio_connector.completion import AckCompletedMessagesResult, CompletionResult
from virgilio_connector.doctor import DoctorResult
from virgilio_connector.local_paths import LocalDataPaths
from virgilio_connector.multi_account import (
    LocalImapAccount,
    LocalStorageConfig,
    load_storage_config,
    load_multi_account_config,
)
from virgilio_connector.pilot_readiness import (BucolicheDoctor, BucolicheSheetSetup,
                                                PilotCheck, PilotPreview, PilotRunV11Runner,
                                                PilotSafeRunner)
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
    def __init__(self, status="completed", errors=(), warnings=(), human_summary=()):
        self.status = status
        self.errors = tuple(errors)
        self.warnings = tuple(warnings)
        self.human_summary = tuple(human_summary)


class FakePipelineRunner:
    def __init__(self, result, log):
        self.result = result
        self.log = log

    def run(self, *, dry_run):
        self.log.append(("pipeline", dry_run))
        return self.result


def test_completion_followup_polls_human_state_without_rerunning_acquisition():
    class CompletionOnlyRunner:
        def __init__(self):
            self.calls = 0

        def resume_pending(self, *, dry_run):
            self.calls += 1
            if self.calls == 1:
                return (SimpleNamespace(
                    status="completion_skipped",
                    reason="in attesa dell'archiviazione finale in Da archiviare",
                ),)
            return (SimpleNamespace(status="completed", reason="completed"),)

    class Clock:
        now = 0.0
        sleeps = []

        def __call__(self):
            return self.now

        def sleep(self, seconds):
            self.sleeps.append(seconds)
            self.now += seconds

    runner = CompletionOnlyRunner()
    clock = Clock()

    results = _poll_pending_completion(
        runner,
        followup_seconds=120,
        poll_seconds=30,
        clock=clock,
        sleeper=clock.sleep,
    )

    assert runner.calls == 2
    assert clock.sleeps == [30.0]
    assert results[0].status == "completed"


def test_completion_followup_zero_timeout_waits_until_pending_handoff_recovers():
    class PendingRunner:
        def __init__(self):
            self.calls = 0

        def resume_pending(self, *, dry_run):
            self.calls += 1
            if self.calls == 1:
                return (SimpleNamespace(
                    status="completion_skipped",
                    reason="message has attachments not delivered to Da archiviare",
                ),)
            return (SimpleNamespace(status="completed", reason="completed"),)

    class Clock:
        now = 0.0
        sleeps = []

        def __call__(self):
            return self.now

        def sleep(self, seconds):
            self.sleeps.append(seconds)
            self.now += seconds

    runner = PendingRunner()
    clock = Clock()

    results = _poll_pending_completion(
        runner,
        followup_seconds=0,
        poll_seconds=30,
        clock=clock,
        sleeper=clock.sleep,
    )

    assert runner.calls == 2
    assert clock.sleeps == [30.0]
    assert results[0].status == "completed"


class FakeExportRunner:
    def __init__(self, log, status="dry_run", errors=(), events_exported=3, already_exported=1):
        self.log = log
        self.status = status
        self.errors = tuple(errors)
        self.events_exported = events_exported
        self.already_exported = already_exported

    def export(self, *, dry_run):
        self.log.append(("export", dry_run))
        return type("ExportResult", (), {
            "status": self.status,
            "events_total": self.events_exported + self.already_exported,
            "events_pending": self.events_exported,
            "events_exported": 0 if dry_run else self.events_exported,
            "already_exported": self.already_exported,
            "conflicts_pending": 0,
            "preview": (),
            "errors": self.errors,
        })()

    def refresh_state(self, *, dry_run):
        self.log.append(("refresh_state", dry_run))
        return type("RefreshResult", (), {
            "status": "dry_run" if dry_run else "completed",
            "state_rows_total": 4,
            "errors": (),
        })()


class FakeDoctorRunner:
    def __init__(self, status="READY", errors=(), warnings=()):
        self.result = DoctorResult(status, tuple(errors), tuple(warnings), ())

    def run(self):
        return self.result


class FakeConflictChecker:
    def __init__(self, log, conflicts=()):
        self.log = log
        self.conflicts = tuple(conflicts)

    def check(self):
        self.log.append("conflicts")
        return {
            "status": "CONFLICTS" if self.conflicts else "OK",
            "conflicts": list(self.conflicts),
        }


class FakeAckRunner:
    def __init__(self, log, preview=None, real=None):
        self.log = log
        self.preview = preview or AckCompletedMessagesResult(
            status="dry_run",
            dry_run=True,
            gate_status="READY",
            messages_planned=1,
            pending_export_events=0,
            local_conflicts=0,
            errors=(),
            warnings=(),
            results=(CompletionResult(
                account_alias="test_box",
                message_row_id=1,
                message_uid="1",
                message_id="<1@example.invalid>",
                subject="msg",
                staged_attachments=("att-1",),
                status="planned",
                dry_run=True,
                ack_strategy="add_done_label_only",
                reason="would mark as traghettata; input message not removed",
            ),),
        )
        self.real = real or AckCompletedMessagesResult(
            status="completed",
            dry_run=False,
            gate_status="READY",
            messages_planned=1,
            pending_export_events=0,
            local_conflicts=0,
            errors=(),
            warnings=(),
            results=(CompletionResult(
                account_alias="test_box",
                message_row_id=1,
                message_uid="1",
                message_id="<1@example.invalid>",
                subject="msg",
                staged_attachments=("att-1",),
                status="completed",
                dry_run=False,
                ack_strategy="add_done_label_only",
                reason="marcata come traghettata; messaggio non rimosso dalla cartella input",
            ),),
        )

    def run(self, *, dry_run):
        self.log.append(("ack", dry_run))
        return self.preview if dry_run else self.real


def sheets():
    return {"bucoliche": EVENT_COLUMNS}


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
    absent, _ = doctor(env, client=FakeReadClient({"altro": EVENT_COLUMNS}))
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
    absent, _ = doctor(env, client=FakeReadClient({"bucoliche": ()}))
    mismatch, _ = doctor(env, client=FakeReadClient({"bucoliche": ("wrong",)}))
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


def pilot_run_runner(tmp_path, *, ack=False, doctor_status="READY", pipeline=None,
                     conflicts=(), export_status="completed", export_errors=(),
                     export_events=3, export_already=1,
                     ack_preview=None, ack_real=None):
    root = tmp_path / ".local_data"
    paths = LocalDataPaths(root)
    log: list[object] = []
    return PilotRunV11Runner(
        accounts=(account(ack),),
        paths=paths,
        doctor_runner=FakeDoctorRunner(status=doctor_status),
        pipeline_factory=lambda: FakePipelineRunner(
            pipeline or FakePipelineResult(status="completed_with_warnings",
                                           warnings=("storage: skipped_no_ready_attachments",)),
            log,
        ),
        conflict_checker_factory=lambda: FakeConflictChecker(log, conflicts=conflicts),
        export_factory=lambda: FakeExportRunner(
            log, status=export_status, errors=export_errors,
            events_exported=export_events, already_exported=export_already,
        ),
        ack_factory=lambda: FakeAckRunner(log, preview=ack_preview, real=ack_real),
    ), log


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


def test_pilot_run_v11_real_success_writes_report_and_acks(tmp_path):
    runner, log = pilot_run_runner(tmp_path, ack=True)
    result = runner.run(dry_run=False)
    assert result.final_status == "OK"
    assert result.doctor_status == "READY"
    assert result.pipeline_status == "completed_with_warnings"
    assert result.conflicts_count == 0
    assert result.bucoliche_events_exported == 3
    assert result.ack_gate_status == "READY"
    assert result.ack_messages_planned == 1
    assert result.ack_completed == 1
    assert result.ack_failed == 0
    assert result.report_path
    assert log == [("pipeline", False), "conflicts", ("export", False), ("refresh_state", True),
                   ("ack", True), ("ack", False)]
    report = json.loads((tmp_path / ".local_data" / result.report_path).read_text(encoding="utf-8"))
    assert report["final_status"] == "OK"
    assert report["ack_completed"] == 1


def test_pilot_run_v11_second_run_reports_ok_no_new_work(tmp_path):
    preview = AckCompletedMessagesResult(
        status="dry_run",
        dry_run=True,
        gate_status="READY",
        messages_planned=0,
        pending_export_events=0,
        local_conflicts=0,
        errors=(),
        warnings=(),
        results=(CompletionResult(
            account_alias="test_box",
            message_row_id=1,
            message_uid="1",
            message_id="<1@example.invalid>",
            subject="msg",
            staged_attachments=("att-1",),
            status="already_completed",
            dry_run=True,
            ack_strategy="add_done_label_only",
            reason="message already completed",
        ),),
    )
    runner, log = pilot_run_runner(
        tmp_path,
        ack=True,
        export_status="completed",
        export_events=0,
        export_already=4,
        ack_preview=preview,
    )
    result = runner.run(dry_run=False)
    assert result.final_status == "OK_NO_NEW_WORK"
    assert result.bucoliche_events_exported == 0
    assert result.ack_skip_reason == "no_ackable_messages"
    assert result.ack_completed == 1
    assert log == [("pipeline", False), "conflicts", ("export", False), ("refresh_state", True),
                   ("ack", True)]


def test_pilot_run_v11_conflicts_block_export_and_ack(tmp_path):
    runner, log = pilot_run_runner(
        tmp_path,
        ack=True,
        conflicts=({"attachment_id": "att-1", "fingerprint": "fp-1"},),
    )
    result = runner.run(dry_run=False)
    assert result.final_status == "BLOCKED"
    assert result.conflicts_count == 1
    assert result.ack_skip_reason == "conflicts_detected"
    assert log == [("pipeline", False), "conflicts"]


def test_pilot_run_v11_export_failure_blocks_ack(tmp_path):
    runner, log = pilot_run_runner(
        tmp_path,
        ack=True,
        export_status="completed_with_errors",
        export_errors=("evt-1: RuntimeError",),
    )
    result = runner.run(dry_run=False)
    assert result.final_status == "BLOCKED"
    assert result.errors == ("evt-1: RuntimeError",)
    assert result.ack_skip_reason == "export_failed"
    assert log == [("pipeline", False), "conflicts", ("export", False), ("refresh_state", True)]


def test_pilot_run_v11_ack_disabled_is_skipped_without_error(tmp_path):
    runner, log = pilot_run_runner(tmp_path, ack=False)
    result = runner.run(dry_run=False)
    assert result.final_status == "OK"
    assert result.ack_gate_status == "SKIPPED"
    assert result.ack_skip_reason == "ack_enabled_false"
    assert "ack skipped: ack_enabled_false" in result.warnings
    assert log == [("pipeline", False), "conflicts", ("export", False), ("refresh_state", True)]


def test_pilot_run_v11_dry_run_keeps_ack_in_preview_only(tmp_path):
    runner, log = pilot_run_runner(tmp_path, ack=True)
    result = runner.run(dry_run=True)
    assert result.final_status == "READY_DRY_RUN"
    assert result.dry_run is True
    assert result.ack_completed == 0
    assert log == [("pipeline", True), "conflicts", ("export", True), ("refresh_state", True),
                   ("ack", True)]


def test_cli_commands_exist_and_missing_config_blocked(tmp_path, monkeypatch, capsys):
    from virgilio_connector.__main__ import main
    for command in ("doctor-bucoliche", "pilot-check", "pilot-run-safe", "pilot", "pilot-run"):
        monkeypatch.setattr(sys, "argv", ["virgilio_connector", command,
                                          "--config", str(tmp_path / "missing.yaml")])
        assert main() == 2
        assert json.loads(capsys.readouterr().out)["status"] == "BLOCKED"


def test_new_cli_commands_are_registered(tmp_path, monkeypatch):
    from virgilio_connector.__main__ import main
    for command in ("setup-bucoliche-test-sheet", "pilot-preview", "google-oauth-login",
                    "watch", "local-watch"):
        monkeypatch.setattr(sys, "argv", ["virgilio_connector", command,
                                          "--config", str(tmp_path / "missing.yaml")])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 2

    monkeypatch.setattr(sys, "argv", ["virgilio_connector", "init-config"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_doctor_bucoliche_cli_runs_without_human_flag(tmp_path, monkeypatch, capsys):
    import virgilio_connector.__main__ as cli

    class FakeResult:
        status = "READY"

        def to_json(self):
            return '{"status":"READY"}'

    class FakeDoctor:
        def __init__(self, *args, **kwargs):
            pass

        def run(self):
            return FakeResult()

    config = tmp_path / "bucoliche.yaml"
    config.write_text("bucoliche:\n  enabled: true\n", encoding="utf-8")
    monkeypatch.setattr(cli, "load_bucoliche_config", lambda _path: object())
    monkeypatch.setattr(cli, "has_bucoliche_section", lambda _path: True)
    monkeypatch.setattr(cli, "BucolicheDoctor", FakeDoctor)
    monkeypatch.setattr(sys, "argv", ["virgilio_connector", "doctor-bucoliche",
                                      "--config", str(config)])

    assert cli.main() == 0
    assert json.loads(capsys.readouterr().out)["status"] == "READY"


def test_doctor_bucoliche_cli_human_uses_doctor_summary(tmp_path, monkeypatch, capsys):
    import virgilio_connector.__main__ as cli

    class FakeResult:
        status = "READY"
        checks = ({"name": "config_section", "status": "OK"},)
        errors = ()
        warnings = ()
        suggested_next_commands = ()

        def to_json(self):
            return '{"status":"READY"}'

    class FakeDoctor:
        def __init__(self, *args, **kwargs):
            pass

        def run(self):
            return FakeResult()

    config = tmp_path / "bucoliche.yaml"
    config.write_text("bucoliche:\n  enabled: true\n", encoding="utf-8")
    monkeypatch.setattr(cli, "load_bucoliche_config", lambda _path: object())
    monkeypatch.setattr(cli, "has_bucoliche_section", lambda _path: True)
    monkeypatch.setattr(cli, "BucolicheDoctor", FakeDoctor)
    monkeypatch.setattr(sys, "argv", ["virgilio_connector", "doctor-bucoliche",
                                      "--config", str(config), "--human"])

    assert cli.main() == 0
    output = capsys.readouterr().out
    assert "Esito doctor Bucoliche: READY" in output
    assert "Check config_section: OK" in output


def test_maintenance_gui_command_calls_launcher(tmp_path, monkeypatch):
    import virgilio_connector.__main__ as cli

    seen = {}

    def fake_launch_gui(*, config_path=None):
        seen["config_path"] = config_path
        return 0

    monkeypatch.setattr(sys, "argv", ["virgilio", "maintenance-gui", "--config", str(tmp_path / "accounts.yaml")])
    monkeypatch.setattr("virgilio_connector.maintenance_gui.launch_gui", fake_launch_gui)

    assert cli.main() == 0
    assert seen["config_path"] == tmp_path / "accounts.yaml"


def test_pilot_cli_returns_preview_and_safe_result(tmp_path, monkeypatch, capsys):
    import virgilio_connector.__main__ as cli

    @dataclass
    class FakePilotResult:
        status: str
        dry_run: bool = True
        stopped_at: str | None = None
        pilot_check: str = "READY_WITH_WARNINGS"
        pipeline_status: str | None = "completed_with_warnings"
        export_status: str | None = "dry_run"
        errors: tuple[str, ...] = ()
        warnings: tuple[str, ...] = ("warn",)
        suggested_next_commands: tuple[str, ...] = ("run-real",)

    class FakePilotCheck:
        def __init__(self, *args, **kwargs):
            pass

        def run(self):
            return type("PilotCheckResult", (), {"status": "READY_WITH_WARNINGS"})()

    class FakePilotPreview:
        def __init__(self, *args, **kwargs):
            pass

        def run(self):
            return {"pilot_check": "READY_WITH_WARNINGS", "next_commands": ["preview-step"]}

    class FakePilotSafeRunner:
        def __init__(self, **kwargs):
            pass

        def run(self):
            return FakePilotResult("READY_WITH_WARNINGS")

    monkeypatch.setattr(cli, "_load_pilot_components",
                        lambda config: (("account",), "storage", "bucoliche", "paths"))
    monkeypatch.setattr(cli, "PilotCheck", FakePilotCheck)
    monkeypatch.setattr(cli, "PilotPreview", FakePilotPreview)
    monkeypatch.setattr(cli, "PilotSafeRunner", FakePilotSafeRunner)
    monkeypatch.setattr(sys, "argv", ["virgilio", "pilot", "--config", str(tmp_path / "accounts.yaml")])

    assert cli.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "READY_WITH_WARNINGS"
    assert payload["dry_run"] is True
    assert payload["preview"]["next_commands"] == ["preview-step"]
    assert payload["pilot_run_safe"]["export_status"] == "dry_run"


def test_pilot_cli_human_output_includes_snapshot(tmp_path, monkeypatch, capsys):
    import virgilio_connector.__main__ as cli

    @dataclass
    class FakePilotResult:
        status: str
        dry_run: bool = True
        stopped_at: str | None = None
        pilot_check: str = "READY_WITH_WARNINGS"
        pipeline_status: str | None = "completed_with_warnings"
        export_status: str | None = "dry_run"
        errors: tuple[str, ...] = ()
        warnings: tuple[str, ...] = ("warn",)
        suggested_next_commands: tuple[str, ...] = ("run-real",)

    class FakePilotCheck:
        def __init__(self, *args, **kwargs):
            pass

        def run(self):
            return type("PilotCheckResult", (), {"status": "READY_WITH_WARNINGS"})()

    class FakePilotPreview:
        def __init__(self, *args, **kwargs):
            pass

        def run(self):
            return {
                "pilot_check": "READY_WITH_WARNINGS",
                "accounts": [{"account_alias": "demo_box", "ack_enabled": False}],
                "events_exportable": 3,
                "local_conflicts": 0,
                "sheet_target": "1234...5678",
                "warnings": [],
                "next_commands": ["preview-step"],
            }

    class FakePilotSafeRunner:
        def __init__(self, **kwargs):
            pass

        def run(self):
            return FakePilotResult("READY_WITH_WARNINGS")

    monkeypatch.setattr(cli, "_load_pilot_components",
                        lambda config: (("account",), "storage", "bucoliche", "paths"))
    monkeypatch.setattr(cli, "PilotCheck", FakePilotCheck)
    monkeypatch.setattr(cli, "PilotPreview", FakePilotPreview)
    monkeypatch.setattr(cli, "PilotSafeRunner", FakePilotSafeRunner)
    monkeypatch.setattr(sys, "argv", ["virgilio", "pilot", "--config",
                                      str(tmp_path / "accounts.yaml"), "--human"])

    assert cli.main() == 0
    text = capsys.readouterr().out
    assert "Stato preview pilota: READY_WITH_WARNINGS" in text
    assert "Esito pilot-run-safe: READY_WITH_WARNINGS (dry-run)" in text
    assert "Prossimo comando: preview-step" in text
    assert '"status"' not in text


def test_pilot_run_cli_human_output_is_essential(tmp_path, monkeypatch, capsys):
    import virgilio_connector.__main__ as cli

    @dataclass
    class FakePilotRunResult:
        timestamp: str = "2026-07-01T12:00:00+00:00"
        dry_run: bool = True
        doctor_status: str = "READY_WITH_WARNINGS"
        pipeline_status: str = "completed_with_warnings"
        conflicts_count: int = 0
        bucoliche_events_exported: int = 2
        bucoliche_already_exported: int = 5
        bucoliche_state_rows: int = 7
        ack_gate_status: str = "READY"
        ack_messages_planned: int = 1
        ack_completed: int = 0
        ack_failed: int = 0
        ack_skip_reason: str | None = None
        errors: tuple[str, ...] = ()
        warnings: tuple[str, ...] = ("ack skipped: no_ackable_messages",)
        final_status: str = "READY_DRY_RUN"
        next_action: str = "Esegui il run reale quando il dry-run e' pulito."
        report_path: str | None = "reports/pilot_run_v11_20260701_120000.json"

    class FakePilotRunRunner:
        def __init__(self, **kwargs):
            pass

        def run(self, *, dry_run):
            assert dry_run is True
            return FakePilotRunResult()

    monkeypatch.setattr(cli, "_load_pilot_components",
                        lambda config: ((account(True),), "storage", "bucoliche", "paths"))
    monkeypatch.setattr(cli, "PilotRunV11Runner", FakePilotRunRunner)
    monkeypatch.setattr(sys, "argv", ["virgilio", "pilot-run", "--config",
                                      str(tmp_path / "accounts.yaml"), "--dry-run", "--human"])

    assert cli.main() == 0
    text = capsys.readouterr().out
    assert "Configurazione: OK (READY_WITH_WARNINGS)" in text
    assert "Pipeline: OK (completed_with_warnings)" in text
    assert "Bucoliche: eventi nuovi 2 / gia esportati 5" in text
    assert "Esito finale: READY_DRY_RUN" in text


def test_watch_cli_runs_controlled_cycles(tmp_path, monkeypatch, capsys):
    import virgilio_connector.__main__ as cli

    @dataclass
    class FakePipelineResult:
        report_path: str | None = None
        dry_run: bool = False
        status: str = "completed"
        errors: tuple[str, ...] = ()
        warnings: tuple[str, ...] = ()
        human_summary: tuple[str, ...] = ("Pipeline locale pronta.",)

    class FakeRunner:
        def __init__(self):
            self.cycles = 0

        def run(self, *, dry_run):
            self.cycles += 1
            return FakePipelineResult(
                dry_run=dry_run,
                human_summary=(f"Simulazione ciclo {self.cycles}",),
            )

    runner = FakeRunner()
    sleep_calls = []
    monkeypatch.setattr(cli, "_build_local_pipeline_runner_from_config", lambda config: runner)
    monkeypatch.setattr(cli, "sleep", lambda seconds: sleep_calls.append(seconds))
    monkeypatch.setattr(sys, "argv", ["virgilio", "watch", "--config",
                                      str(tmp_path / "accounts.yaml"), "--dry-run",
                                      "--human", "--interval-seconds", "7",
                                      "--max-cycles", "2"])

    assert cli.main() == 0
    text = capsys.readouterr().out
    assert "Ciclo watch #1" in text
    assert "Ciclo watch #2" in text
    assert "Simulazione ciclo 1" in text
    assert "Simulazione ciclo 2" in text
    assert runner.cycles == 2
    assert sleep_calls == [7]


def test_watch_single_cycle_returns_failure_when_pipeline_has_errors(
    tmp_path, monkeypatch, capsys
):
    import virgilio_connector.__main__ as cli

    @dataclass
    class FailedPipelineResult:
        report_path: str | None = None
        dry_run: bool = False
        status: str = "completed_with_errors"
        errors: tuple[str, ...] = ("handoff failed",)
        warnings: tuple[str, ...] = ()
        human_summary: tuple[str, ...] = ("Invio non completato.",)

    class FailedRunner:
        def run(self, *, dry_run):
            return FailedPipelineResult(dry_run=dry_run)

    monkeypatch.setattr(
        cli, "_build_local_pipeline_runner_from_config", lambda config: FailedRunner()
    )
    monkeypatch.setattr(sys, "argv", [
        "virgilio", "watch", "--config", str(tmp_path / "accounts.yaml"),
        "--human", "--interval-seconds", "7", "--max-cycles", "1",
    ])

    assert cli.main() == 1
    assert "Invio non completato." in capsys.readouterr().out


def test_init_config_cli_writes_valid_template(tmp_path, monkeypatch, capsys):
    from virgilio_connector.__main__ import main
    output = tmp_path / "accounts.local.yaml"
    monkeypatch.setattr(sys, "argv", [
        "virgilio", "init-config",
        "--output", str(output),
        "--email", "account.1@example.com",
        "--staging-dir", str(tmp_path / "staging"),
    ])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "written"
    assert output.is_file()
    assert load_storage_config(output).staging_dir == tmp_path / "staging"
    assert load_multi_account_config(output)[0].account_alias == "account_1"


def test_init_config_cli_dry_run_does_not_write(tmp_path, monkeypatch, capsys):
    from virgilio_connector.__main__ import main
    output = tmp_path / "accounts.local.yaml"
    monkeypatch.setattr(sys, "argv", [
        "virgilio", "init-config",
        "--output", str(output),
        "--email", "box@example.com",
        "--staging-dir", str(tmp_path / "staging"),
        "--dry-run",
    ])
    assert main() == 0
    text = capsys.readouterr().out
    assert "accounts:" in text
    assert not output.exists()


def test_init_config_cli_rejects_relative_staging_dir(tmp_path, monkeypatch, capsys):
    from virgilio_connector.__main__ import main
    output = tmp_path / "accounts.local.yaml"
    monkeypatch.setattr(sys, "argv", [
        "virgilio", "init-config",
        "--output", str(output),
        "--email", "box@example.com",
        "--staging-dir", "staging",
    ])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "absolute path" in captured.err
    assert not output.exists()


def test_install_windows_task_cli_dry_run_outputs_task_scheduler_payload(tmp_path, monkeypatch, capsys):
    from virgilio_connector.__main__ import main

    config = tmp_path / "accounts.local.yaml"
    config.write_text("accounts: []\n", encoding="utf-8")
    python_exe = tmp_path / "python.exe"
    python_exe.write_text("", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", [
        "virgilio", "install-windows-task",
        "--config", str(config),
        "--python-exe", str(python_exe),
        "--task-name", "Virgilio Test Watch",
        "--interval-seconds", "600",
        "--dry-run",
    ])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "dry_run"
    assert payload["task_name"] == "Virgilio Test Watch"
    assert payload["trigger"] == "ONLOGON"
    assert "--interval-seconds 600" in payload["task_action"]
    assert "schtasks" in payload["create_command"]


def test_install_windows_task_cli_registers_task(tmp_path, monkeypatch, capsys):
    import virgilio_connector.windows_task as windows_task
    from virgilio_connector.__main__ import main

    config = tmp_path / "accounts.local.yaml"
    config.write_text("accounts: []\n", encoding="utf-8")
    python_exe = tmp_path / "python.exe"
    python_exe.write_text("", encoding="utf-8")
    seen = {}

    def fake_run(args, **kwargs):
        seen["args"] = args
        seen["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="SUCCESS: The scheduled task has successfully been created.",
            stderr="",
        )

    monkeypatch.setattr(windows_task.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", [
        "virgilio", "install-windows-task",
        "--config", str(config),
        "--python-exe", str(python_exe),
        "--task-name", "Virgilio Test Watch",
        "--force",
    ])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "created"
    assert payload["task_name"] == "Virgilio Test Watch"
    assert seen["args"][:4] == ["schtasks", "/create", "/tn", "Virgilio Test Watch"]
    assert "/f" in seen["args"]
    assert seen["kwargs"]["capture_output"] is True
    assert seen["kwargs"]["text"] is True
    assert seen["kwargs"]["check"] is False


def test_console_script_registers_virgilio_entrypoint():
    data = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["scripts"]["virgilio"] == "virgilio_connector.__main__:main"


def setup(environ, fake, *, dry_run=False, enabled=True):
    return BucolicheSheetSetup(BucolicheConfig(enabled=enabled), environ=environ,
        client_factory=lambda *_: fake).run(dry_run=dry_run)


def setup_env():
    return {"VIRGILIO_BUCOLICHE_SPREADSHEET_ID": "sheet-test",
            "VIRGILIO_GOOGLE_SERVICE_ACCOUNT_JSON": "{}"}


def test_sheet_setup_dry_run_never_calls_google():
    fake = FakeReadClient()
    result = setup(setup_env(), fake, dry_run=True)
    assert result.status == "DRY_RUN" and len(result.actions) == 1
    assert fake.calls == []


def test_sheet_setup_creates_missing_and_writes_only_headers():
    fake = FakeReadClient({})
    result = setup(setup_env(), fake)
    assert result.status == "READY"
    assert [call[0] for call in fake.calls[1:]] == ["create_sheet", "write_header"]


def test_sheet_setup_empty_header_only_and_coherent_unchanged():
    fake = FakeReadClient({"bucoliche": ()})
    result = setup(setup_env(), fake)
    assert result.status == "READY"
    assert ("write_header", "bucoliche", EVENT_COLUMNS) in fake.calls


def test_sheet_setup_mismatch_blocks_without_any_write():
    fake = FakeReadClient({"bucoliche": ("wrong",)})
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
    assert fake.calls == ["inspect_sheets"]


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
