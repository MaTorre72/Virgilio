"""Persistent state models for the local connector."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath

from .models import QuarantineStatus


class MessageStatus(StrEnum):
    DISCOVERED = "discovered"
    QUARANTINED = "quarantined"
    READY = "ready"
    SUBMITTING = "submitting"
    ACK_PENDING = "ack_pending"
    ACKNOWLEDGED = "acknowledged"
    REJECTED = "rejected"
    ERROR = "error"


class CommandAttemptStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


_MESSAGE_TRANSITIONS: dict[MessageStatus, frozenset[MessageStatus]] = {
    MessageStatus.DISCOVERED: frozenset(
        {MessageStatus.QUARANTINED, MessageStatus.REJECTED, MessageStatus.ERROR}
    ),
    MessageStatus.QUARANTINED: frozenset(
        {MessageStatus.READY, MessageStatus.REJECTED, MessageStatus.ERROR}
    ),
    MessageStatus.READY: frozenset(
        {MessageStatus.SUBMITTING, MessageStatus.REJECTED, MessageStatus.ERROR}
    ),
    MessageStatus.SUBMITTING: frozenset(
        {MessageStatus.ACK_PENDING, MessageStatus.READY, MessageStatus.ERROR}
    ),
    MessageStatus.ACK_PENDING: frozenset(
        {MessageStatus.ACKNOWLEDGED, MessageStatus.ERROR}
    ),
    MessageStatus.ERROR: frozenset({MessageStatus.DISCOVERED}),
    MessageStatus.ACKNOWLEDGED: frozenset(),
    MessageStatus.REJECTED: frozenset(),
}


class InvalidMessageTransition(ValueError):
    """Raised when a persisted message transition is not allowed."""


def can_transition_message(source: MessageStatus, target: MessageStatus) -> bool:
    return target in _MESSAGE_TRANSITIONS[source]


def require_message_transition(source: MessageStatus, target: MessageStatus) -> None:
    if not can_transition_message(source, target):
        raise InvalidMessageTransition(f"cannot transition {source} -> {target}")


@dataclass(frozen=True, slots=True)
class NewMessage:
    account_alias: str
    mailbox: str
    mailbox_uidvalidity: str
    message_uid: str
    message_id: str
    thread_id: str | None
    subject: str
    sender: str
    message_date: str

    def __post_init__(self) -> None:
        for field in (
            "account_alias",
            "mailbox",
            "mailbox_uidvalidity",
            "message_uid",
            "sender",
            "message_date",
        ):
            if not getattr(self, field).strip():
                raise ValueError(f"{field} must not be empty")


@dataclass(frozen=True, slots=True)
class MessageRecord:
    id: int
    account_alias: str
    mailbox: str
    mailbox_uidvalidity: str
    message_uid: str
    message_id: str
    thread_id: str | None
    subject: str
    sender: str
    message_date: str
    status: MessageStatus
    command_id: str | None
    acknowledged_at: str | None
    last_error: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class NewAttachment:
    message_row_id: int
    local_temp_id: str
    local_relative_path: str
    original_filename: str
    sanitized_filename: str
    mime_type: str
    size_bytes: int
    sha256: str

    def __post_init__(self) -> None:
        if self.message_row_id <= 0:
            raise ValueError("message_row_id must be positive")
        for field in (
            "local_temp_id",
            "local_relative_path",
            "original_filename",
            "sanitized_filename",
            "mime_type",
            "sha256",
        ):
            if not str(getattr(self, field)).strip():
                raise ValueError(f"{field} must not be empty")
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")

        relative_path = self.local_relative_path
        path_parts = relative_path.replace("\\", "/").split("/")
        if (
            PurePosixPath(relative_path).is_absolute()
            or PureWindowsPath(relative_path).is_absolute()
            or ".." in path_parts
        ):
            raise ValueError("local_relative_path must stay inside quarantine root")


@dataclass(frozen=True, slots=True)
class AttachmentRecord:
    id: int
    message_row_id: int
    local_temp_id: str
    local_relative_path: str
    original_filename: str
    sanitized_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    quarantine_status: QuarantineStatus
    status_reason: str
    scan_engine: str
    scan_result: str
    drive_file_id: str | None
    bucoliche_row_reference: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class CommandAttemptRecord:
    id: int
    message_row_id: int
    command_id: str
    attempt_number: int
    dry_run: bool
    status: CommandAttemptStatus
    request_sha256: str
    response_ok: bool | None
    response_message: str | None
    error_code: str | None
    retryable: bool | None
    created_at: str
    completed_at: str | None


@dataclass(frozen=True, slots=True)
class StateEvent:
    id: int
    entity_type: str
    entity_id: int
    previous_state: str | None
    new_state: str
    reason: str
    created_at: str
