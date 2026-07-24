import pytest
from types import SimpleNamespace

from virgilio_connector.application.credentials import FakeCredentialStore
from virgilio_connector.application.operational_connection import (
    CONNECTION_CREDENTIAL,
    OperationalConnectionService,
)


def test_connection_stores_only_endpoint_in_config_and_code_in_credentials(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("preferences:\n  interval_seconds: 300\n", encoding="utf-8")
    credentials = FakeCredentialStore()
    service = OperationalConnectionService(config, credentials)

    result = service.configure(
        "https://script.google.com/macros/s/deployment/exec",
        "protected-code",
    )

    assert result.configured is True
    text = config.read_text(encoding="utf-8")
    assert "https://script.google.com/macros/s/deployment/exec" in text
    assert "protected-code" not in text
    assert credentials.read(CONNECTION_CREDENTIAL) == "protected-code"
    assert service.runtime_environment() == {
        "VIRGILIO_CARONTE_DRIVE_VERIFY_URL":
            "https://script.google.com/macros/s/deployment/exec",
        "VIRGILIO_CARONTE_INTAKE_URL":
            "https://script.google.com/macros/s/deployment/exec",
        "VIRGILIO_TOKEN": "protected-code",
    }


def test_connection_can_be_reopened_and_updated_without_exposing_code(tmp_path):
    config = tmp_path / "config.yaml"
    credentials = FakeCredentialStore()
    service = OperationalConnectionService(config, credentials)
    service.configure("https://example.invalid/first", "first-code")

    reopened = OperationalConnectionService(config, credentials)
    snapshot = reopened.load()
    updated = reopened.configure("https://example.invalid/second", "second-code")

    assert snapshot.configured is True
    assert snapshot.endpoint_url == "https://example.invalid/first"
    assert updated.endpoint_url == "https://example.invalid/second"
    assert credentials.read(CONNECTION_CREDENTIAL) == "second-code"
    assert "first-code" not in config.read_text(encoding="utf-8")
    assert "second-code" not in config.read_text(encoding="utf-8")


@pytest.mark.parametrize("endpoint", ["", "http://example.invalid/exec", "not-a-url"])
def test_connection_rejects_invalid_endpoint_without_writing_secret(tmp_path, endpoint):
    config = tmp_path / "config.yaml"
    credentials = FakeCredentialStore()
    service = OperationalConnectionService(config, credentials)

    with pytest.raises(ValueError, match="HTTPS"):
        service.configure(endpoint, "protected-code")

    assert not config.exists()
    assert service.runtime_environment() == {}


def test_connection_requires_access_code(tmp_path):
    service = OperationalConnectionService(tmp_path / "config.yaml", FakeCredentialStore())

    with pytest.raises(ValueError, match="chiave"):
        service.configure("https://example.invalid/exec", "")


def test_existing_protected_key_is_kept_when_administrator_leaves_field_empty(tmp_path):
    path = tmp_path / "config.yaml"
    credentials = FakeCredentialStore()
    service = OperationalConnectionService(path, credentials)
    service.configure("https://example.invalid/first", "protected-code")

    result = service.configure("https://example.invalid/second", "")

    assert result.configured
    assert result.endpoint_url == "https://example.invalid/second"
    assert credentials.read(CONNECTION_CREDENTIAL) == "protected-code"


def test_installed_worker_hydrates_mailbox_and_connection_credentials(
    tmp_path, monkeypatch
):
    import virgilio_connector.__main__ as cli

    account = SimpleNamespace(
        username_env="VIRGILIO_IMAP_ACCOUNT_USERNAME",
        password_env="VIRGILIO_IMAP_ACCOUNT_PASSWORD",
    )
    account_credentials = SimpleNamespace(username="user@example.invalid", password="secret")
    monkeypatch.setattr(cli.os, "environ", {})
    monkeypatch.setattr(
        cli,
        "create_account_credential_service",
        lambda: SimpleNamespace(read=lambda selected: account_credentials),
    )
    monkeypatch.setattr(
        cli,
        "create_operational_connection_service",
        lambda path: SimpleNamespace(runtime_environment=lambda: {
            "VIRGILIO_CARONTE_DRIVE_VERIFY_URL": "https://example.invalid/exec",
            "VIRGILIO_CARONTE_INTAKE_URL": "https://example.invalid/exec",
            "VIRGILIO_TOKEN": "protected-code",
        }),
    )

    runtime = cli._protected_runtime_environment(tmp_path / "config.yaml", (account,))

    assert runtime == {
        "VIRGILIO_IMAP_ACCOUNT_USERNAME": "user@example.invalid",
        "VIRGILIO_IMAP_ACCOUNT_PASSWORD": "secret",
        "VIRGILIO_CARONTE_DRIVE_VERIFY_URL": "https://example.invalid/exec",
        "VIRGILIO_CARONTE_INTAKE_URL": "https://example.invalid/exec",
        "VIRGILIO_TOKEN": "protected-code",
    }


def test_cli_environment_takes_precedence_over_protected_values(tmp_path, monkeypatch):
    import virgilio_connector.__main__ as cli

    account = SimpleNamespace(
        username_env="VIRGILIO_IMAP_ACCOUNT_USERNAME",
        password_env="VIRGILIO_IMAP_ACCOUNT_PASSWORD",
    )
    existing = {
        "VIRGILIO_IMAP_ACCOUNT_USERNAME": "cli-user",
        "VIRGILIO_IMAP_ACCOUNT_PASSWORD": "cli-password",
        "VIRGILIO_CARONTE_DRIVE_VERIFY_URL": "https://cli.invalid/verify",
        "VIRGILIO_CARONTE_INTAKE_URL": "https://cli.invalid/intake",
        "VIRGILIO_TOKEN": "cli-code",
    }
    monkeypatch.setattr(cli.os, "environ", existing)
    monkeypatch.setattr(
        cli,
        "create_account_credential_service",
        lambda: pytest.fail("protected mailbox store must not be read"),
    )
    monkeypatch.setattr(
        cli,
        "create_operational_connection_service",
        lambda path: pytest.fail("protected connection store must not be read"),
    )

    assert cli._protected_runtime_environment(
        tmp_path / "config.yaml", (account,)
    ) == existing
