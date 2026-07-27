"""Minimal IMAP4/SSL mailbox adapter constrained to read-only operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
import imaplib
from pathlib import Path
import re
from typing import Callable

from .files import sanitize_filename
from .ports import AttachmentReference, MessageReference


class ImapReadonlyError(RuntimeError):
    """Raised when the read-only IMAP session cannot return valid data."""


class ImapCompletionError(ImapReadonlyError):
    """Raised when prudent IMAP completion cannot safely add the done label."""


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
    auth_mode: str = "password"

    def __post_init__(self) -> None:
        if not self.host.strip() or not self.username.strip() or not self.password:
            raise ValueError("host, username and password are required")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if self.timeout_seconds <= 0 or self.max_messages <= 0:
            raise ValueError("timeout_seconds and max_messages must be positive")
        if self.auth_mode not in {"password", "oauth2"}:
            raise ValueError("unsupported IMAP authentication mode")


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
            uidvalidity = self._uidvalidity(client)
            status, data = client.uid("SEARCH", None, "ALL")
            self._require_ok(status, "UID SEARCH")
            raw_uids = data[0].split() if data and data[0] else []
            uids = raw_uids[-self.config.max_messages:]
            return tuple(
                self._reference(client, uid.decode("ascii"), uidvalidity)
                for uid in uids
            )
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
        if self.config.auth_mode == "oauth2":
            payload = (
                f"user={self.config.username}\x01"
                f"auth=Bearer {self.config.password}\x01\x01"
            ).encode("utf-8")
            status, _ = client.authenticate("XOAUTH2", lambda _challenge: payload)
            self._require_ok(status, "AUTHENTICATE XOAUTH2")
        else:
            status, _ = client.login(self.config.username, self.config.password)
            self._require_ok(status, "LOGIN")
        return client

    def _select_readonly(self, client) -> None:
        status, _ = client.select(self.config.mailbox, readonly=True)
        self._require_ok(status, "SELECT READ-ONLY")

    @staticmethod
    def _uidvalidity(client) -> str | None:
        read_response = getattr(client, "response", None)
        if not callable(read_response):
            return None
        response = read_response("UIDVALIDITY")
        if not response or len(response) <= 1 or not response[1]:
            return None
        value = response[1][0]
        return value.decode("ascii") if isinstance(value, bytes) else str(value)

    def _reference(self, client, uid: str, uidvalidity: str | None) -> MessageReference:
        parsed = self._fetch_message(client, uid)
        date_header = parsed.get("Date")
        try:
            date = parsedate_to_datetime(date_header).isoformat() if date_header else "1970-01-01T00:00:00+00:00"
        except (TypeError, ValueError):
            date = "1970-01-01T00:00:00+00:00"
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
    """Minimal IMAP completion adapter without DELETE or EXPUNGE."""

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
            listed = self.list_mailboxes(client=client)
            if self.done_folder not in listed:
                raise ImapCompletionError(
                    "done_folder_not_found_in_imap_list: "
                    f"done_folder={self.done_folder!r}; "
                    f"available_mailboxes={', '.join(listed) if listed else '<empty>'}; "
                    "verify exact IMAP name and 'Mostra in IMAP'"
                )
            self._select(client, self.config.mailbox, readonly=False)
            target = self._mailbox_argument(self.done_folder)
            status, data = client.uid("COPY", str(uid), target)
            self._require_completion_ok(
                status,
                "UID COPY DONE",
                done_folder=self.done_folder,
                data=data,
            )
        finally:
            ImapReadonlyMailbox._close(client)

    def move_to_done_label(self, uid: str, message_id: str) -> None:
        """Apply/remove labels and prove both final label post-conditions."""
        if not message_id:
            raise ImapCompletionError(
                "move_to_done_label requires Message-ID for postcondition verification"
            )
        client = self._connect()
        try:
            listed = self.list_mailboxes(client=client)
            missing = tuple(
                mailbox
                for mailbox in (self.config.mailbox, self.done_folder)
                if mailbox not in listed
            )
            if missing:
                raise ImapCompletionError(
                    "completion_folder_not_found_in_imap_list: "
                    f"missing_mailboxes={', '.join(missing)}; "
                    f"available_mailboxes={', '.join(listed) if listed else '<empty>'}; "
                    "verify exact IMAP name and 'Mostra in IMAP'"
                )
            if self.config.mailbox == self.done_folder:
                raise ImapCompletionError(
                    "input_folder and done_folder must be different for move_to_done_label"
                )
            self._select(client, self.config.mailbox, readonly=False)
            gmail_message_id = self._gmail_message_id(client, str(uid))
            target = self._mailbox_argument(self.done_folder)
            status, data = client.uid("COPY", str(uid), target)
            self._require_completion_ok(
                status,
                "UID COPY DONE",
                done_folder=self.done_folder,
                data=data,
            )
            self._select(client, self.done_folder, readonly=False)
            done_uid = self._uid_for_gmail_message_id(client, gmail_message_id)
            source_label = f"({self._mailbox_argument(self.config.mailbox)})"
            status, data = client.uid(
                "STORE", done_uid, "-X-GM-LABELS", source_label
            )
            self._require_completion_ok(
                status,
                "UID STORE REMOVE INPUT LABEL",
                done_folder=self.config.mailbox,
                data=data,
            )
        finally:
            ImapReadonlyMailbox._close(client)
        input_present = self.input_contains_uid(uid)
        done_present = self.done_contains_message_id(message_id)
        if input_present or not done_present:
            raise ImapCompletionError(
                "move_to_done_label postcondition failed: "
                f"input_present={input_present}; done_present={done_present}"
            )

    @classmethod
    def _gmail_message_id(cls, client, uid: str) -> str:
        status, data = client.uid("FETCH", uid, "(X-GM-MSGID)")
        cls._require_completion_ok(status, "UID FETCH X-GM-MSGID", data=data)
        values = []
        for item in data or ():
            text = item.decode("ascii", "replace") if isinstance(item, bytes) else str(item)
            values.extend(re.findall(r"\bX-GM-MSGID\s+(\d+)\b", text, flags=re.IGNORECASE))
        unique = tuple(dict.fromkeys(values))
        if len(unique) != 1:
            raise ImapCompletionError("UID FETCH X-GM-MSGID returned no unique Gmail message id")
        return unique[0]

    @classmethod
    def _uid_for_gmail_message_id(cls, client, gmail_message_id: str) -> str:
        status, data = client.uid("SEARCH", None, "X-GM-MSGID", gmail_message_id)
        cls._require_completion_ok(status, "UID SEARCH X-GM-MSGID", data=data)
        values = tuple(
            token.decode("ascii", "replace") if isinstance(token, bytes) else str(token)
            for item in data or ()
            for token in (item.split() if isinstance(item, bytes) else str(item).split())
        )
        if len(values) != 1 or not values[0].isdigit():
            raise ImapCompletionError("UID SEARCH X-GM-MSGID returned no unique done-folder UID")
        return values[0]

    def list_mailboxes(self, *, client=None) -> tuple[str, ...]:
        close_client = client is None
        active_client = client or self._connect()
        try:
            status, data = active_client.list('""', "*")
            self._require_completion_ok(status, "LIST", done_folder=self.done_folder, data=data)
            return tuple(
                item
                for item in (self._parse_list_mailbox_name(line) for line in data or ())
                if item
            )
        finally:
            if close_client:
                ImapReadonlyMailbox._close(active_client)

    def _connect(self):
        client = self._client_factory(self.config.host, self.config.port,
                                      timeout=self.config.timeout_seconds)
        if self.config.auth_mode == "oauth2":
            payload = (
                f"user={self.config.username}\x01"
                f"auth=Bearer {self.config.password}\x01\x01"
            ).encode("utf-8")
            status, _ = client.authenticate("XOAUTH2", lambda _challenge: payload)
            ImapReadonlyMailbox._require_ok(status, "AUTHENTICATE XOAUTH2")
        else:
            status, _ = client.login(self.config.username, self.config.password)
            ImapReadonlyMailbox._require_ok(status, "LOGIN")
        return client

    @staticmethod
    def _select(client, mailbox: str, *, readonly: bool) -> None:
        status, data = client.select(ImapCompletionMailbox._mailbox_argument(mailbox),
                                     readonly=readonly)
        ImapCompletionMailbox._require_completion_ok(
            status, "SELECT", done_folder=mailbox, data=data)

    @staticmethod
    def _mailbox_argument(mailbox: str) -> str:
        if re.fullmatch(r"[A-Za-z0-9_\-./]+", mailbox):
            return mailbox
        escaped = mailbox.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    @staticmethod
    def _parse_list_mailbox_name(line) -> str | None:
        if line is None:
            return None
        text = line.decode("utf-8", "replace") if isinstance(line, bytes) else str(line)
        if not text:
            return None
        if text.startswith("("):
            closing = text.find(")")
            if closing != -1:
                text = text[closing + 1:].lstrip()
        if not text:
            return None
        if text.startswith("NIL"):
            text = text[3:].lstrip()
        elif text.startswith('"'):
            text = ImapCompletionMailbox._consume_quoted(text)[0].lstrip()
        else:
            parts = text.split(maxsplit=1)
            text = parts[1].lstrip() if len(parts) == 2 else ""
        if not text:
            return None
        if text.startswith('"'):
            _, mailbox = ImapCompletionMailbox._consume_quoted(text)
            return mailbox
        return text

    @staticmethod
    def _consume_quoted(text: str) -> tuple[str, str]:
        escaped = False
        collected: list[str] = []
        for index, char in enumerate(text[1:], start=1):
            if escaped:
                collected.append(char)
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                return text[index + 1:], "".join(collected)
            collected.append(char)
        return "", text.strip('"')

    @staticmethod
    def _require_completion_ok(status, operation: str, *,
                               done_folder: str | None = None,
                               data=None) -> None:
        text = status.decode("ascii", "replace") if isinstance(status, bytes) else str(status)
        if text.upper() == "OK":
            return
        detail = ImapCompletionMailbox._stringify_imap_data(data)
        context = f"; done_folder={done_folder!r}" if done_folder is not None else ""
        suffix = (
            "; verify exact IMAP name and 'Mostra in IMAP'"
            if operation == "UID COPY DONE"
            else ""
        )
        raise ImapCompletionError(
            f"{operation} failed{context}; imap_status={text}; imap_detail={detail}{suffix}"
        )

    @staticmethod
    def _stringify_imap_data(data) -> str:
        if not data:
            return "<none>"
        parts: list[str] = []
        for item in data:
            if isinstance(item, bytes):
                parts.append(item.decode("utf-8", "replace"))
            elif isinstance(item, tuple):
                tuple_parts = []
                for value in item:
                    if isinstance(value, bytes):
                        tuple_parts.append(value.decode("utf-8", "replace"))
                    else:
                        tuple_parts.append(str(value))
                parts.append(" | ".join(tuple_parts))
            else:
                parts.append(str(item))
        return " ; ".join(parts)
