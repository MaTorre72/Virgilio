"""Shared multi-account management use cases for Caronte presentations."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import re

from ..multi_account import LocalImapAccount, LocalStorageConfig, MultiAccountConfigError
from .configuration import ConfigurationModel, ConfigurationService
from .credentials import AccountCredentialService, AccountCredentials


@dataclass(frozen=True, slots=True)
class ManagedAccount:
    alias: str
    name: str
    email: str
    host: str
    port: int
    enabled: bool


class AccountManagementService:
    """Persist independent account structure and credentials through shared ports."""

    def __init__(
        self,
        configuration: ConfigurationService,
        credentials: AccountCredentialService,
    ) -> None:
        self.configuration = configuration
        self.credentials = credentials

    def list_accounts(self) -> tuple[ManagedAccount, ...]:
        if not self.configuration.exists():
            return ()
        return tuple(_managed(account) for account in self.configuration.load().accounts)

    def add(
        self,
        *,
        name: str,
        email: str,
        password: str,
        host: str,
        port: int,
        enabled: bool,
        limbo: Path,
    ) -> ManagedAccount:
        current = self.configuration.load() if self.configuration.exists() else None
        aliases = {account.account_alias for account in current.accounts} if current else set()
        alias = _unique_alias(name, aliases)
        account = _account(alias, email, host, port, enabled)
        model = (
            replace(current, accounts=(*current.accounts, account))
            if current
            else ConfigurationModel(
                accounts=(account,),
                storage=LocalStorageConfig(
                    adapter="local_filesystem",
                    staging_dir=Path(limbo),
                ),
            )
        )
        self.credentials.save(account, AccountCredentials(email, password))
        try:
            self.configuration.save(model)
        except Exception:
            self.credentials.delete(account)
            raise
        return _managed(account)

    def update(
        self,
        alias: str,
        *,
        email: str,
        password: str,
        host: str,
        port: int,
        enabled: bool,
    ) -> ManagedAccount:
        model = self.configuration.load()
        previous = _find(model, alias)
        updated = replace(
            previous,
            email=email,
            provider_hint=_provider_hint(host),
            imap_host=host,
            imap_port=port,
            enabled=enabled,
        )
        old_credentials = self.credentials.read(previous)
        self.credentials.update(updated, AccountCredentials(email, password))
        try:
            self.configuration.save(
                replace(
                    model,
                    accounts=tuple(updated if item.account_alias == alias else item for item in model.accounts),
                )
            )
        except Exception:
            self.credentials.update(previous, old_credentials)
            raise
        return _managed(updated)

    def remove(self, alias: str) -> None:
        model = self.configuration.load()
        account = _find(model, alias)
        remaining = tuple(item for item in model.accounts if item.account_alias != alias)
        if not remaining:
            raise MultiAccountConfigError("at least one mailbox must remain")
        credentials = self.credentials.read(account)
        self.configuration.save(replace(model, accounts=remaining))
        try:
            self.credentials.delete(account)
        except Exception:
            self.configuration.save(model)
            self.credentials.update(account, credentials)
            raise


def _managed(account: LocalImapAccount) -> ManagedAccount:
    return ManagedAccount(
        alias=account.account_alias,
        name=account.account_alias.replace("_", " ").title(),
        email=account.email,
        host=account.imap_host,
        port=account.imap_port,
        enabled=account.enabled,
    )


def _account(alias: str, email: str, host: str, port: int, enabled: bool) -> LocalImapAccount:
    prefix = re.sub(r"[^A-Z0-9]", "_", alias.upper())
    return LocalImapAccount(
        account_alias=alias,
        email=email,
        provider_hint=_provider_hint(host),
        imap_host=host,
        imap_port=port,
        username_env=f"VIRGILIO_{prefix}_USERNAME",
        password_env=f"VIRGILIO_{prefix}_PASSWORD",
        input_folder="Virgilio_Inbox",
        done_folder="Virgilio_Done",
        error_folder="Virgilio_Errori",
        enabled=enabled,
    )


def _unique_alias(name: str, existing: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_") or "casella"
    alias = base
    suffix = 2
    while alias in existing:
        alias = f"{base}_{suffix}"
        suffix += 1
    return alias


def _provider_hint(host: str) -> str:
    return "gmail_workspace" if host.strip().lower() == "imap.gmail.com" else "custom_imap"


def _find(model: ConfigurationModel, alias: str) -> LocalImapAccount:
    for account in model.accounts:
        if account.account_alias == alias:
            return account
    raise MultiAccountConfigError("mailbox not found")
