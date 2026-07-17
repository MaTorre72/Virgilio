from pathlib import Path

from virgilio_connector.application.account_management import AccountManagementService
from virgilio_connector.application.configuration import ConfigurationService
from virgilio_connector.application.credentials import AccountCredentialService, FakeCredentialStore
from virgilio_connector.user_app.app import UserAppShell
from virgilio_connector.user_app.navigation import UserRoute
from virgilio_connector.user_app.wizard import AccountView, WizardStep

from test_user_app import FakeButton, FakeLabel, FakeRoot, FakeTreeview, FakeTtk


class FakeHomeControl:
    def __init__(self):
        self.closed = False

    def check_now(self):
        return True

    def start(self):
        return True

    def pause(self):
        return True

    def close(self):
        self.closed = True


def _services(tmp_path: Path):
    configuration = ConfigurationService.for_file(tmp_path / "config.yaml")
    accounts = AccountManagementService(
        configuration, AccountCredentialService(FakeCredentialStore())
    )
    return configuration, accounts


def _open_account_step(shell: UserAppShell, limbo: Path) -> AccountView:
    shell.first_run.continue_forward()
    limbo.mkdir(exist_ok=True)
    shell.first_run.current_view.folder_entry.set(str(limbo.resolve()))
    shell.first_run.continue_forward()
    assert shell.first_run.step is WizardStep.ACCOUNT
    return shell.first_run.current_view


def _fill(view: AccountView, *, email="one@example.invalid", password="secret"):
    view.name_entry.set("Principale")
    view.email_entry.set(email)
    view.password_entry.set(password)


def test_active_mailbox_state_is_binary_visible_and_persisted(tmp_path):
    configuration, accounts = _services(tmp_path)
    shell = UserAppShell(
        FakeRoot(), configuration, ttk_module=FakeTtk, account_service=accounts
    )
    view = _open_account_step(shell, tmp_path / "limbo")
    _fill(view)

    assert "selected" in view.enabled_control.state()
    assert shell.first_run.add_account().is_valid
    assert accounts.list_accounts()[0].enabled is True

    view.enabled_control.state(("!selected",))
    view.toggle_enabled()
    view.table.select(accounts.list_accounts()[0].alias)
    assert shell.first_run.update_account().is_valid
    assert accounts.list_accounts()[0].enabled is False


def test_first_run_finishes_explicitly_on_home_without_restart(tmp_path):
    configuration, accounts = _services(tmp_path)
    shell = UserAppShell(
        FakeRoot(), configuration, ttk_module=FakeTtk, account_service=accounts
    )
    view = _open_account_step(shell, tmp_path / "limbo")
    _fill(view)
    assert shell.first_run.add_account().is_valid

    result = shell.first_run.continue_forward()

    assert result.is_valid
    assert shell.route is UserRoute.HOME
    assert shell.home is not None
    assert "Termina configurazione" in [button.kwargs.get("text") for button in FakeButton.created]


def test_home_reopens_existing_configuration_and_returns_after_edit(tmp_path):
    configuration, accounts = _services(tmp_path)
    first_shell = UserAppShell(
        FakeRoot(), configuration, ttk_module=FakeTtk, account_service=accounts
    )
    view = _open_account_step(first_shell, tmp_path / "limbo")
    _fill(view)
    first_shell.first_run.add_account()
    first_shell.first_run.continue_forward()

    first_shell.open_configuration()
    edit = first_shell.first_run.current_view
    alias = accounts.list_accounts()[0].alias
    edit.table.select(alias)
    edit.table.event_generate("<<TreeviewSelect>>")
    assert edit.email_entry.get() == "one@example.invalid"
    assert edit.password_entry.get() == "secret"

    edit.email_entry.set("changed@example.invalid")
    edit.password_entry.set("changed-secret")
    assert first_shell.first_run.update_account().is_valid
    assert first_shell.first_run.continue_forward().is_valid
    assert first_shell.route is UserRoute.HOME
    assert accounts.list_accounts()[0].email == "changed@example.invalid"


def test_window_controls_are_visible_and_close_owned_worker(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("present: true\n", encoding="utf-8")
    root = FakeRoot()
    control = FakeHomeControl()
    shell = UserAppShell(
        root,
        ConfigurationService.for_file(config),
        ttk_module=FakeTtk,
        home_control=control,
    )
    labels = [button.kwargs.get("text") for button in FakeButton.created]

    assert "Riduci a icona" in labels
    assert "Chiudi" in labels
    shell.minimize()
    assert root.iconified is True
    root.protocols["WM_DELETE_WINDOW"]()
    assert control.closed is True
    assert root.destroyed is True


def test_complete_visible_text_inventory_has_no_technical_or_legacy_terms(tmp_path):
    configuration, accounts = _services(tmp_path)
    shell = UserAppShell(
        FakeRoot(), configuration, ttk_module=FakeTtk, account_service=accounts
    )
    view = _open_account_step(shell, tmp_path / "limbo")
    _fill(view)
    shell.first_run.add_account()
    shell.first_run.continue_forward()
    shell.open_configuration()

    visible = " ".join(
        [widget.kwargs.get("text", "") for widget in (*FakeLabel.created, *FakeButton.created)]
        + [heading.get("text", "") for tree in FakeTreeview.created for heading in tree.headings.values()]
    ).lower()
    forbidden = {
        "python", "venv", "cli", "yaml", ".env", "doctor", "pilot",
        "dry-run", "watch", "staging", "ack", "manifest", "sqlite",
        "exit code", "account_alias", "username_env", "password_env",
        "stack trace", "percorso del repository", "diagnostica avanzata",
        "automazione win11", "setup iniziale", "monitoraggio", "manutenzione",
    }

    assert all(term not in visible for term in forbidden)
