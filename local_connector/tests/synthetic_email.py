"""Local-only EML mailbox used by integration tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from pathlib import Path

from virgilio_connector.files import sanitize_filename
from virgilio_connector.ports import AttachmentReference, MessageReference


@dataclass
class SyntheticEmlMailbox:
    source_dir: Path
    quarantine_dir: Path
    mailbox: str = "Virgilio/da-traghettare"
    uidvalidity: str = "synthetic-1"
    acknowledged: list[str] = field(default_factory=list)

    def list_pending(self):
        messages = []
        for path in sorted(self.source_dir.glob("*.eml")):
            uid = path.stem
            if uid in self.acknowledged:
                continue
            parsed = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
            date = parsedate_to_datetime(parsed["Date"]).isoformat()
            messages.append(MessageReference(
                mailbox=self.mailbox, uidvalidity=self.uidvalidity, message_uid=uid,
                message_id=parsed.get("Message-ID", ""), subject=parsed.get("Subject", ""),
                sender=parsed.get("From", "unknown@example.invalid"), date=date,
                thread_id=parsed.get("X-Synthetic-Thread-ID"),
            ))
        return tuple(messages)

    def download_attachments(self, message):
        source = self.source_dir / f"{message.message_uid}.eml"
        parsed = BytesParser(policy=policy.default).parsebytes(source.read_bytes())
        target_dir = self.quarantine_dir / message.message_uid
        target_dir.mkdir(parents=True, exist_ok=True)
        result = []
        for index, part in enumerate(parsed.iter_attachments(), start=1):
            original = part.get_filename() or f"unnamed-{index}.bin"
            target = target_dir / sanitize_filename(original)
            target.write_bytes(part.get_payload(decode=True) or b"")
            result.append(AttachmentReference(
                local_temp_id=f"eml-{message.message_uid}-{index}",
                original_filename=original, local_path=target,
            ))
        return tuple(result)

    def acknowledge(self, message):
        self.acknowledged.append(message.message_uid)
