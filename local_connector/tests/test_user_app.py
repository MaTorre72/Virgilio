import ast
from pathlib import Path

import pytest

from virgilio_connector.application.configuration import ConfigurationService
from virgilio_connector.user_app import launch_user_app
from virgilio_connector.user_app.app import USER_VIEWS, WINDOW_TITLE, UserAppShell
from virgilio_connector.user_app.navigation import UserRoute


class FakeRoot:
    def __init__(self):
        self.window_title = None
        self.minimum_size = None

    def title(self, value):
        self.window_title = value

    def minsize(self, width, height):
        self.minimum_size = (width, height)


class FakeWidget:
    created = []

    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.kwargs = kwargs
        self.grid_options = None
        type(self).created.append(self)

    def grid(self, **kwargs):
        self.grid_options = kwargs


class FakeFrame(FakeWidget):
    created = []


class FakeLabel(FakeWidget):
    created = []


class FakeTtk:
    Frame = FakeFrame
    Label = FakeLabel


@pytest.fixture(autouse=True)
def clear_widgets():
    FakeFrame.created.clear()
    FakeLabel.created.clear()


def build_shell(config_path: Path) -> UserAppShell:
    return UserAppShell(
        FakeRoot(),
        ConfigurationService.for_file(config_path),
        ttk_module=FakeTtk,
    )


def test_shell_has_caronte_title_and_routes_missing_configuration_to_first_run(tmp_path):
    shell = build_shell(tmp_path / "empty" / "config.yaml")

    assert WINDOW_TITLE == "Caronte"
    assert shell.root.window_title == WINDOW_TITLE
    assert shell.root.minimum_size == (720, 480)
    assert shell.route is UserRoute.FIRST_RUN
    assert [widget.kwargs["text"] for widget in FakeLabel.created] == [
        "Primo avvio",
        "Configuriamo insieme gli elementi necessari per iniziare.",
    ]


def test_shell_routes_existing_configuration_to_home(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("present: true\n", encoding="utf-8")

    shell = build_shell(config_path)

    assert shell.route is UserRoute.HOME
    assert FakeLabel.created[0].kwargs["text"] == "Home"


def test_user_app_imports_no_technical_or_legacy_presentation():
    package = Path(__file__).parents[1] / "src" / "virgilio_connector" / "user_app"
    forbidden_modules = {"maintenance_gui", "gui"}

    for source_path in package.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
                imported.update(alias.name for alias in node.names)
        assert all(
            name not in forbidden_modules and not name.startswith("gui_")
            for name in imported
        )


def test_user_view_inventory_excludes_legacy_tabs_and_forbidden_terms(tmp_path):
    legacy_tabs = {
        "Stato",
        "Setup iniziale",
        "Account mail",
        "Bucoliche",
        "Avvio",
        "Monitoraggio",
        "Manutenzione",
        "Automazione Win11",
        "Diagnostica avanzata",
    }
    forbidden_terms = {
        "python", "venv", "cli", "yaml", ".env", "doctor", "pilot",
        "dry-run", "watch", "staging", "ack", "manifest", "sqlite",
        "exit code", "account_alias", "username_env", "password_env",
        "stack trace", "percorso del repository",
    }
    visible_text = " ".join(
        widget.kwargs["text"]
        for route_path in (tmp_path / "missing", tmp_path / "present")
        for widget in _rendered_labels(route_path)
    ).lower()

    assert legacy_tabs.isdisjoint(USER_VIEWS)
    assert all(term not in visible_text for term in forbidden_terms)


def _rendered_labels(config_path: Path):
    FakeLabel.created.clear()
    if config_path.name == "present":
        config_path.write_text("present: true\n", encoding="utf-8")
    build_shell(config_path)
    return tuple(FakeLabel.created)


def test_user_gui_help_and_dispatch(monkeypatch, capsys, tmp_path):
    from virgilio_connector import __main__ as cli

    monkeypatch.setattr("sys.argv", ["virgilio", "--help"])
    with pytest.raises(SystemExit) as exc_info:
        cli.main()
    assert exc_info.value.code == 0
    assert "user-gui" in capsys.readouterr().out

    seen = {}

    def fake_launch_user_app(*, config_path=None):
        seen["config_path"] = config_path
        return 0

    monkeypatch.setattr("sys.argv", ["virgilio", "user-gui", "--config", str(tmp_path / "config.yaml")])
    monkeypatch.setattr("virgilio_connector.user_app.launch_user_app", fake_launch_user_app)
    assert cli.main() == 0
    assert seen["config_path"] == tmp_path / "config.yaml"
    assert callable(launch_user_app)
