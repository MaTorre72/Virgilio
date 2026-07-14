from dataclasses import replace

import pytest

from virgilio_connector.gui_accounts import AccountDraft, AccountManager
from virgilio_connector.gui_config import GuiConfigService
from virgilio_connector.multi_account import MultiAccountConfigError, scaffold_local_config


def manager(tmp_path, *, tester=None):
    yaml = tmp_path / "accounts.local.yaml"
    yaml.write_text(scaffold_local_config(email="one@example.invalid", staging_dir=tmp_path / "limbo",
                                          account_alias="account_1"), encoding="utf-8")
    (tmp_path / ".env.local").write_text(
        "VIRGILIO_IMAP_ACCOUNT_1_USERNAME=user-one\n"
        "VIRGILIO_IMAP_ACCOUNT_1_PASSWORD=secret-one\n", encoding="utf-8")
    return AccountManager(GuiConfigService(yaml, tmp_path / ".env.local"), tester=tester)


def test_complete_crud_for_two_distinct_accounts(tmp_path):
    item = manager(tmp_path)
    item.save(AccountDraft("account_2", "two@example.invalid", "user-two", "secret-two",
                           "generic_imap", "imap.example.invalid", 1993, "INBOX", "done", "error"))
    assert [account.account_alias for account in item.list_accounts()] == ["account_1", "account_2"]
    item.set_enabled("account_2", False)
    edited = replace(item.get("account_2"), alias="archive", imap_host="mail.example.invalid")
    item.save(edited, previous_alias="account_2")
    assert item.get("archive").enabled is False
    assert item.get("archive").password == "secret-two"
    item.remove("archive")
    assert [account.account_alias for account in item.list_accounts()] == ["account_1"]


def test_duplicate_alias_is_rejected(tmp_path):
    item = manager(tmp_path)
    with pytest.raises(MultiAccountConfigError, match="unique"):
        item.save(AccountDraft("account_1", "duplicate@example.invalid"))


def test_separate_readonly_test_uses_selected_account_and_fake_provider(tmp_path):
    calls = []
    item = manager(tmp_path, tester=lambda account, credentials, root:
                   calls.append((account, credentials, root)) or 3)
    item.save(AccountDraft("account_2", "two@example.invalid", "user-two", "secret-two",
                           "generic_imap", "imap.example.invalid"))
    result = item.test_connection("account_2")
    assert result.pending_messages == 3 and result.alias == "account_2"
    assert calls[0][0].imap_host == "imap.example.invalid"
    assert calls[0][1].password == "secret-two"


def test_default_connection_test_is_readonly(monkeypatch, tmp_path):
    seen = {}
    class FakeMailbox:
        def __init__(self, config, root): seen.update(config=config, root=root)
        def list_pending(self): return (object(), object())
    monkeypatch.setattr("virgilio_connector.gui_accounts.ImapReadonlyMailbox", FakeMailbox)
    result = manager(tmp_path).test_connection("account_1")
    assert result.pending_messages == 2
    assert seen["config"].mailbox == "Virgilio/da-traghettare"
