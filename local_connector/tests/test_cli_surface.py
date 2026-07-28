import sys

import pytest


SUPPORTED_COMMANDS = ("init-config", "doctor", "watch")
INTERNAL_COMMANDS = ("scan-imap-accounts", "pilot-preview", "user-gui", "maintenance-gui")


def test_top_level_help_exposes_only_supported_commands(monkeypatch, capsys):
    from virgilio_connector import __main__ as cli

    monkeypatch.setattr(sys, "argv", ["virgilio", "--help"])
    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "{init-config,doctor,watch}" in help_text
    assert all(command in help_text for command in SUPPORTED_COMMANDS)
    assert all(command not in help_text for command in INTERNAL_COMMANDS)
    assert "local-watch" not in help_text


def test_removed_local_watch_alias_is_rejected(monkeypatch, capsys):
    from virgilio_connector import __main__ as cli

    monkeypatch.setattr(sys, "argv", ["virgilio", "local-watch"])
    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2
    assert "invalid choice" in capsys.readouterr().err
