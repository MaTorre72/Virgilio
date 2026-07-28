import sys

import pytest

from virgilio_connector import cli


SUPPORTED_COMMANDS = ("init-config", "doctor", "watch")
INTERNAL_COMMANDS = ("scan-imap-accounts", "pilot-preview", "user-gui", "maintenance-gui")


def test_top_level_help_exposes_only_supported_commands(monkeypatch, capsys):
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
    monkeypatch.setattr(sys, "argv", ["virgilio", "local-watch"])
    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_bootstrap_only_composes_cli_entrypoint():
    from virgilio_connector import __main__ as bootstrap

    assert bootstrap.main is cli.main
    assert not hasattr(bootstrap, "build_parser") or bootstrap is cli


@pytest.mark.parametrize(
    ("command", "group"),
    (
        ("init-config", "configuration"),
        ("watch", "pipeline"),
        ("export-to-bucoliche", "registry"),
        ("status-windows-task", "maintenance"),
        ("user-gui", "presentation"),
    ),
)
def test_parser_preserves_representative_command_groups(command, group):
    parser = cli.build_parser()
    choices = parser._subparsers._group_actions[0].choices

    assert command in choices, group
