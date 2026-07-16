from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from virgilio_connector.application.home_status import AccountHomeStatusService, HomeStatus
from virgilio_connector.application.configuration import ConfigurationService
from virgilio_connector.user_app.app import UserAppShell
from virgilio_connector.user_app.home import StaticHomeStatusService

from test_user_app import FakeButton, FakeFrame, FakeLabel, FakeRoot, FakeTtk


def _home(tmp_path, status):
    FakeFrame.created.clear()
    FakeLabel.created.clear()
    FakeButton.created.clear()
    config = tmp_path / "config.yaml"
    config.write_text("present: true\n", encoding="utf-8")
    return UserAppShell(
        FakeRoot(),
        ConfigurationService.for_file(config),
        ttk_module=FakeTtk,
        home_status=StaticHomeStatusService(status),
    )


def _visible_text():
    return " ".join(
        widget.kwargs.get("text", "")
        for widget_type in (FakeLabel, FakeButton)
        for widget in widget_type.created
    )


@pytest.mark.parametrize(
    "state", ("Pronto", "Controllo in corso", "In pausa", "Richiede attenzione")
)
def test_home_renders_main_general_states(tmp_path, state):
    shell = _home(tmp_path, HomeStatus(state, 2))

    assert shell.home.status.state == state
    assert f"Stato generale: {state}" in _visible_text()
    assert "Caselle attive: 2" in _visible_text()


def test_home_status_service_counts_only_active_accounts():
    accounts = SimpleNamespace(list_accounts=lambda: (
        SimpleNamespace(enabled=True),
        SimpleNamespace(enabled=True),
        SimpleNamespace(enabled=False),
    ))

    status = AccountHomeStatusService(accounts).get_status()

    assert status.state == "Pronto"
    assert status.active_accounts == 2


def test_home_renders_last_check_in_europe_rome(tmp_path):
    _home(tmp_path, HomeStatus("Pronto", 2, datetime(2026, 7, 16, 8, 5, tzinfo=timezone.utc)))

    assert "Ultimo controllo: 16/07/2026 10:05" in _visible_text()


def test_home_has_exactly_the_three_primary_actions(tmp_path):
    _home(tmp_path, HomeStatus("Pronto", 2))

    labels = [button.kwargs["text"] for button in FakeButton.created]
    assert [label for label in labels if label in {"Controlla ora", "Avvia", "Pausa"}] == [
        "Controlla ora", "Avvia", "Pausa"
    ]
    assert "Impostazioni" in labels


def test_home_contains_no_technical_output_or_forbidden_terms(tmp_path):
    _home(tmp_path, HomeStatus("Pronto", 2))
    visible = _visible_text().lower()
    forbidden = {
        "json", "python", "venv", "cli", "yaml", ".env", "doctor", "pilot",
        "dry-run", "watch", "staging", "ack", "manifest", "sqlite",
        "exit code", "account_alias", "username_env", "password_env",
        "stack trace", "percorso del repository",
    }

    assert all(term not in visible for term in forbidden)
