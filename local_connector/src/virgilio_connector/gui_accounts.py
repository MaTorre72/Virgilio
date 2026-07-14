"""Account lifecycle services shared by the local GUI."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from .gui_config import GuiConfigService, LocalCredentials
from .imap_readonly import ImapReadonlyConfig, ImapReadonlyMailbox
from .multi_account import LocalImapAccount, MultiAccountConfigError


@dataclass(frozen=True, slots=True)
class AccountDraft:
    alias: str
    email: str
    username: str = ""
    password: str = ""
    provider: str = "gmail_workspace"
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    input_folder: str = "Virgilio/da-traghettare"
    done_folder: str = "Virgilio/traghettate"
    error_folder: str = "Virgilio/errore"
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class ConnectionTestResult:
    alias: str
    pending_messages: int
    message: str


ReadonlyTester = Callable[[LocalImapAccount, LocalCredentials, Path], int]


class AccountManager:
    """Persists account changes and performs a separate read-only connection test."""

    def __init__(self, service: GuiConfigService, *, tester: ReadonlyTester | None = None) -> None:
        self.service = service
        self.tester = tester or _test_readonly

    def list_accounts(self) -> tuple[LocalImapAccount, ...]:
        return self.service.load().accounts

    def get(self, alias: str) -> AccountDraft:
        model = self.service.load()
        account = next((item for item in model.accounts if item.account_alias == alias), None)
        if account is None:
            raise MultiAccountConfigError(f"Casella non trovata: {alias}")
        credentials = model.credentials[alias]
        return AccountDraft(
            alias=alias, email=account.email, username=credentials.username,
            password=credentials.password, provider=account.provider_hint,
            imap_host=account.imap_host, imap_port=account.imap_port,
            input_folder=account.input_folder, done_folder=account.done_folder,
            error_folder=account.error_folder, enabled=account.enabled,
        )

    def save(self, draft: AccountDraft, *, previous_alias: str | None = None) -> None:
        alias = draft.alias.strip()
        if not alias or not draft.email.strip():
            raise MultiAccountConfigError("Nome casella ed email sono obbligatori.")
        account = self.service.new_account(
            account_alias=alias, email=draft.email.strip(), provider_hint=draft.provider,
            imap_host=draft.imap_host.strip(), imap_port=draft.imap_port,
            input_folder=draft.input_folder.strip(), done_folder=draft.done_folder.strip(),
            error_folder=draft.error_folder.strip(), enabled=draft.enabled,
        )
        credentials = LocalCredentials(draft.username, draft.password)
        model = self.service.load()
        if previous_alias is None:
            model = model.create_account(account, credentials)
        else:
            model = model.update_account(previous_alias, account, credentials)
        self.service.save(model)

    def set_enabled(self, alias: str, enabled: bool) -> None:
        model = self.service.load()
        account = next((item for item in model.accounts if item.account_alias == alias), None)
        if account is None:
            raise MultiAccountConfigError(f"Casella non trovata: {alias}")
        self.service.save(model.update_account(alias, replace(account, enabled=enabled)))

    def remove(self, alias: str) -> None:
        self.service.save(self.service.load().remove_account(alias))

    def test_connection(self, alias: str) -> ConnectionTestResult:
        model = self.service.load()
        account = next((item for item in model.accounts if item.account_alias == alias), None)
        if account is None:
            raise MultiAccountConfigError(f"Casella non trovata: {alias}")
        count = self.tester(account, model.credentials[alias], model.storage.staging_dir)
        return ConnectionTestResult(alias, count, f"Collegamento read-only riuscito: {count} messaggi visibili.")


def _test_readonly(account: LocalImapAccount, credentials: LocalCredentials,
                   quarantine_root: Path) -> int:
    mailbox = ImapReadonlyMailbox(ImapReadonlyConfig(
        host=account.imap_host, port=account.imap_port, username=credentials.username,
        password=credentials.password, mailbox=account.input_folder,
        max_messages=account.max_messages,
    ), quarantine_root)
    return len(mailbox.list_pending())
