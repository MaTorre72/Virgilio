"""Read-only IMAP to local quarantine pipeline. No Caronte or Drive boundary."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from .files import sanitize_filename
from .local_paths import LocalDataPaths
from .policy import AttachmentPolicy, PolicyDecision
from .readonly_state import ReadonlyStateStore


@dataclass(frozen=True, slots=True)
class QuarantinePlanItem:
    message_uid: str
    ordinal: int
    original_filename: str | None
    sanitized_filename: str | None
    size_bytes: int
    sha256: str
    decision: str
    saved: bool


class ReadonlyQuarantineRunner:
    def __init__(self, *, mailbox, paths: LocalDataPaths | None = None,
                 policy: AttachmentPolicy | None = None,
                 max_attachment_bytes: int = 25 * 1024 * 1024) -> None:
        if max_attachment_bytes <= 0:
            raise ValueError("max_attachment_bytes must be positive")
        self.mailbox = mailbox
        self.paths = paths or LocalDataPaths()
        self.policy = policy or AttachmentPolicy()
        self.max_attachment_bytes = max_attachment_bytes

    def run(self, *, dry_run: bool) -> tuple[QuarantinePlanItem, ...]:
        messages = self.mailbox.list_pending()
        if dry_run:
            return self._plan(messages)
        self.paths.create()
        store = ReadonlyStateStore(self.paths.state_db)
        store.initialize()
        run_id = store.start_run()
        results = []
        attachments_seen = 0
        try:
            for message in messages:
                message_row_id = store.add_message(run_id, message)
                for attachment in self.mailbox.detect_attachments(message):
                    attachments_seen += 1
                    results.append(self._persist(store, message_row_id, message, attachment))
            store.complete_run(run_id, messages_seen=len(messages),
                               attachments_seen=attachments_seen)
            return tuple(results)
        except Exception:
            store.complete_run(run_id, messages_seen=len(messages),
                               attachments_seen=attachments_seen, status="error")
            raise

    def _plan(self, messages) -> tuple[QuarantinePlanItem, ...]:
        result = []
        for message in messages:
            for attachment in self.mailbox.detect_attachments(message):
                digest = hashlib.sha256(attachment.payload).hexdigest()
                filename = (sanitize_filename(attachment.original_filename)
                            if attachment.original_filename else None)
                decision, _ = self._decision(attachment.original_filename,
                                             len(attachment.payload))
                result.append(QuarantinePlanItem(message.message_uid, attachment.ordinal,
                    attachment.original_filename, filename, len(attachment.payload), digest,
                    decision, False))
        return tuple(result)

    def _persist(self, store, message_row_id, message, attachment) -> QuarantinePlanItem:
        payload = attachment.payload
        digest = hashlib.sha256(payload).hexdigest()
        filename = (sanitize_filename(attachment.original_filename)
                    if attachment.original_filename else None)
        status, reason = self._decision(attachment.original_filename, len(payload))
        relative_path = None
        duplicate_of_id = None
        saved = False
        if status == "ready_for_scan":
            duplicate = store.find_by_sha256(digest)
            if duplicate:
                duplicate_of_id = int(duplicate["id"])
                relative_path = str(duplicate["relative_path"])
                reason = "duplicate sha256; existing quarantined bytes reused"
            else:
                opaque_dir = f"{message.uidvalidity or 'unknown'}-{message.message_uid}"
                target_dir = self.paths.incoming / sanitize_filename(opaque_dir)
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / f"{attachment.ordinal:03d}-{filename}"
                temporary = target.with_suffix(target.suffix + ".attachment.tmp")
                temporary.write_bytes(payload)
                temporary.replace(target)
                relative_path = target.relative_to(self.paths.root).as_posix()
                saved = True
        store.add_attachment(message_row_id, ordinal=attachment.ordinal,
            original_filename=attachment.original_filename, sanitized_filename=filename,
            declared_mime_type=attachment.declared_mime_type, size_bytes=len(payload),
            sha256=digest, status=status, relative_path=relative_path,
            duplicate_of_id=duplicate_of_id, reason=reason)
        return QuarantinePlanItem(message.message_uid, attachment.ordinal,
            attachment.original_filename, filename, len(payload), digest, status, saved)

    def _decision(self, filename: str | None, size_bytes: int) -> tuple[str, str]:
        if size_bytes > self.max_attachment_bytes:
            return "rejected_by_size", "attachment exceeds configured size limit"
        if not filename:
            return "rejected_by_extension", "attachment has no filename"
        result = self.policy.evaluate_filename(filename)
        if result.decision is not PolicyDecision.ALLOW:
            return "rejected_by_extension", result.reason
        return "ready_for_scan", "extension allowed; awaiting future antivirus scan"
