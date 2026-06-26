"""Minimal IMAP4/SSL mailbox adapter constrained to read-only operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
import imaplib
from pathlib import Path
from typing import Callable

from .files import sanitize_filename
from .ports import AttachmentReference, MessageReference


class ImapReadonlyError(RuntimeError):
    """Raised when the read-only IMAP session cannot return valid data."""


@dataclass(frozen=True, slots=True)
class DetectedAttachment:
    ordinal: int
    original_filename: str | None
    declared_mime_type: str
    payload: bytes = field(repr=False)


@dataclass(frozen=True, slots=True)
class ImapReadonlyConfig:
    host: str
    username: str
    password: str = field(repr=False)
    mailbox: str = "Virgilio/da-traghettare"
    port: int = 993
    timeout_seconds: float = 20.0
    max_messages: int = 25

    def __post_init__(self) -> None:
        if not self.host.strip() or not self.username.strip() or not self.password:
            raise ValueError("host, username and password are required")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if self.timeout_seconds <= 0 or self.max_messages <= 0:
            raise ValueError("timeout_seconds and max_messages must be positive")


class ImapReadonlyMailbox:
    """Reads one configured folder without flags, moves, deletes, or expunge."""

    def __init__(self, config: ImapReadonlyConfig, quarantine_root: str | Path,
                 *, client_factory: Callable[..., object] = imaplib.IMAP4_SSL) -> None:
        self.config = config
        self.quarantine_root = Path(quarantine_root)
        self._client_factory = client_factory

    def list_pending(self) -> tuple[MessageReference, ...]:
        client = self._connect()
        try:
            self._select_readonly(client)
            status, data = client.uid("SEARCH", None, "ALL")
            self._require_ok(status, "UID SEARCH")
            raw_uids = data[0].split() if data and data[0] else []
            uids = raw_uids[-self.config.max_messages:]
            return tuple(self._reference(client, uid.decode("ascii")) for uid in uids)
        finally:
            self._close(client)

    def download_attachments(self, message: MessageReference) -> tuple[AttachmentReference, ...]:
        """Legacy test helper. Production LC3 uses detect_attachments instead."""
        client = self._connect()
        try:
            self._select_readonly(client)
            parsed = self._fetch_message(client, message.message_uid)
            target_dir = self.quarantine_root / sanitize_filename(message.message_uid)
            target_dir.mkdir(parents=True, exist_ok=True)
            attachments = []
            for index, part in enumerate(parsed.iter_attachments(), start=1):
                original = part.get_filename() or f"unnamed-{index}.bin"
                filename = f"{index:03d}-{sanitize_filename(original)}"
                target = target_dir / filename
                target.write_bytes(part.get_payload(decode=True) or b"")
                attachments.append(AttachmentReference(
                    local_temp_id=f"imap-{message.uidvalidity or 'unknown'}-{message.message_uid}-{index}",
                    original_filename=original, local_path=target,
                ))
            return tuple(attachments)
        finally:
            self._close(client)

    def detect_attachments(self, message: MessageReference) -> tuple[DetectedAttachment, ...]:
        """Return MIME attachment bytes without writing files or changing flags."""
        client = self._connect()
        try:
            self._select_readonly(client)
            parsed = self._fetch_message(client, message.message_uid)
            return tuple(DetectedAttachment(
                ordinal=index, original_filename=part.get_filename(),
                declared_mime_type=part.get_content_type(),
                payload=part.get_payload(decode=True) or b"",
            ) for index, part in enumerate(parsed.iter_attachments(), start=1))
        finally:
            self._close(client)

    def acknowledge(self, message: MessageReference) -> None:
        raise ImapReadonlyError("acknowledge is disabled for a read-only IMAP adapter")

    def _connect(self):
        client = self._client_factory(self.config.host, self.config.port,
                                      timeout=self.config.timeout_seconds)
        status, _ = client.login(self.config.username, self.config.password)
        self._require_ok(status, "LOGIN")
        return client

    def _select_readonly(self, client) -> None:
        status, _ = client.select(self.config.mailbox, readonly=True)
        self._require_ok(status, "SELECT READ-ONLY")

    def _reference(self, client, uid: str) -> MessageReference:
        parsed = self._fetch_message(client, uid)
        date_header = parsed.get("Date")
        try:
            date = parsedate_to_datetime(date_header).isoformat() if date_header else "1970-01-01T00:00:00+00:00"
        except (TypeError, ValueError):
            date = "1970-01-01T00:00:00+00:00"
        response = client.response("UIDVALIDITY")
        uidvalidity = None
        if response and len(response) > 1 and response[1]:
            value = response[1][0]
            uidvalidity = value.decode("ascii") if isinstance(value, bytes) else str(value)
        return MessageReference(
            mailbox=self.config.mailbox, uidvalidity=uidvalidity, message_uid=uid,
            message_id=parsed.get("Message-ID", ""), subject=parsed.get("Subject", ""),
            sender=parsed.get("From", "unknown@example.invalid"), date=date,
            thread_id=parsed.get("Thread-Index") or parsed.get("X-GM-THRID"),
        )

    def _fetch_message(self, client, uid: str):
        status, data = client.uid("FETCH", uid, "(BODY.PEEK[])")
        self._require_ok(status, "UID FETCH BODY.PEEK")
        payload = next((item[1] for item in data if isinstance(item, tuple) and len(item) > 1), None)
        if not isinstance(payload, bytes):
            raise ImapReadonlyError(f"UID {uid} returned no RFC 822 payload")
        return BytesParser(policy=policy.default).parsebytes(payload)

    @staticmethod
    def _require_ok(status, operation: str) -> None:
        text = status.decode("ascii", "replace") if isinstance(status, bytes) else str(status)
        if text.upper() != "OK":
            raise ImapReadonlyError(f"{operation} failed")

    @staticmethod
    def _close(client) -> None:
        try:
            client.close()
        except (imaplib.IMAP4.error, OSError):
            pass
        try:
            client.logout()
        except (imaplib.IMAP4.error, OSError):
            pass


class ImapCompletionMailbox:
    """Minimal IMAP completion adapter: SEARCH + COPY only, no EXPUNGE/STORE."""

    def __init__(self, config: ImapReadonlyConfig, *,
                 done_folder: str,
                 client_factory: Callable[..., object] = imaplib.IMAP4_SSL) -> None:
        self.config = config
        self.done_folder = done_folder
        self._client_factory = client_factory

    def input_contains_uid(self, uid: str) -> bool:
        client = self._connect()
        try:
            self._select(client, self.config.mailbox, readonly=True)
            status, data = client.uid("SEARCH", None, "UID", str(uid))
            ImapReadonlyMailbox._require_ok(status, "UID SEARCH INPUT")
            return bool(data and data[0] and data[0].split())
        finally:
            ImapReadonlyMailbox._close(client)

    def done_contains_message_id(self, message_id: str) -> bool:
        if not message_id:
            return False
        client = self._connect()
        try:
            self._select(client, self.done_folder, readonly=True)
            status, data = client.uid("SEARCH", None, "HEADER", "Message-ID", message_id)
            ImapReadonlyMailbox._require_ok(status, "UID SEARCH DONE")
            return bool(data and data[0] and data[0].split())
        finally:
            ImapReadonlyMailbox._close(client)

    def add_done_label_only(self, uid: str) -> None:
        client = self._connect()
        try:
            self._select(client, self.config.mailbox, readonly=False)
            status, _ = client.uid("COPY", str(uid), self.done_folder)
            ImapReadonlyMailbox._require_ok(status, "UID COPY DONE")
        finally:
            ImapReadonlyMailbox._close(client)

    def _connect(self):
        client = self._client_factory(self.config.host, self.config.port,
                                      timeout=self.config.timeout_seconds)
        status, _ = client.login(self.config.username, self.config.password)
        ImapReadonlyMailbox._require_ok(status, "LOGIN")
        return client

    @staticmethod
    def _select(client, mailbox: str, *, readonly: bool) -> None:
        status, _ = client.select(mailbox, readonly=readonly)
        ImapReadonlyMailbox._require_ok(status, "SELECT")
