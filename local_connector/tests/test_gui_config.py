from dataclasses import replace
import os
from pathlib import Path

import pytest

from virgilio_connector.gui_config import GuiConfigService, GuiRuntimeSettings, LocalCredentials
from virgilio_connector.multi_account import MultiAccountConfigError, scaffold_local_config


def service_with_one_account(tmp_path: Path) -> GuiConfigService:
    yaml_path = tmp_path / "accounts.local.yaml"
    yaml_path.write_text(scaffold_local_config(
        email="account.1@example.invalid", staging_dir=tmp_path / "staging"
    ), encoding="utf-8")
    values_path = tmp_path / ".env.local"
    values_path.write_text("VIRGILIO_IMAP_ACCOUNT_1_USERNAME=user1@example.invalid\n"
                           "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD=secret-one\n"
                           "UNRELATED=value\n", encoding="utf-8")
    return GuiConfigService(yaml_path, values_path)


def test_runtime_settings_round_trip_preserves_credentials(tmp_path):
    service = service_with_one_account(tmp_path)
    settings = GuiRuntimeSettings(
        local_data_dir=(tmp_path / "local-data").resolve(),
        scanner="defender",
        interval_seconds=120,
        task_name="Caronte test",
    )

    service.save_runtime_settings(settings)

    assert service.load_runtime_settings() == settings
    values = service.local_values_path.read_text(encoding="utf-8")
    assert "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD=secret-one" in values


@pytest.mark.parametrize("settings", [
    GuiRuntimeSettings(local_data_dir=Path("relative")),
    GuiRuntimeSettings(scanner="unknown"),
    GuiRuntimeSettings(interval_seconds=0),
])
def test_runtime_settings_reject_invalid_values(settings):
    with pytest.raises(MultiAccountConfigError):
        settings.validate()


def test_round_trip_crud_multi_account_keeps_secrets_local(tmp_path):
    service = service_with_one_account(tmp_path)
    model = service.load()
    second = service.new_account(
        account_alias="account_2", email="account.2@example.invalid",
        provider_hint="generic_imap", imap_host="imap.example.invalid", imap_port=993,
        input_folder="INBOX", done_folder="done", error_folder="error",
    )
    model = model.create_account(second, LocalCredentials("user2@example.invalid", "secret-two"))
    model = model.update_account("account_1", replace(model.accounts[0], enabled=False))
    service.save(model)
    loaded = service.load()
    assert [(item.account_alias, item.enabled) for item in loaded.accounts] == [
        ("account_1", False), ("account_2", True)
    ]
    assert loaded.credentials["account_2"].password == "secret-two"
    yaml_text = service.yaml_path.read_text(encoding="utf-8")
    assert "secret-one" not in yaml_text and "secret-two" not in yaml_text
    assert "bucoliche:" in yaml_text and "rules:" in yaml_text
    assert "UNRELATED=value" in service.local_values_path.read_text(encoding="utf-8")


def test_remove_account_removes_its_local_credentials(tmp_path):
    service = service_with_one_account(tmp_path)
    model = service.load()
    second = service.new_account(
        account_alias="account_2", email="account.2@example.invalid",
        provider_hint="generic_imap", imap_host="imap.example.invalid", imap_port=993,
        input_folder="INBOX", done_folder="done", error_folder="error",
    )
    service.save(model.create_account(second, LocalCredentials("user2", "secret-two")))
    service.save(service.load().remove_account("account_2"))
    text = service.local_values_path.read_text(encoding="utf-8")
    assert "ACCOUNT_2" not in text and "secret-two" not in text


def test_duplicate_alias_and_env_names_are_rejected(tmp_path):
    service = service_with_one_account(tmp_path)
    model = service.load()
    with pytest.raises(MultiAccountConfigError, match="unique"):
        model.create_account(model.accounts[0])
    duplicate_env = service.new_account(
        account_alias="account_2", email="account.2@example.invalid",
        provider_hint="generic_imap", imap_host="imap.example.invalid", imap_port=993,
        input_folder="INBOX", done_folder="done", error_folder="error",
    )
    duplicate_env = replace(duplicate_env, username_env=model.accounts[0].username_env)
    with pytest.raises(MultiAccountConfigError, match="environment variable names"):
        model.create_account(duplicate_env)


def test_failed_second_replace_rolls_back_both_files(tmp_path, monkeypatch):
    service = service_with_one_account(tmp_path)
    yaml_before = service.yaml_path.read_bytes()
    values_before = service.local_values_path.read_bytes()
    original_replace = Path.replace
    calls = 0

    def fail_second_replace(path, target):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic write failure")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_second_replace)
    with pytest.raises(MultiAccountConfigError, match="previous values restored"):
        service.save(service.load())
    assert service.yaml_path.read_bytes() == yaml_before
    assert service.local_values_path.read_bytes() == values_before


def test_error_messages_do_not_expose_credentials(tmp_path):
    service = service_with_one_account(tmp_path)
    model = service.load()
    with pytest.raises(MultiAccountConfigError) as error:
        replace(model.accounts[0], username_env="bad")
    assert "secret-one" not in str(error.value)


def test_local_credentials_are_reopened_redacted_and_written_privately(tmp_path):
    service = service_with_one_account(tmp_path)
    model = service.load()
    service.save(replace(model, credentials={
        "account_1": LocalCredentials("user1@example.invalid", "new-secret-value")
    }))

    assert service.load().credentials["account_1"].password == "new-secret-value"
    assert "new-secret-value" not in service.yaml_path.read_text(encoding="utf-8")
    assert service.redact("failure for new-secret-value") == "failure for <redacted>"
    assert service.redact("draft-secret failed", ("draft-secret",)) == "<redacted> failed"
    if os.name != "nt":
        assert service.local_values_path.stat().st_mode & 0o077 == 0


def test_local_credentials_write_failure_is_redacted_and_restores_files(tmp_path, monkeypatch):
    service = service_with_one_account(tmp_path)
    before = service.local_values_path.read_bytes()

    def fail_chmod(path, mode):
        raise OSError("synthetic permission failure containing secret-one")

    monkeypatch.setattr("virgilio_connector.gui_config.os.chmod", fail_chmod)
    with pytest.raises(MultiAccountConfigError) as error:
        service.save(service.load())

    assert "secret-one" not in str(error.value)
    assert service.local_values_path.read_bytes() == before


def test_deterministic_env_names_reject_normalization_collisions(tmp_path):
    service = service_with_one_account(tmp_path)
    model = service.load()
    first = service.new_account(
        account_alias="legal-mail", email="one@example.invalid", provider_hint="generic_imap",
        imap_host="imap.example.invalid", imap_port=993, input_folder="INBOX",
        done_folder="done", error_folder="error",
    )
    second = service.new_account(
        account_alias="legal_mail", email="two@example.invalid", provider_hint="generic_imap",
        imap_host="imap.example.invalid", imap_port=993, input_folder="INBOX",
        done_folder="done", error_folder="error",
    )
    with pytest.raises(MultiAccountConfigError, match="environment variable names"):
        model.create_account(first).create_account(second)
