from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path
import tempfile
import unittest

from synthetic_email import SyntheticEmlMailbox
from virgilio_connector.in_memory import InMemoryAntivirus, InMemoryCaronte
from virgilio_connector.models import QuarantineStatus
from virgilio_connector.orchestrator import ConnectorConfig, ConnectorOrchestrator
from virgilio_connector.state_db import StateStore
from virgilio_connector.state_models import MessageStatus


def write_email(path: Path, *, subject: str, attachments=()):
    message = EmailMessage()
    message["From"] = "mittente@example.invalid"
    message["To"] = "virgilio@example.invalid"
    message["Date"] = "Tue, 23 Jun 2026 09:30:00 +0200"
    message["Message-ID"] = f"<{path.stem}@example.invalid>"
    message["Subject"] = subject
    message["X-Synthetic-Thread-ID"] = f"thread-{path.stem}"
    message.set_content("Corpo sintetico senza dati personali.")
    for filename, content, maintype, subtype in attachments:
        message.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)
    path.write_bytes(message.as_bytes(policy=SMTP))


class SyntheticEmailIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.inbox = root / "inbox"
        self.inbox.mkdir()
        self.mailbox = SyntheticEmlMailbox(self.inbox, root / "quarantine")
        self.caronte = InMemoryCaronte()
        self.store = StateStore(root / "state.db")
        self.store.initialize()

    def tearDown(self):
        self.temp.cleanup()

    def run_cycle(self):
        return ConnectorOrchestrator(
            mailbox=self.mailbox, antivirus=InMemoryAntivirus(), caronte=self.caronte,
            store=self.store, config=ConnectorConfig("synthetic-test", "test-user"),
        ).run_once()

    def test_pdf_email_is_parsed_submitted_and_acknowledged(self):
        write_email(self.inbox / "101.eml", subject="Relazione tecnica",
                    attachments=(("relazione.pdf", b"%PDF-synthetic", "application", "pdf"),))
        result = self.run_cycle()[0]
        command = self.caronte.submitted[0]
        self.assertEqual(result.status, MessageStatus.ACKNOWLEDGED)
        self.assertEqual(command.subject, "Relazione tecnica")
        self.assertEqual(command.sender, "mittente@example.invalid")
        self.assertEqual(command.thread_id, "thread-101")
        self.assertEqual(command.attachments[0].original_filename, "relazione.pdf")

    def test_email_with_safe_and_executable_attachment_submits_only_safe_file(self):
        write_email(self.inbox / "102.eml", subject="Allegati misti", attachments=(
            ("planimetria.png", b"synthetic-png", "image", "png"),
            ("installer.exe", b"synthetic-executable", "application", "octet-stream"),
        ))
        result = self.run_cycle()[0]
        command = self.caronte.submitted[0]
        self.assertTrue(result.acknowledged)
        self.assertEqual([x.original_filename for x in command.attachments], ["planimetria.png"])
        self.assertEqual(self.store.get_attachment("eml-102-2").quarantine_status,
                         QuarantineStatus.REJECTED)

    def test_email_without_attachments_is_rejected_without_ack(self):
        write_email(self.inbox / "103.eml", subject="Solo testo")
        result = self.run_cycle()[0]
        self.assertEqual(result.status, MessageStatus.REJECTED)
        self.assertFalse(result.acknowledged)
        self.assertEqual(self.caronte.submitted, [])
        self.assertEqual(self.mailbox.acknowledged, [])

    def test_multiple_emails_are_processed_independently_and_second_poll_is_empty(self):
        for uid in ("104", "105"):
            write_email(self.inbox / f"{uid}.eml", subject=f"Documento {uid}",
                        attachments=((f"documento-{uid}.pdf", uid.encode(), "application", "pdf"),))
        first = self.run_cycle()
        second = self.run_cycle()
        self.assertEqual(len(first), 2)
        self.assertTrue(all(x.acknowledged for x in first))
        self.assertEqual(second, ())
        self.assertEqual(self.mailbox.acknowledged, ["104", "105"])


if __name__ == "__main__":
    unittest.main()
