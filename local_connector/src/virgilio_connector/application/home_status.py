"""Presentation-independent status exposed to Caronte home views."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .account_management import AccountManagementService


@dataclass(frozen=True, slots=True)
class HomeStatus:
    state: str
    active_accounts: int
    last_check: datetime | None = None


class HomeStatusService(Protocol):
    """Read the operational summary without depending on a GUI toolkit."""

    def get_status(self) -> HomeStatus: ...


class AccountHomeStatusService:
    """Build the initial summary from shared account configuration."""

    def __init__(self, accounts: AccountManagementService) -> None:
        self._accounts = accounts

    def get_status(self) -> HomeStatus:
        active_accounts = sum(account.enabled for account in self._accounts.list_accounts())
        return HomeStatus(
            state="Pronto" if active_accounts else "Nessuna casella attiva",
            active_accounts=active_accounts,
        )
