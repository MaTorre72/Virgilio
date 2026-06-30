from pathlib import Path
import subprocess
import sys

import pytest

from virgilio_connector.gui import GuiCommandSpec, build_cli_args, run_cli_command


def test_build_cli_args_for_doctor_and_pilot():
    doctor_args = build_cli_args(GuiCommandSpec(
        command="doctor",
        config_path=Path("accounts.local.yaml"),
    ))
    pilot_args = build_cli_args(GuiCommandSpec(
        command="pilot",
        config_path=Path("accounts.local.yaml"),
        human=True,
    ))
    assert doctor_args == ["doctor", "--config", "accounts.local.yaml"]
    assert pilot_args == ["pilot", "--config", "accounts.local.yaml", "--human"]


def test_build_cli_args_for_init_config_dry_run():
    args = build_cli_args(GuiCommandSpec(
        command="init-config",
        output_path=Path("accounts.local.yaml"),
        email="box@example.com",
        staging_dir=Path("C:/Virgilio/staging"),
        dry_run=True,
    ))
    assert args == [
        "init-config",
        "--output", "accounts.local.yaml",
        "--email", "box@example.com",
        "--staging-dir", "C:\\Virgilio\\staging",
        "--dry-run",
    ]


def test_build_cli_args_rejects_missing_required_values():
    with pytest.raises(ValueError, match="config_path is required"):
        build_cli_args(GuiCommandSpec(command="doctor"))
    with pytest.raises(ValueError, match="output_path is required"):
        build_cli_args(GuiCommandSpec(command="init-config"))


def test_run_cli_command_invokes_module(monkeypatch):
    seen = {}

    def fake_run(args, **kwargs):
        seen["args"] = args
        seen["kwargs"] = kwargs
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = run_cli_command(["doctor", "--config", "accounts.local.yaml"])

    assert seen["args"] == [sys.executable, "-m", "virgilio_connector",
                             "doctor", "--config", "accounts.local.yaml"]
    assert seen["kwargs"]["capture_output"] is True
    assert seen["kwargs"]["text"] is True
    assert seen["kwargs"]["check"] is False
    assert result.stdout == "ok"
