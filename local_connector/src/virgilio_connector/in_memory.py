"""Deterministic in-memory adapters for offline tests and demonstrations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .models import AcceptedAttachment, BucolicheRow, CaronteCommand, CaronteResponse, LimboDriveFile
from .ports import AttachmentReference, MessageReference, ScanOutcome


@dataclass
class InMemoryMailbox:
    messages: tuple[MessageReference, ...]
    attachments: dict[str, tuple[AttachmentReference, ...]]
    acknowledged: list[str] = field(default_factory=list)

    def list_pending(self):
        return tuple(x for x in self.messages if x.message_uid not in self.acknowledged)

    def download_attachments(self, message):
        return self.attachments.get(message.message_uid, ())

    def acknowledge(self, message):
        self.acknowledged.append(message.message_uid)


@dataclass(frozen=True)
class InMemoryAntivirus:
    infected_paths: frozenset[Path] = frozenset()

    def scan(self, path: Path) -> ScanOutcome:
        clean = path not in self.infected_paths
        return ScanOutcome("in-memory", "clean" if clean else "infected", clean)


@dataclass
class InMemoryCaronte:
    submitted: list[CaronteCommand] = field(default_factory=list)

    def submit(self, command: CaronteCommand) -> CaronteResponse:
        self.submitted.append(command)
        accepted = tuple(AcceptedAttachment(x.local_temp_id, x.sha256) for x in command.attachments)
        return CaronteResponse(
            schema_version=command.schema_version, command_id=command.command_id, ok=True,
            accepted_attachments=accepted, rejected_attachments=(),
            limbo_drive_ids=tuple(LimboDriveFile(x.local_temp_id, f"drive-{x.local_temp_id}") for x in command.attachments),
            bucoliche_rows=tuple(BucolicheRow(x.local_temp_id, f"row-{x.local_temp_id}") for x in command.attachments),
            message="in-memory success", errors=())
