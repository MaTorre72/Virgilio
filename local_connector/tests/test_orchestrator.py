from pathlib import Path
import tempfile
import unittest

from virgilio_connector.in_memory import InMemoryAntivirus, InMemoryCaronte, InMemoryMailbox
from virgilio_connector.orchestrator import ConnectorConfig, ConnectorOrchestrator
from virgilio_connector.ports import AttachmentReference, MessageReference
from virgilio_connector.state_db import StateStore
from virgilio_connector.state_models import MessageStatus


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.document = root / "document.docx"
        self.document.write_bytes(b"synthetic office document")
        self.message = MessageReference("Virgilio/da-traghettare", "100", "42",
            "<test@example.invalid>", "Synthetic", "sender@example.invalid",
            "2026-06-23T10:00:00+02:00")
        self.mailbox = InMemoryMailbox((self.message,), {"42": (
            AttachmentReference("att-1", "document.docx", self.document),)})
        self.caronte = InMemoryCaronte()
        self.store = StateStore(root / "state.db")
        self.store.initialize()

    def tearDown(self):
        self.temp.cleanup()

    def orchestrator(self, scanner=None):
        return ConnectorOrchestrator(mailbox=self.mailbox,
            antivirus=scanner or InMemoryAntivirus(), caronte=self.caronte,
            store=self.store, config=ConnectorConfig("test-connector", "test-user"))

    def test_complete_offline_cycle_acknowledges_only_after_caronte_confirmation(self):
        result = self.orchestrator().run_once()[0]
        self.assertEqual(result.status, MessageStatus.ACKNOWLEDGED)
        self.assertTrue(result.acknowledged)
        self.assertEqual(self.mailbox.acknowledged, ["42"])
        self.assertEqual(len(self.caronte.submitted), 1)
        attachment = self.store.get_attachment("att-1")
        self.assertEqual(attachment.drive_file_id, "drive-att-1")

    def test_denied_extension_never_reaches_scanner_or_caronte(self):
        dangerous = Path(self.temp.name) / "payload.exe"
        dangerous.write_bytes(b"not executable")
        self.mailbox.attachments["42"] = (AttachmentReference("att-2", "payload.exe", dangerous),)
        result = self.orchestrator().run_once()[0]
        self.assertEqual(result.status, MessageStatus.REJECTED)
        self.assertFalse(result.acknowledged)
        self.assertEqual(self.caronte.submitted, [])

    def test_infected_attachment_is_not_submitted_or_acknowledged(self):
        scanner = InMemoryAntivirus(frozenset({self.document}))
        result = self.orchestrator(scanner).run_once()[0]
        self.assertEqual(result.status, MessageStatus.REJECTED)
        self.assertEqual(self.mailbox.acknowledged, [])
        self.assertEqual(self.caronte.submitted, [])


if __name__ == "__main__":
    unittest.main()
