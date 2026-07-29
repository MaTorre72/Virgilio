from dataclasses import replace

import pytest

from virgilio_connector.application.credentials import (
    AccountCredentials,
    AccountCredentialService,
    CredentialAlreadyExistsError,
    CredentialNotFoundError,
    CredentialStore,
    FakeCredentialStore,
)
from virgilio_connector.application.configuration import ConfigurationService
from virgilio_connector.multi_account import (
    LocalImapAccount,
    scaffold_local_config,
)


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


@pytest.mark.parametrize("store_factory", [FakeCredentialStore])
def test_fake_store_implements_public_contract_and_crud(store_factory):
    store: CredentialStore = store_factory()

    store.save("credential-ref", "first-secret")
    assert store.read("credential-ref") == "first-secret"
    with pytest.raises(CredentialAlreadyExistsError, match="credential-ref"):
        store.save("credential-ref", "duplicate-secret")

    store.update("credential-ref", "updated-secret")
    assert store.read("credential-ref") == "updated-secret"
    store.delete("credential-ref")
    with pytest.raises(CredentialNotFoundError, match="credential-ref"):
        store.read("credential-ref")


def test_account_service_uses_fake_store_and_isolates_two_accounts():
    first = account("account_1")
    second = replace(
        first,
        account_alias="account_2",
        email="account_2@example.invalid",
        username_env="VIRGILIO_ACCOUNT_2_USERNAME",
        password_env="VIRGILIO_ACCOUNT_2_PASSWORD",
    )
    service = AccountCredentialService(FakeCredentialStore())

    service.save(first, AccountCredentials("first-user", "first-secret"))
    service.save(second, AccountCredentials("second-user", "second-secret"))

    assert service.read(first) == AccountCredentials("first-user", "first-secret")
    assert service.read(second) == AccountCredentials("second-user", "second-secret")

    service.update(first, AccountCredentials("new-first-user", "new-first-secret"))
    service.delete(second)
    assert service.read(first) == AccountCredentials("new-first-user", "new-first-secret")
    with pytest.raises(CredentialNotFoundError):
        service.read(second)


def test_secret_values_are_absent_from_structural_file_logs_and_errors(tmp_path, caplog):
    path = tmp_path / "config.yaml"
    path.write_text(
        scaffold_local_config(
            email="account.1@example.invalid",
            staging_dir=(tmp_path / "limbo").resolve(),
        ),
        encoding="utf-8",
    )
    item = ConfigurationService.for_file(path).load().accounts[0]
    credentials = AccountCredentials("private-user", "private-secret")
    store = FakeCredentialStore()
    service = AccountCredentialService(store)

    service.save(item, credentials)
    text = repr(credentials) + path.read_text(encoding="utf-8") + caplog.text
    with pytest.raises(CredentialAlreadyExistsError) as captured:
        service.save(item, AccountCredentials("other-user", "other-secret"))
    text += str(captured.value)

    for secret in ("private-user", "private-secret", "other-user", "other-secret"):
        assert secret not in text
