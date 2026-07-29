from __future__ import annotations

from dataclasses import replace

import pytest

from virgilio_connector.application.configuration import ConfigurationService
from virgilio_connector.application.credentials import (
    AccountCredentials,
    CredentialAlreadyExistsError,
    CredentialNotFoundError,
)
from virgilio_connector.application.windows_credentials import (
    ERROR_ACCESS_DENIED,
    ERROR_NOT_FOUND,
    CredentialAccessDeniedError,
    WindowsCredentialApiError,
    WindowsCredentialStore,
    create_account_credential_service,
    credential_error_message,
)
from virgilio_connector.multi_account import LocalImapAccount, scaffold_local_config


class MockWindowsCredentialApi:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.calls: list[tuple[str, str]] = []
        self.error: tuple[str, int] | None = None

    def write(self, target: str, value: str) -> None:
        self._maybe_fail("write")
        self.calls.append(("write", target))
        self.values[target] = value

    def read(self, target: str) -> str:
        self._maybe_fail("read")
        self.calls.append(("read", target))
        try:
            return self.values[target]
        except KeyError as exc:
            raise WindowsCredentialApiError("read", ERROR_NOT_FOUND) from exc

    def delete(self, target: str) -> None:
        self._maybe_fail("delete")
        self.calls.append(("delete", target))
        try:
            del self.values[target]
        except KeyError as exc:
            raise WindowsCredentialApiError("delete", ERROR_NOT_FOUND) from exc

    def _maybe_fail(self, operation: str) -> None:
        if self.error == (operation, ERROR_ACCESS_DENIED):
            raise WindowsCredentialApiError(operation, ERROR_ACCESS_DENIED)


def account(alias: str) -> LocalImapAccount:
    return LocalImapAccount(
        account_alias=alias,
        email=f"{alias}@example.invalid",
        provider_hint="generic_imap",
        imap_host="imap.example.invalid",
        imap_port=993,
        username_env=f"VIRGILIO_{alias.upper()}_USERNAME",
        password_env=f"VIRGILIO_{alias.upper()}_PASSWORD",
        input_folder="INBOX",
        done_folder="Processed",
        error_folder="Errors",
    )


def test_windows_adapter_contract_uses_mocked_system_api():
    api = MockWindowsCredentialApi()
    store = WindowsCredentialStore(api)

    store.save("ACCOUNT_PASSWORD", "synthetic-secret")
    assert store.read("ACCOUNT_PASSWORD") == "synthetic-secret"
    with pytest.raises(CredentialAlreadyExistsError):
        store.save("ACCOUNT_PASSWORD", "duplicate-secret")
    store.update("ACCOUNT_PASSWORD", "updated-secret")
    store.delete("ACCOUNT_PASSWORD")

    assert api.values == {}
    assert ("write", "Caronte/ACCOUNT_PASSWORD") in api.calls
    with pytest.raises(CredentialNotFoundError):
        store.read("ACCOUNT_PASSWORD")


def test_factory_service_removes_both_account_credentials_from_mock_backend():
    api = MockWindowsCredentialApi()
    item = account("account_1")
    service = create_account_credential_service(api)

    service.save(item, AccountCredentials("synthetic-user", "synthetic-password"))
    service.delete(item)

    assert api.values == {}
    assert ("delete", f"Caronte/{item.username_env}") in api.calls
    assert ("delete", f"Caronte/{item.password_env}") in api.calls


def test_structural_model_keeps_only_references_for_two_accounts(tmp_path):
    path = tmp_path / "accounts.yaml"
    path.write_text(
        scaffold_local_config(
            email="account.1@example.invalid",
            staging_dir=(tmp_path / "limbo").resolve(),
        ),
        encoding="utf-8",
    )
    first = ConfigurationService.for_file(path).load().accounts[0]
    second = replace(
        first,
        account_alias="account_2",
        email="account.2@example.invalid",
        username_env="VIRGILIO_ACCOUNT_2_USERNAME",
        password_env="VIRGILIO_ACCOUNT_2_PASSWORD",
    )
    api = MockWindowsCredentialApi()
    service = create_account_credential_service(api)
    service.save(first, AccountCredentials("synthetic-user-1", "synthetic-password-1"))
    service.save(second, AccountCredentials("synthetic-user-2", "synthetic-password-2"))

    structural_text = path.read_text(encoding="utf-8") + repr((first, second))
    for secret in (
        "synthetic-user-1",
        "synthetic-password-1",
        "synthetic-user-2",
        "synthetic-password-2",
    ):
        assert secret not in structural_text
    assert service.read(first) == AccountCredentials(
        "synthetic-user-1", "synthetic-password-1"
    )
    assert service.read(second) == AccountCredentials(
        "synthetic-user-2", "synthetic-password-2"
    )


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (CredentialNotFoundError("safe"), "non sono state trovate"),
        (CredentialAlreadyExistsError("safe"), "esistono gia`"),
    ],
)
def test_typed_errors_have_safe_user_messages(error, message):
    assert message in credential_error_message(error)


def test_windows_access_error_is_typed_and_does_not_expose_secret():
    api = MockWindowsCredentialApi()
    api.error = ("read", ERROR_ACCESS_DENIED)
    store = WindowsCredentialStore(api)

    with pytest.raises(CredentialAccessDeniedError) as captured:
        store.read("SAFE_REFERENCE")

    assert "synthetic-password" not in str(captured.value)
    assert "non consente" in credential_error_message(captured.value)
