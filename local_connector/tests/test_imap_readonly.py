from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path
import tempfile
import unittest

from virgilio_connector.imap_readonly import ImapReadonlyConfig, ImapReadonlyError, ImapReadonlyMailbox


def eml_bytes():
    message = EmailMessage()
    message["From"] = "sender@example.invalid"
    message["To"] = "test@example.invalid"
    message["Date"] = "Tue, 23 Jun 2026 10:00:00 +0200"
    message["Message-ID"] = "<readonly@example.invalid>"
    message["Subject"] = "Readonly synthetic"
    message.set_content("Synthetic body")
    message.add_attachment(b"%PDF-test", maintype="application", subtype="pdf", filename="report.pdf")
    return message.as_bytes(policy=SMTP)


class FakeImapClient:
    instances = []

    def __init__(self, host, port, *, timeout):
        self.calls = [("connect", host, port, timeout)]
        self.__class__.instances.append(self)

    def login(self, username, password):
        self.calls.append(("login", username, password))
        return "OK", [b"logged in"]

    def select(self, mailbox, readonly=False):
        self.calls.append(("select", mailbox, readonly))
        return "OK", [b"1"]

    def uid(self, command, *args):
        self.calls.append(("uid", command, *args))
        if command == "SEARCH":
            return "OK", [b"42"]
        return "OK", [(b"42 (BODY[] {1})", eml_bytes()), b")"]

    def response(self, name):
        self.calls.append(("response", name))
        return "UIDVALIDITY", [b"12345"]

    def close(self):
        self.calls.append(("close",))

    def logout(self):
        self.calls.append(("logout",))


class ImapReadonlyTests(unittest.TestCase):
    def setUp(self):
        FakeImapClient.instances.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.adapter = ImapReadonlyMailbox(
            ImapReadonlyConfig("imap.example.invalid", "test-user", "test-password"),
            Path(self.temp.name), client_factory=FakeImapClient)

    def tearDown(self):
        self.temp.cleanup()

    def test_lists_and_downloads_with_readonly_and_body_peek(self):
        reference = self.adapter.list_pending()[0]
        attachment = self.adapter.download_attachments(reference)[0]
        calls = [call for client in FakeImapClient.instances for call in client.calls]
        self.assertEqual(reference.uidvalidity, "12345")
        self.assertEqual(reference.subject, "Readonly synthetic")
        self.assertEqual(attachment.original_filename, "report.pdf")
        self.assertEqual(attachment.local_path.read_bytes(), b"%PDF-test")
        self.assertTrue(all(call[2] is True for call in calls if call[0] == "select"))
        fetches = [call for call in calls if call[:2] == ("uid", "FETCH")]
        self.assertTrue(fetches)
        self.assertTrue(all("BODY.PEEK[]" in str(call) for call in fetches))

    def test_never_issues_mutating_imap_commands(self):
        reference = self.adapter.list_pending()[0]
        self.adapter.download_attachments(reference)
        calls = [str(call).upper() for client in FakeImapClient.instances for call in client.calls]
        for forbidden in ("STORE", "COPY", "MOVE", "EXPUNGE", "DELETE"):
            self.assertFalse(any(forbidden in call for call in calls))
        with self.assertRaises(ImapReadonlyError):
            self.adapter.acknowledge(reference)

    def test_password_is_redacted_from_config_repr(self):
        self.assertNotIn("test-password", repr(self.adapter.config))


if __name__ == "__main__":
    unittest.main()
