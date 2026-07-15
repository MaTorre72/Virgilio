from pathlib import Path

from virgilio_connector.application.account_management import AccountManagementService
from virgilio_connector.application.configuration import ConfigurationService
from virgilio_connector.application.credentials import AccountCredentialService, FakeCredentialStore
from virgilio_connector.user_app.app import UserAppShell
from virgilio_connector.user_app.navigation import UserRoute
from virgilio_connector.user_app.wizard import AccountView, FirstRunController

from test_user_app import FakeRoot, FakeTtk


def _open_accounts(tmp_path: Path):
    config_path = tmp_path / "config.yaml"
    credential_store = FakeCredentialStore()
    service = AccountManagementService(
        ConfigurationService.for_file(config_path),
        AccountCredentialService(credential_store),
    )
    controller = FirstRunController(
        FakeRoot(), ttk_module=FakeTtk, account_service=service
    )
    controller.continue_forward()
    controller.current_view.folder_entry.set("C:\\Limbo")
    controller.continue_forward()
    return controller, service, credential_store, config_path


def _fill(view: AccountView, *, name: str, email: str, password: str, host: str):
    view.name_entry.set(name)
    view.email_entry.set(email)
    view.password_entry.set(password)
    view.host_entry.set(host)
    view.port_entry.set("993")


def test_mailbox_table_has_expected_columns_and_two_synthetic_rows(tmp_path):
    controller, service, _, _ = _open_accounts(tmp_path)
    view = controller.current_view

    _fill(view, name="Principale", email="one@example.invalid", password="one-secret", host="imap.gmail.com")
    assert controller.add_account().is_valid
    _fill(view, name="Archivio", email="two@example.invalid", password="two-secret", host="imap.example.invalid")
    assert controller.add_account().is_valid

    assert view.table.headings == {
        "name": {"text": "Nome casella"},
        "email": {"text": "Email"},
        "provider": {"text": "Provider"},
        "status": {"text": "Stato"},
    }
    assert len(view.table.rows) == 2
    assert len(service.list_accounts()) == 2


def test_multi_account_view_has_no_forbidden_technical_terms(tmp_path):
    controller, _, _, _ = _open_accounts(tmp_path)
    view = controller.current_view
    visible = " ".join(
        [item["text"] for item in view.table.headings.values()]
        + [widget.kwargs.get("text", "") for widget in FakeTtk.Label.created]
        + [widget.kwargs.get("text", "") for widget in FakeTtk.Button.created]
    ).lower()
    forbidden = {
        "python", "venv", "cli", "yaml", ".env", "doctor", "pilot",
        "dry-run", "watch", "staging", "ack", "manifest", "sqlite",
        "exit code", "account_alias", "username_env", "password_env",
        "stack trace", "percorso del repository",
    }

    assert all(term not in visible for term in forbidden)


def test_account_crud_supports_different_providers_and_separate_credentials(tmp_path):
    controller, service, credential_store, _ = _open_accounts(tmp_path)
    view = controller.current_view

    _fill(view, name="Principale", email="one@example.invalid", password="one-secret", host="imap.gmail.com")
    controller.add_account()
    _fill(view, name="Archivio", email="two@example.invalid", password="two-secret", host="imap.example.invalid")
    controller.add_account()

    accounts = service.configuration.load().accounts
    assert [account.provider_hint for account in accounts] == ["gmail_workspace", "custom_imap"]
    assert accounts[0].username_env != accounts[1].username_env
    assert accounts[0].password_env != accounts[1].password_env
    assert credential_store.read(accounts[0].password_env) == "one-secret"
    assert credential_store.read(accounts[1].password_env) == "two-secret"

    view.table.select(accounts[0].account_alias)
    _fill(view, name="Principale", email="changed@example.invalid", password="changed-secret", host="imap.changed.invalid")
    assert controller.update_account().is_valid
    changed = service.configuration.load().accounts[0]
    assert changed.email == "changed@example.invalid"
    assert changed.imap_host == "imap.changed.invalid"
    assert credential_store.read(changed.password_env) == "changed-secret"

    view.table.select(accounts[1].account_alias)
    assert controller.remove_account().is_valid
    assert [item.email for item in service.list_accounts()] == ["changed@example.invalid"]


def test_two_accounts_persist_after_shell_is_closed_and_reopened(tmp_path):
    controller, service, credential_store, config_path = _open_accounts(tmp_path)
    view = controller.current_view
    _fill(view, name="Principale", email="one@example.invalid", password="one-secret", host="imap.gmail.com")
    controller.add_account()
    _fill(view, name="Archivio", email="two@example.invalid", password="two-secret", host="imap.example.invalid")
    controller.add_account()
    controller.current_view.frame.destroy()

    reopened_configuration = ConfigurationService.for_file(config_path)
    reopened = AccountManagementService(
        reopened_configuration, AccountCredentialService(credential_store)
    )
    shell = UserAppShell(
        FakeRoot(), reopened_configuration, ttk_module=FakeTtk,
        account_service=reopened,
    )

    assert shell.route is UserRoute.HOME
    assert [item.email for item in reopened.list_accounts()] == [
        "one@example.invalid", "two@example.invalid"
    ]
