"""Read-only mailbox connection check shared by Caronte presentations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..imap_readonly import ImapReadonlyConfig, ImapReadonlyMailbox


@dataclass(frozen=True, slots=True)
class AccountConnectionRequest:
    email: str
    password: str = field(repr=False)
    host: str = "imap.gmail.com"
    port: int = 993


class ReadonlyAccountConnectionService:
    """Check mailbox access without exposing mutating operations."""

    def __init__(
        self,
        local_root: Path,
        *,
        mailbox_factory: Callable[..., ImapReadonlyMailbox] = ImapReadonlyMailbox,
    ) -> None:
        self._local_root = Path(local_root)
        self._mailbox_factory = mailbox_factory

    def check(self, request: AccountConnectionRequest) -> str:
        mailbox = self._mailbox_factory(
            ImapReadonlyConfig(
                host=request.host,
                port=request.port,
                username=request.email,
                password=request.password,
            ),
            self._local_root,
        )
        count = len(mailbox.list_pending())
        return f"Collegamento riuscito: {count} messaggi visibili."
