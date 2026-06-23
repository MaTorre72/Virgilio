"""SQLite persistence for local connector state.

The store owns technical state only. It never stores attachment bytes,
credentials, authentication tokens, or full request/response payloads.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Iterator

from .models import QuarantineStatus, require_sha256
from .quarantine import InvalidTransition, can_transition
from .state_models import (
    AttachmentRecord,
    CommandAttemptRecord,
    CommandAttemptStatus,
    InvalidMessageTransition,
    MessageRecord,
    MessageStatus,
    NewAttachment,
    NewMessage,
    StateEvent,
    require_message_transition,
)


DATABASE_SCHEMA_VERSION = 1


class StateDatabaseError(RuntimeError):
    """Base error for local state persistence."""


class StateNotFoundError(StateDatabaseError):
    """Raised when a requested persistent entity does not exist."""


class StateConflictError(StateDatabaseError):
    """Raised when an idempotency key conflicts with different data."""


class UnsupportedSchemaError(StateDatabaseError):
    """Raised when state.db was created by a newer schema."""


_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE messages (
        id INTEGER PRIMARY KEY,
        account_alias TEXT NOT NULL,
        mailbox TEXT NOT NULL,
        mailbox_uidvalidity TEXT NOT NULL,
        message_uid TEXT NOT NULL,
        message_id TEXT NOT NULL,
        thread_id TEXT,
        subject TEXT NOT NULL,
        sender TEXT NOT NULL,
        message_date TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN (
            'discovered', 'quarantined', 'ready', 'submitting',
            'ack_pending', 'acknowledged', 'rejected', 'error'
        )),
        command_id TEXT,
        acknowledged_at TEXT,
        last_error TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (account_alias, mailbox, mailbox_uidvalidity, message_uid)
    )
    """,
    """
    CREATE TABLE attachments (
        id INTEGER PRIMARY KEY,
        message_row_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE RESTRICT,
        local_temp_id TEXT NOT NULL UNIQUE,
        local_relative_path TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        sanitized_filename TEXT NOT NULL,
        mime_type TEXT NOT NULL,
        size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
        sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
        quarantine_status TEXT NOT NULL CHECK (quarantine_status IN (
            'downloaded', 'quarantined', 'rejected', 'scan_failed',
            'ready_for_caronte', 'uploaded_to_limbo'
        )),
        status_reason TEXT NOT NULL,
        scan_engine TEXT NOT NULL DEFAULT 'none',
        scan_result TEXT NOT NULL DEFAULT 'not_scanned',
        drive_file_id TEXT,
        bucoliche_row_reference TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE command_attempts (
        id INTEGER PRIMARY KEY,
        message_row_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE RESTRICT,
        command_id TEXT NOT NULL,
        attempt_number INTEGER NOT NULL CHECK (attempt_number > 0),
        dry_run INTEGER NOT NULL CHECK (dry_run IN (0, 1)),
        status TEXT NOT NULL CHECK (status IN ('pending', 'succeeded', 'failed')),
        request_sha256 TEXT NOT NULL CHECK (length(request_sha256) = 64),
        response_ok INTEGER CHECK (response_ok IN (0, 1)),
        response_message TEXT,
        error_code TEXT,
        retryable INTEGER CHECK (retryable IN (0, 1)),
        created_at TEXT NOT NULL,
        completed_at TEXT,
        UNIQUE (command_id, attempt_number)
    )
    """,
    """
    CREATE TABLE state_events (
        id INTEGER PRIMARY KEY,
        entity_type TEXT NOT NULL CHECK (entity_type IN ('message', 'attachment')),
        entity_id INTEGER NOT NULL,
        previous_state TEXT,
        new_state TEXT NOT NULL,
        reason TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX idx_messages_status ON messages(status, updated_at)",
    "CREATE INDEX idx_attachments_message ON attachments(message_row_id, id)",
    "CREATE INDEX idx_attachments_status ON attachments(quarantine_status, updated_at)",
    "CREATE INDEX idx_attempts_message ON command_attempts(message_row_id, created_at)",
    "CREATE INDEX idx_events_entity ON state_events(entity_type, entity_id, id)",
)


class StateStore:
    """Small transactional repository around one local SQLite database."""

    def __init__(self, path: str | Path, *, timeout_seconds: float = 5.0) -> None:
        self.path = Path(path)
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._transaction(write=True) as connection:
            current = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if current > DATABASE_SCHEMA_VERSION:
                raise UnsupportedSchemaError(
                    f"state.db schema {current} is newer than supported version "
                    f"{DATABASE_SCHEMA_VERSION}"
                )
            if current == 0:
                for statement in _SCHEMA_STATEMENTS:
                    connection.execute(statement)
                connection.execute(f"PRAGMA user_version = {DATABASE_SCHEMA_VERSION}")

    def schema_version(self) -> int:
        with self._transaction() as connection:
            return int(connection.execute("PRAGMA user_version").fetchone()[0])

    def integrity_check(self) -> bool:
        with self._transaction() as connection:
            result = connection.execute("PRAGMA quick_check").fetchone()[0]
            return result == "ok"

    def register_message(self, message: NewMessage) -> MessageRecord:
        now = _utc_now()
        identity = (
            message.account_alias,
            message.mailbox,
            message.mailbox_uidvalidity,
            message.message_uid,
        )
        with self._transaction(write=True) as connection:
            existing = connection.execute(
                """
                SELECT * FROM messages
                WHERE account_alias = ? AND mailbox = ?
                  AND mailbox_uidvalidity = ? AND message_uid = ?
                """,
                identity,
            ).fetchone()
            if existing is not None:
                connection.execute(
                    """
                    UPDATE messages
                    SET message_id = ?, thread_id = ?, subject = ?, sender = ?,
                        message_date = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        message.message_id,
                        message.thread_id,
                        message.subject,
                        message.sender,
                        message.message_date,
                        now,
                        existing["id"],
                    ),
                )
                return self._get_message_in(connection, int(existing["id"]))

            cursor = connection.execute(
                """
                INSERT INTO messages (
                    account_alias, mailbox, mailbox_uidvalidity, message_uid,
                    message_id, thread_id, subject, sender, message_date,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (*identity, message.message_id, message.thread_id, message.subject,
                 message.sender, message.message_date, MessageStatus.DISCOVERED.value,
                 now, now),
            )
            message_row_id = int(cursor.lastrowid)
            self._add_event(
                connection,
                entity_type="message",
                entity_id=message_row_id,
                previous_state=None,
                new_state=MessageStatus.DISCOVERED.value,
                reason="message registered",
                created_at=now,
            )
            return self._get_message_in(connection, message_row_id)

    def get_message(self, message_row_id: int) -> MessageRecord:
        with self._transaction() as connection:
            return self._get_message_in(connection, message_row_id)

    def transition_message(
        self,
        message_row_id: int,
        target: MessageStatus,
        *,
        reason: str,
        command_id: str | None = None,
        last_error: str | None = None,
    ) -> MessageRecord:
        if not reason.strip():
            raise ValueError("transition reason must not be empty")
        with self._transaction(write=True) as connection:
            current = self._get_message_in(connection, message_row_id)
            require_message_transition(current.status, target)
            if target is MessageStatus.ACK_PENDING and not (command_id or current.command_id):
                raise StateConflictError("ack_pending requires a command_id")
            if target is MessageStatus.ACKNOWLEDGED:
                uploaded = connection.execute(
                    """
                    SELECT COUNT(*) FROM attachments
                    WHERE message_row_id = ? AND quarantine_status = ?
                      AND drive_file_id IS NOT NULL
                    """,
                    (message_row_id, QuarantineStatus.UPLOADED_TO_LIMBO.value),
                ).fetchone()[0]
                if int(uploaded) < 1:
                    raise StateConflictError(
                        "cannot acknowledge without an attachment confirmed in Limbo Drive"
                    )
            now = _utc_now()
            acknowledged_at = now if target is MessageStatus.ACKNOWLEDGED else current.acknowledged_at
            connection.execute(
                """
                UPDATE messages
                SET status = ?, command_id = ?, acknowledged_at = ?,
                    last_error = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    target.value,
                    command_id if command_id is not None else current.command_id,
                    acknowledged_at,
                    last_error,
                    now,
                    message_row_id,
                ),
            )
            self._add_event(
                connection,
                entity_type="message",
                entity_id=message_row_id,
                previous_state=current.status.value,
                new_state=target.value,
                reason=reason,
                created_at=now,
            )
            return self._get_message_in(connection, message_row_id)

    def add_attachment(self, attachment: NewAttachment) -> AttachmentRecord:
        require_sha256(attachment.sha256)
        now = _utc_now()
        with self._transaction(write=True) as connection:
            self._get_message_in(connection, attachment.message_row_id)
            existing = connection.execute(
                "SELECT * FROM attachments WHERE local_temp_id = ?",
                (attachment.local_temp_id,),
            ).fetchone()
            if existing is not None:
                record = _attachment_from_row(existing)
                if (
                    record.message_row_id == attachment.message_row_id
                    and record.sha256 == attachment.sha256
                    and record.local_relative_path == attachment.local_relative_path
                ):
                    return record
                raise StateConflictError(
                    f"local_temp_id already refers to different data: {attachment.local_temp_id}"
                )
            cursor = connection.execute(
                """
                INSERT INTO attachments (
                    message_row_id, local_temp_id, local_relative_path,
                    original_filename, sanitized_filename, mime_type,
                    size_bytes, sha256, quarantine_status, status_reason,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attachment.message_row_id,
                    attachment.local_temp_id,
                    attachment.local_relative_path,
                    attachment.original_filename,
                    attachment.sanitized_filename,
                    attachment.mime_type,
                    attachment.size_bytes,
                    attachment.sha256,
                    QuarantineStatus.DOWNLOADED.value,
                    "attachment registered after local write",
                    now,
                    now,
                ),
            )
            attachment_id = int(cursor.lastrowid)
            self._add_event(
                connection,
                entity_type="attachment",
                entity_id=attachment_id,
                previous_state=None,
                new_state=QuarantineStatus.DOWNLOADED.value,
                reason="attachment registered after local write",
                created_at=now,
            )
            return self._get_attachment_by_id_in(connection, attachment_id)

    def get_attachment(self, local_temp_id: str) -> AttachmentRecord:
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM attachments WHERE local_temp_id = ?",
                (local_temp_id,),
            ).fetchone()
            if row is None:
                raise StateNotFoundError(f"attachment not found: {local_temp_id}")
            return _attachment_from_row(row)

    def list_attachments(self, message_row_id: int) -> tuple[AttachmentRecord, ...]:
        with self._transaction() as connection:
            self._get_message_in(connection, message_row_id)
            rows = connection.execute(
                "SELECT * FROM attachments WHERE message_row_id = ? ORDER BY id",
                (message_row_id,),
            ).fetchall()
            return tuple(_attachment_from_row(row) for row in rows)

    def transition_attachment(
        self,
        local_temp_id: str,
        target: QuarantineStatus,
        *,
        reason: str,
        scan_engine: str | None = None,
        scan_result: str | None = None,
        drive_file_id: str | None = None,
        bucoliche_row_reference: str | None = None,
    ) -> AttachmentRecord:
        if not reason.strip():
            raise ValueError("transition reason must not be empty")
        with self._transaction(write=True) as connection:
            row = connection.execute(
                "SELECT * FROM attachments WHERE local_temp_id = ?",
                (local_temp_id,),
            ).fetchone()
            if row is None:
                raise StateNotFoundError(f"attachment not found: {local_temp_id}")
            current = _attachment_from_row(row)
            if not can_transition(current.quarantine_status, target):
                raise InvalidTransition(
                    f"cannot transition {current.quarantine_status} -> {target}"
                )
            final_drive_id = drive_file_id or current.drive_file_id
            if target is QuarantineStatus.UPLOADED_TO_LIMBO and not final_drive_id:
                raise StateConflictError("uploaded_to_limbo requires drive_file_id")
            if drive_file_id and target is not QuarantineStatus.UPLOADED_TO_LIMBO:
                raise StateConflictError(
                    "drive_file_id may be set only when transitioning to uploaded_to_limbo"
                )
            now = _utc_now()
            connection.execute(
                """
                UPDATE attachments
                SET quarantine_status = ?, status_reason = ?, scan_engine = ?,
                    scan_result = ?, drive_file_id = ?,
                    bucoliche_row_reference = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    target.value,
                    reason,
                    scan_engine if scan_engine is not None else current.scan_engine,
                    scan_result if scan_result is not None else current.scan_result,
                    final_drive_id,
                    (
                        bucoliche_row_reference
                        if bucoliche_row_reference is not None
                        else current.bucoliche_row_reference
                    ),
                    now,
                    current.id,
                ),
            )
            self._add_event(
                connection,
                entity_type="attachment",
                entity_id=current.id,
                previous_state=current.quarantine_status.value,
                new_state=target.value,
                reason=reason,
                created_at=now,
            )
            return self._get_attachment_by_id_in(connection, current.id)

    def start_command_attempt(
        self,
        message_row_id: int,
        *,
        command_id: str,
        dry_run: bool,
        request_sha256: str,
    ) -> CommandAttemptRecord:
        if not command_id.strip():
            raise ValueError("command_id must not be empty")
        require_sha256(request_sha256, "request_sha256")
        with self._transaction(write=True) as connection:
            self._get_message_in(connection, message_row_id)
            attempt_number = int(
                connection.execute(
                    """
                    SELECT COALESCE(MAX(attempt_number), 0) + 1
                    FROM command_attempts WHERE command_id = ?
                    """,
                    (command_id,),
                ).fetchone()[0]
            )
            now = _utc_now()
            cursor = connection.execute(
                """
                INSERT INTO command_attempts (
                    message_row_id, command_id, attempt_number, dry_run,
                    status, request_sha256, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_row_id,
                    command_id,
                    attempt_number,
                    int(dry_run),
                    CommandAttemptStatus.PENDING.value,
                    request_sha256,
                    now,
                ),
            )
            return self._get_attempt_in(connection, int(cursor.lastrowid))

    def complete_command_attempt(
        self,
        attempt_id: int,
        *,
        succeeded: bool,
        response_ok: bool | None,
        response_message: str | None = None,
        error_code: str | None = None,
        retryable: bool | None = None,
    ) -> CommandAttemptRecord:
        with self._transaction(write=True) as connection:
            current = self._get_attempt_in(connection, attempt_id)
            if current.status is not CommandAttemptStatus.PENDING:
                raise StateConflictError("command attempt is already complete")
            status = (
                CommandAttemptStatus.SUCCEEDED
                if succeeded
                else CommandAttemptStatus.FAILED
            )
            now = _utc_now()
            connection.execute(
                """
                UPDATE command_attempts
                SET status = ?, response_ok = ?, response_message = ?,
                    error_code = ?, retryable = ?, completed_at = ?
                WHERE id = ?
                """,
                (
                    status.value,
                    None if response_ok is None else int(response_ok),
                    response_message,
                    error_code,
                    None if retryable is None else int(retryable),
                    now,
                    attempt_id,
                ),
            )
            return self._get_attempt_in(connection, attempt_id)

    def list_command_attempts(
        self, message_row_id: int
    ) -> tuple[CommandAttemptRecord, ...]:
        with self._transaction() as connection:
            self._get_message_in(connection, message_row_id)
            rows = connection.execute(
                """
                SELECT * FROM command_attempts
                WHERE message_row_id = ? ORDER BY id
                """,
                (message_row_id,),
            ).fetchall()
            return tuple(_attempt_from_row(row) for row in rows)

    def list_events(
        self, entity_type: str, entity_id: int
    ) -> tuple[StateEvent, ...]:
        if entity_type not in {"message", "attachment"}:
            raise ValueError("entity_type must be message or attachment")
        with self._transaction() as connection:
            rows = connection.execute(
                """
                SELECT * FROM state_events
                WHERE entity_type = ? AND entity_id = ? ORDER BY id
                """,
                (entity_type, entity_id),
            ).fetchall()
            return tuple(_event_from_row(row) for row in rows)

    @contextmanager
    def _transaction(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path,
            timeout=self.timeout_seconds,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.execute(f"PRAGMA busy_timeout = {int(self.timeout_seconds * 1000)}")
        return connection

    def _get_message_in(
        self, connection: sqlite3.Connection, message_row_id: int
    ) -> MessageRecord:
        row = connection.execute(
            "SELECT * FROM messages WHERE id = ?", (message_row_id,)
        ).fetchone()
        if row is None:
            raise StateNotFoundError(f"message not found: {message_row_id}")
        return _message_from_row(row)

    def _get_attachment_by_id_in(
        self, connection: sqlite3.Connection, attachment_id: int
    ) -> AttachmentRecord:
        row = connection.execute(
            "SELECT * FROM attachments WHERE id = ?", (attachment_id,)
        ).fetchone()
        if row is None:
            raise StateNotFoundError(f"attachment not found: {attachment_id}")
        return _attachment_from_row(row)

    def _get_attempt_in(
        self, connection: sqlite3.Connection, attempt_id: int
    ) -> CommandAttemptRecord:
        row = connection.execute(
            "SELECT * FROM command_attempts WHERE id = ?", (attempt_id,)
        ).fetchone()
        if row is None:
            raise StateNotFoundError(f"command attempt not found: {attempt_id}")
        return _attempt_from_row(row)

    @staticmethod
    def _add_event(
        connection: sqlite3.Connection,
        *,
        entity_type: str,
        entity_id: int,
        previous_state: str | None,
        new_state: str,
        reason: str,
        created_at: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO state_events (
                entity_type, entity_id, previous_state, new_state, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (entity_type, entity_id, previous_state, new_state, reason, created_at),
        )


def _message_from_row(row: sqlite3.Row) -> MessageRecord:
    return MessageRecord(
        id=int(row["id"]),
        account_alias=str(row["account_alias"]),
        mailbox=str(row["mailbox"]),
        mailbox_uidvalidity=str(row["mailbox_uidvalidity"]),
        message_uid=str(row["message_uid"]),
        message_id=str(row["message_id"]),
        thread_id=row["thread_id"],
        subject=str(row["subject"]),
        sender=str(row["sender"]),
        message_date=str(row["message_date"]),
        status=MessageStatus(str(row["status"])),
        command_id=row["command_id"],
        acknowledged_at=row["acknowledged_at"],
        last_error=row["last_error"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _attachment_from_row(row: sqlite3.Row) -> AttachmentRecord:
    return AttachmentRecord(
        id=int(row["id"]),
        message_row_id=int(row["message_row_id"]),
        local_temp_id=str(row["local_temp_id"]),
        local_relative_path=str(row["local_relative_path"]),
        original_filename=str(row["original_filename"]),
        sanitized_filename=str(row["sanitized_filename"]),
        mime_type=str(row["mime_type"]),
        size_bytes=int(row["size_bytes"]),
        sha256=str(row["sha256"]),
        quarantine_status=QuarantineStatus(str(row["quarantine_status"])),
        status_reason=str(row["status_reason"]),
        scan_engine=str(row["scan_engine"]),
        scan_result=str(row["scan_result"]),
        drive_file_id=row["drive_file_id"],
        bucoliche_row_reference=row["bucoliche_row_reference"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _attempt_from_row(row: sqlite3.Row) -> CommandAttemptRecord:
    return CommandAttemptRecord(
        id=int(row["id"]),
        message_row_id=int(row["message_row_id"]),
        command_id=str(row["command_id"]),
        attempt_number=int(row["attempt_number"]),
        dry_run=bool(row["dry_run"]),
        status=CommandAttemptStatus(str(row["status"])),
        request_sha256=str(row["request_sha256"]),
        response_ok=None if row["response_ok"] is None else bool(row["response_ok"]),
        response_message=row["response_message"],
        error_code=row["error_code"],
        retryable=None if row["retryable"] is None else bool(row["retryable"]),
        created_at=str(row["created_at"]),
        completed_at=row["completed_at"],
    )


def _event_from_row(row: sqlite3.Row) -> StateEvent:
    return StateEvent(
        id=int(row["id"]),
        entity_type=str(row["entity_type"]),
        entity_id=int(row["entity_id"]),
        previous_state=row["previous_state"],
        new_state=str(row["new_state"]),
        reason=str(row["reason"]),
        created_at=str(row["created_at"]),
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
