from pathlib import Path
import sqlite3

import pytest

from virgilio_connector.multi_account import (
    LocalImapAccount,
    MultiAccountConfigError,
    MultiAccountReadonlyScanner,
    load_multi_account_config,
)
from virgilio_connector.local_paths import LocalDataPaths
from virgilio_connector.ports import MessageReference


def write_config(tmp_path: Path) -> Path:
    path = tmp_path / "accounts.yaml"
    path.write_text("""accounts:
  - account_alias: marco_sigmapiu
    email: marco@example.invalid
    provider_hint: gmail_workspace
    imap_host: imap.gmail.com
    imap_port: 993
    username_env: VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME
    password_env: VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD
    input_folder: Virgilio/da-traghettare
    done_folder: Virgilio/traghettate
    error_folder: Virgilio/errore
    enabled: true
    max_messages: 7
  - account_alias: disabled_box
    email: disabled@example.invalid
    provider_hint: generic_imap
    imap_host: imap.example.invalid
    imap_port: 993
    username_env: VIRGILIO_IMAP_DISABLED_USERNAME
    password_env: VIRGILIO_IMAP_DISABLED_PASSWORD
    input_folder: INBOX
    done_folder: done
    error_folder: error
    enabled: false
""", encoding="utf-8")
    return path


class FakeMailbox:
    instances = []

    def __init__(self, config, root):
        self.config = config
        self.root = root
        self.calls = []
        self.__class__.instances.append(self)

    def list_pending(self):
        self.calls.append("list_pending")
        return (
            MessageReference(self.config.mailbox, "123", "41", "<a@example.invalid>",
                             "Subject A", "sender@example.invalid",
                             "2026-06-25T10:00:00+00:00"),
            MessageReference(self.config.mailbox, "123", "42", "<b@example.invalid>",
                             "Subject B", "sender@example.invalid",
                             "2026-06-25T10:01:00+00:00"),
        )

    def detect_attachments(self, message):
        raise AssertionError("multi-account scan must not download or inspect attachments")

    def download_attachments(self, message):
        raise AssertionError("multi-account scan must not download attachments")

    def acknowledge(self, message):
        raise AssertionError("multi-account scan must not acknowledge messages")


def test_loads_multi_account_yaml_without_secret_values(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))
    assert [account.account_alias for account in accounts] == ["marco_sigmapiu", "disabled_box"]
    assert accounts[0].email == "marco@example.invalid"
    assert accounts[0].max_messages == 7
    assert accounts[0].password_env == "VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD"


def test_rejects_duplicate_alias(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("""accounts:
  - account_alias: same_alias
    email: a@example.invalid
    provider_hint: generic
    imap_host: imap.example.invalid
    imap_port: 993
    username_env: VIRGILIO_A_USERNAME
    password_env: VIRGILIO_A_PASSWORD
    input_folder: INBOX
    done_folder: done
    error_folder: error
  - account_alias: same_alias
    email: b@example.invalid
    provider_hint: generic
    imap_host: imap.example.invalid
    imap_port: 993
    username_env: VIRGILIO_B_USERNAME
    password_env: VIRGILIO_B_PASSWORD
    input_folder: INBOX
    done_folder: done
    error_folder: error
""", encoding="utf-8")
    with pytest.raises(MultiAccountConfigError, match="unique"):
        load_multi_account_config(path)


def test_missing_env_vars_fail_closed_without_network(tmp_path):
    account = LocalImapAccount(
        account_alias="marco_sigmapiu",
        email="marco@example.invalid",
        provider_hint="gmail_workspace",
        imap_host="imap.gmail.com",
        imap_port=993,
        username_env="VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME",
        password_env="VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD",
        input_folder="Virgilio/da-traghettare",
        done_folder="Virgilio/traghettate",
        error_folder="Virgilio/errore",
    )
    calls = []
    result = MultiAccountReadonlyScanner(
        [account],
        paths=LocalDataPaths(tmp_path / ".local_data"),
        environ={},
        mailbox_factory=lambda *_: calls.append("network"),
    ).scan(dry_run=True)
    assert result[0].status == "error"
    assert "VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME" in result[0].error
    assert calls == []


def test_dry_run_scans_enabled_accounts_without_writing_state(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))
    paths = LocalDataPaths(tmp_path / ".local_data")
    result = MultiAccountReadonlyScanner(
        accounts,
        paths=paths,
        environ={
            "VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME": "user@example.invalid",
            "VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD": "secret",
        },
        mailbox_factory=lambda config, root: FakeMailbox(config, root),
    ).scan(dry_run=True)
    assert [(item.account_alias, item.status, item.messages_seen) for item in result] == [
        ("marco_sigmapiu", "ok", 2),
        ("disabled_box", "disabled", 0),
    ]
    assert not paths.root.exists()
    assert len(FakeMailbox.instances) == 1
    assert FakeMailbox.instances[0].config.password == "secret"


def test_non_dry_run_records_account_alias_separately(tmp_path):
    accounts = load_multi_account_config(write_config(tmp_path))[:1]
    paths = LocalDataPaths(tmp_path / ".local_data")
    result = MultiAccountReadonlyScanner(
        accounts,
        paths=paths,
        environ={
            "VIRGILIO_IMAP_MARCO_SIGMAPIU_USERNAME": "user@example.invalid",
            "VIRGILIO_IMAP_MARCO_SIGMAPIU_PASSWORD": "secret",
        },
        mailbox_factory=lambda config, root: FakeMailbox(config, root),
    ).scan(dry_run=False)
    assert result[0].status == "ok"
    with sqlite3.connect(paths.state_db) as db:
        runs = db.execute("SELECT account_alias,messages_seen,attachments_seen,status FROM runs").fetchall()
        messages = db.execute("SELECT account_alias,message_uid,mailbox FROM messages ORDER BY message_uid").fetchall()
        attachments = db.execute("SELECT COUNT(*) FROM attachments").fetchone()[0]
    assert runs == [("marco_sigmapiu", 2, 0, "completed")]
    assert messages == [
        ("marco_sigmapiu", "41", "Virgilio/da-traghettare"),
        ("marco_sigmapiu", "42", "Virgilio/da-traghettare"),
    ]
    assert attachments == 0
