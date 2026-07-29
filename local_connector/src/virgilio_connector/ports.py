"""Abstract ports only; no concrete IMAP, antivirus, or HTTP adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from .models import CaronteCommand, CaronteResponse


@dataclass(frozen=True, slots=True)
class MessageReference:
    mailbox: str
    uidvalidity: str | None
    message_uid: str
    message_id: str
    subject: str = ""
    sender: str = "unknown@example.invalid"
    date: str = "1970-01-01T00:00:00+00:00"
    thread_id: str | None = None


@dataclass(frozen=True, slots=True)
class AttachmentReference:
    local_temp_id: str
    original_filename: str
    local_path: Path


@dataclass(frozen=True, slots=True)
class ScanOutcome:
    engine: str
    result: str
    clean: bool


class MailboxPort(Protocol):
    """Future mailbox adapter boundary; implementations are intentionally absent."""

    def list_pending(self) -> Sequence[MessageReference]: ...

    def download_attachments(
        self, message: MessageReference
    ) -> Sequence[AttachmentReference]: ...

    def acknowledge(self, message: MessageReference) -> None: ...


class AntivirusPort(Protocol):
    """Future local scanner boundary."""

    def scan(self, path: Path) -> ScanOutcome: ...


class CarontePort(Protocol):
    """Future transport boundary toward Caronte."""

    def submit(self, command: CaronteCommand) -> CaronteResponse: ...
