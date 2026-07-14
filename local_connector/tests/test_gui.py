from pathlib import Path
import subprocess
import sys

import pytest

from virgilio_connector.gui import (
    GuiCommandSpec,
    build_cli_args,
    gui_actions_by_tab,
    gui_context_fields,
    gui_tabs,
    run_cli_command,
    sanitize_output,
)


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
        "--provider", "gmail_workspace",
        "--imap-port", "993",
        "--dry-run",
    ]


def test_build_cli_args_for_operational_tabs():
    assert build_cli_args(GuiCommandSpec(
        command="run-local-pipeline",
        config_path=Path("accounts.local.yaml"),
        dry_run=True,
        human=True,
    )) == [
        "run-local-pipeline", "--config", "accounts.local.yaml", "--dry-run", "--human",
    ]
    assert build_cli_args(GuiCommandSpec(
        command="watch",
        config_path=Path("accounts.local.yaml"),
        human=True,
        interval_seconds=60,
        max_cycles=1,
    )) == [
        "watch", "--config", "accounts.local.yaml", "--human",
        "--interval-seconds", "60", "--max-cycles", "1",
    ]
    assert build_cli_args(GuiCommandSpec(
        command="doctor-bucoliche",
        config_path=Path("accounts.local.yaml"),
        human=True,
    )) == ["doctor-bucoliche", "--config", "accounts.local.yaml", "--human"]


def test_build_cli_args_for_maintenance_and_windows_task():
    assert build_cli_args(GuiCommandSpec(
        command="reset-local-state",
        backup=True,
        confirm=True,
        human=True,
    )) == ["reset-local-state", "--backup", "--confirm", "--human"]
    assert build_cli_args(GuiCommandSpec(
        command="install-windows-task",
        config_path=Path("accounts.local.yaml"),
        python_exe=Path("C:/Python/python.exe"),
        task_name="Virgilio Test Watch",
        interval_seconds=120,
        dry_run=True,
    )) == [
        "install-windows-task", "--config", "accounts.local.yaml",
        "--python-exe", "C:\\Python\\python.exe",
        "--task-name", "Virgilio Test Watch",
        "--interval-seconds", "120",
        "--dry-run",
    ]


def test_build_cli_args_rejects_missing_required_values():
    with pytest.raises(ValueError, match="Seleziona prima"):
        build_cli_args(GuiCommandSpec(command="doctor"))
    with pytest.raises(ValueError, match="Scegli dove salvare"):
        build_cli_args(GuiCommandSpec(command="init-config"))


def test_gui_registry_has_required_tabs_and_disabled_missing_cli_actions():
    assert gui_tabs() == (
        "Stato",
        "Setup iniziale",
        "Account mail",
        "Bucoliche",
        "Avvio",
        "Monitoraggio",
        "Manutenzione",
        "Automazione Win11",
        "Diagnostica avanzata",
    )
    actions = gui_actions_by_tab()
    assert all(actions[tab] for tab in gui_tabs())
    unavailable = {
        action.key: action.unavailable_reason
        for tab_actions in actions.values()
        for action in tab_actions
        if not action.available
    }
    assert unavailable["win11-status"] == "CLI mancante: status-windows-task"
    assert unavailable["maintenance-backup"] == "CLI mancante: backup-local-state"


def test_gui_settings_are_contextual_and_technical_fields_are_isolated():
    fields = gui_context_fields()
    assert fields["Stato"] == ()
    assert fields["Setup iniziale"] == (
        "profile", "init_output", "init_email", "local_data", "limbo", "scanner",
    )
    assert fields["Bucoliche"] == ("shared_register",)
    assert fields["Avvio"] == ("interval", "safe_test")
    assert fields["Manutenzione"] == ("confirm_reset",)
    assert fields["Automazione Win11"] == ("interval", "task_name")
    assert fields["Diagnostica avanzata"] == ("python", "format", "max_cycles")
    ordinary = {
        field for tab, tab_fields in fields.items()
        if tab != "Diagnostica avanzata" for field in tab_fields
    }
    assert ordinary.isdisjoint({"python", "format", "max_cycles"})
    ordinary_text = " ".join(
        f"{action.label} {action.summary}" for tab, actions in gui_actions_by_tab().items()
        if tab != "Diagnostica avanzata" for action in actions
    ).lower()
    assert "staging" not in ordinary_text


def test_sanitize_output_redacts_obvious_secret_values():
    text = "password=abc token:xyz ok"
    assert sanitize_output(text) == "password=<redacted> token:<redacted> ok"


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
