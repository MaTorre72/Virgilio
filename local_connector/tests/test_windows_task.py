import json
import subprocess
import sys

import pytest

import virgilio_connector.windows_task as windows_task


def completed(args, *, returncode=0, payload=None, stderr=""):
    stdout = json.dumps(payload) if payload is not None else ""
    return subprocess.CompletedProcess(args, returncode, stdout=stdout, stderr=stderr)


def test_query_windows_task_parses_real_state(monkeypatch):
    payload = {
        "task_name": "Virgilio Local Watch", "installed": True, "state": "Ready",
        "last_run_time": "2026-07-14T08:00:00.0000000+02:00",
        "next_run_time": "", "last_result": 0,
    }
    monkeypatch.setattr(windows_task.os, "name", "nt")
    monkeypatch.setattr(windows_task.subprocess, "run",
                        lambda args, **kwargs: completed(args, payload=payload))

    status = windows_task.query_windows_watch_task("Virgilio Local Watch")

    assert status.installed is True
    assert status.state == "Ready"
    assert status.last_result == 0
    assert status.to_payload()["status"] == "installed"


def test_query_windows_task_reports_absent_and_rejects_bad_output(monkeypatch):
    monkeypatch.setattr(windows_task.os, "name", "nt")
    monkeypatch.setattr(windows_task.subprocess, "run", lambda args, **kwargs: completed(
        args, payload={"task_name": "Virgilio Local Watch", "installed": False}))
    assert windows_task.query_windows_watch_task("Virgilio Local Watch").installed is False

    monkeypatch.setattr(windows_task.subprocess, "run", lambda args, **kwargs:
                        subprocess.CompletedProcess(args, 0, stdout="not-json", stderr=""))
    with pytest.raises(windows_task.WindowsTaskError, match="unexpected"):
        windows_task.query_windows_watch_task("Virgilio Local Watch")

    monkeypatch.setattr(windows_task.subprocess, "run", lambda args, **kwargs:
                        subprocess.CompletedProcess(args, 1, stdout="", stderr="access denied"))
    with pytest.raises(windows_task.WindowsTaskError, match="access denied"):
        windows_task.query_windows_watch_task("Virgilio Local Watch")


def test_unregister_windows_task_is_idempotent(monkeypatch):
    monkeypatch.setattr(windows_task, "query_windows_watch_task", lambda name:
                        windows_task.WindowsTaskStatus(name, installed=False))
    monkeypatch.setattr(windows_task.subprocess, "run", lambda *args, **kwargs:
                        pytest.fail("delete must not run for an absent task"))
    assert windows_task.unregister_windows_watch_task("Virgilio Local Watch") == {
        "status": "not_installed", "task_name": "Virgilio Local Watch", "removed": False,
    }


def test_unregister_windows_task_deletes_existing_task(monkeypatch):
    seen = {}
    monkeypatch.setattr(windows_task, "query_windows_watch_task", lambda name:
                        windows_task.WindowsTaskStatus(name, installed=True))

    def fake_run(args, **kwargs):
        seen["args"] = args
        return subprocess.CompletedProcess(args, 0, stdout="SUCCESS", stderr="")

    monkeypatch.setattr(windows_task.subprocess, "run", fake_run)
    payload = windows_task.unregister_windows_watch_task("Virgilio Local Watch")
    assert seen["args"] == ["schtasks", "/delete", "/tn", "Virgilio Local Watch", "/f"]
    assert payload["status"] == "removed"
    assert payload["removed"] is True


def test_windows_task_status_cli_has_readable_last_result(monkeypatch, capsys):
    from virgilio_connector.__main__ import main

    monkeypatch.setattr("virgilio_connector.__main__.query_windows_watch_task", lambda name:
                        windows_task.WindowsTaskStatus(
                            name, installed=True, state="Ready",
                            last_run_time="2026-07-14T08:00:00+02:00", last_result=0))
    monkeypatch.setattr(sys, "argv", [
        "virgilio", "status-windows-task", "--task-name", "Virgilio Test Watch", "--human",
    ])
    assert main() == 0
    output = capsys.readouterr().out
    assert "Stato: Ready" in output
    assert "Ultimo esito: completato correttamente (0)" in output


def test_windows_task_uninstall_cli_requires_confirmation(monkeypatch, capsys):
    from virgilio_connector.__main__ import main

    called = False

    def fake_unregister(name):
        nonlocal called
        called = True
        return {"status": "removed", "task_name": name, "removed": True}

    monkeypatch.setattr("virgilio_connector.__main__.unregister_windows_watch_task", fake_unregister)
    monkeypatch.setattr(sys, "argv", ["virgilio", "uninstall-windows-task"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
    assert "requires --confirm" in capsys.readouterr().err
    assert called is False


def test_windows_task_uninstall_cli_is_idempotent(monkeypatch, capsys):
    from virgilio_connector.__main__ import main

    monkeypatch.setattr("virgilio_connector.__main__.unregister_windows_watch_task", lambda name: {
        "status": "not_installed", "task_name": name, "removed": False,
    })
    monkeypatch.setattr(sys, "argv", [
        "virgilio", "uninstall-windows-task", "--confirm", "--human",
    ])
    assert main() == 0
    assert "non installato" in capsys.readouterr().out
