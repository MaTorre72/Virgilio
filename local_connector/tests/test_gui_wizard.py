from pathlib import Path

import pytest

from virgilio_connector.gui_config import GuiConfigService
from virgilio_connector.gui_wizard import FirstRunWizard, WizardAccount
from virgilio_connector.multi_account import MultiAccountConfigError


def wizard(tmp_path: Path, *, verifier=None) -> FirstRunWizard:
    return FirstRunWizard(
        GuiConfigService(tmp_path / "accounts.local.yaml", tmp_path / ".env.local"),
        verifier=verifier,
    )


def test_wizard_forward_back_and_incomplete_configuration(tmp_path):
    item = wizard(tmp_path)
    assert item.first_run and item.step == "Cartelle"
    with pytest.raises(MultiAccountConfigError, match="Limbo"):
        item.next()
    item.set_folders(tmp_path / "limbo")
    assert item.next() == "Caselle"
    assert item.back() == "Cartelle"


def test_wizard_saves_two_synthetic_accounts_without_network(tmp_path):
    calls = []
    item = wizard(tmp_path, verifier=lambda draft: calls.append(draft) or ())
    item.set_folders(tmp_path / "limbo")
    item.set_accounts((
        WizardAccount("account_1", "one@example.invalid", "user-one", "secret-one"),
        WizardAccount("account_2", "two@example.invalid", "user-two", "secret-two",
                      provider="generic_imap", imap_host="imap.example.invalid",
                      input_folder="INBOX", done_folder="done", error_folder="error"),
    ))
    item.set_bucoliche(True)
    item.save()
    loaded = item.service.load()
    assert [account.account_alias for account in loaded.accounts] == ["account_1", "account_2"]
    assert loaded.credentials["account_2"].password == "secret-two"
    yaml_text = item.service.yaml_path.read_text(encoding="utf-8")
    assert "secret-one" not in yaml_text and "secret-two" not in yaml_text
    assert "bucoliche:" in yaml_text and calls


def test_wizard_reports_fake_provider_problem_without_saving(tmp_path):
    item = wizard(tmp_path, verifier=lambda draft: ("Registro condiviso non verificabile.",))
    item.set_folders(tmp_path / "limbo")
    item.set_accounts((WizardAccount("account_1", "one@example.invalid"),))
    assert item.problems() == ("Registro condiviso non verificabile.",)
    with pytest.raises(MultiAccountConfigError, match="Registro condiviso"):
        item.save()
    assert not item.service.yaml_path.exists()


def test_wizard_reopens_saved_configuration(tmp_path):
    item = wizard(tmp_path)
    item.set_folders(tmp_path / "limbo")
    item.set_accounts((WizardAccount("account_1", "one@example.invalid"),))
    item.set_bucoliche(True)
    item.save()
    reopened = FirstRunWizard(item.service)
    assert not reopened.first_run
    assert reopened.draft.staging_dir == tmp_path / "limbo"
    assert reopened.draft.accounts[0].email == "one@example.invalid"
    assert reopened.draft.bucoliche_enabled is True
