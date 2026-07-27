from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path
import tempfile
import unittest

from virgilio_connector.imap_readonly import (
    ImapCompletionError,
    ImapCompletionMailbox,
    ImapReadonlyConfig,
    ImapReadonlyError,
    ImapReadonlyMailbox,
)


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
    list_data = [b'(\\HasNoChildren) "/" "Virgilio/traghettate"']
    copy_status = "OK"
    copy_data = [b"copied"]
    store_status = "OK"
    store_data = [b"label removed"]
    label_removed = False

    def __init__(self, host, port, *, timeout):
        self.calls = [("connect", host, port, timeout)]
        self.__class__.instances.append(self)

    def login(self, username, password):
        self.calls.append(("login", username, password))
        return "OK", [b"logged in"]

    def select(self, mailbox, readonly=False):
        self.calls.append(("select", mailbox, readonly))
        self.selected_mailbox = mailbox
        return "OK", [b"1"]

    def uid(self, command, *args):
        self.calls.append(("uid", command, *args))
        if command == "SEARCH":
            if self.selected_mailbox == "Virgilio/da-traghettare" and self.label_removed:
                return "OK", [b""]
            return "OK", [b"42"]
        if command == "COPY":
            return self.copy_status, self.copy_data
        if command == "STORE":
            if self.store_status == "OK":
                self.__class__.label_removed = True
            return self.store_status, self.store_data
        return "OK", [(b"42 (BODY[] {1})", eml_bytes()), b")"]

    def list(self, directory='""', pattern='*'):
        self.calls.append(("list", directory, pattern))
        return "OK", list(self.list_data)

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
        FakeImapClient.list_data = [b'(\\HasNoChildren) "/" "Virgilio/traghettate"']
        FakeImapClient.copy_status = "OK"
        FakeImapClient.copy_data = [b"copied"]
        FakeImapClient.store_status = "OK"
        FakeImapClient.store_data = [b"label removed"]
        FakeImapClient.label_removed = False
        self.temp = tempfile.TemporaryDirectory()
        self.adapter = ImapReadonlyMailbox(
            ImapReadonlyConfig("imap.example.invalid", "test-user", "test-password"),
            Path(self.temp.name), client_factory=FakeImapClient)
        self.completion = ImapCompletionMailbox(
            ImapReadonlyConfig("imap.example.invalid", "test-user", "test-password"),
            done_folder="Virgilio/traghettate",
            client_factory=FakeImapClient,
        )

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

    def test_uidvalidity_is_read_once_and_reused_for_all_session_messages(self):
        class ConsumableUidValidityClient(FakeImapClient):
            def uid(self, command, *args):
                if command == "SEARCH":
                    self.calls.append(("uid", command, *args))
                    return "OK", [b"42 43"]
                return super().uid(command, *args)

            def response(self, name):
                self.calls.append(("response", name))
                reads = sum(1 for call in self.calls if call == ("response", name))
                return ("UIDVALIDITY", [b"12345"]) if reads == 1 else (name, None)

        adapter = ImapReadonlyMailbox(
            ImapReadonlyConfig("imap.example.invalid", "test-user", "test-password"),
            Path(self.temp.name), client_factory=ConsumableUidValidityClient,
        )

        references = adapter.list_pending()
        calls = ConsumableUidValidityClient.instances[-1].calls

        self.assertEqual([item.uidvalidity for item in references], ["12345", "12345"])
        self.assertEqual(calls.count(("response", "UIDVALIDITY")), 1)

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

    def test_completion_copy_uses_exact_done_folder_when_safe(self):
        self.completion.add_done_label_only("42")
        calls = [call for client in FakeImapClient.instances for call in client.calls]
        self.assertIn(("list", '""', "*"), calls)
        self.assertIn(("select", "Virgilio/da-traghettare", False), calls)
        self.assertIn(("uid", "COPY", "42", "Virgilio/traghettate"), calls)
        texts = [str(call).upper() for call in calls]
        for forbidden in ("STORE", "DELETE", "EXPUNGE", "MOVE", "SEEN"):
            self.assertFalse(any(forbidden in item for item in texts))

    def test_completion_quotes_nested_mailbox_with_spaces(self):
        FakeImapClient.list_data = [b'(\\HasNoChildren) "/" "Virgilio/Pratica chiusa"']
        completion = ImapCompletionMailbox(
            ImapReadonlyConfig("imap.example.invalid", "test-user", "test-password"),
            done_folder="Virgilio/Pratica chiusa",
            client_factory=FakeImapClient,
        )
        completion.add_done_label_only("42")
        calls = [call for client in FakeImapClient.instances for call in client.calls]
        self.assertIn(("uid", "COPY", "42", '"Virgilio/Pratica chiusa"'), calls)

    def test_completion_blocks_copy_when_done_folder_missing_from_list(self):
        FakeImapClient.list_data = [b'(\\HasNoChildren) "/" "Virgilio/altro"']
        with self.assertRaises(ImapCompletionError) as ctx:
            self.completion.add_done_label_only("42")
        message = str(ctx.exception)
        self.assertIn("done_folder_not_found_in_imap_list", message)
        self.assertIn("Virgilio/traghettate", message)
        calls = [call for client in FakeImapClient.instances for call in client.calls]
        self.assertFalse(any(call[:2] == ("uid", "COPY") for call in calls))

    def test_completion_copy_failure_includes_diagnostics(self):
        FakeImapClient.copy_status = "NO"
        FakeImapClient.copy_data = [b"[TRYCREATE] mailbox not available"]
        with self.assertRaises(ImapCompletionError) as ctx:
            self.completion.add_done_label_only("42")
        message = str(ctx.exception)
        self.assertIn("UID COPY DONE failed", message)
        self.assertIn("imap_status=NO", message)
        self.assertIn("Virgilio/traghettate", message)
        self.assertIn("TRYCREATE", message)
        self.assertIn("Mostra in IMAP", message)

    def test_completion_move_adds_done_and_removes_only_input_label(self):
        FakeImapClient.list_data = [
            b'(\\HasNoChildren) "/" "Virgilio/da-traghettare"',
            b'(\\HasNoChildren) "/" "Virgilio/traghettate"',
        ]
        self.completion.move_to_done_label("42", "<readonly@example.invalid>")
        calls = [call for client in FakeImapClient.instances for call in client.calls]
        self.assertIn(("select", "Virgilio/da-traghettare", False), calls)
        self.assertIn(("uid", "COPY", "42", "Virgilio/traghettate"), calls)
        self.assertIn(("uid", "STORE", "42", "-X-GM-LABELS",
                       "(Virgilio/da-traghettare)"), calls)
        self.assertIn(("select", "Virgilio/da-traghettare", True), calls)
        self.assertIn(("select", "Virgilio/traghettate", True), calls)
        texts = [str(call).upper() for call in calls]
        for forbidden in ("DELETE", "EXPUNGE", "MOVE", "\\DELETED"):
            self.assertFalse(any(forbidden in item for item in texts))

    def test_completion_move_stops_if_source_label_removal_fails(self):
        FakeImapClient.list_data = [
            b'(\\HasNoChildren) "/" "Virgilio/da-traghettare"',
            b'(\\HasNoChildren) "/" "Virgilio/traghettate"',
        ]
        FakeImapClient.store_status = "NO"
        FakeImapClient.store_data = [b"extension unavailable"]
        with self.assertRaises(ImapCompletionError) as ctx:
            self.completion.move_to_done_label("42", "<readonly@example.invalid>")
        self.assertIn("UID STORE REMOVE INPUT LABEL failed", str(ctx.exception))

    def test_completion_move_rejects_unverified_postcondition(self):
        FakeImapClient.list_data = [
            b'(\\HasNoChildren) "/" "Virgilio/da-traghettare"',
            b'(\\HasNoChildren) "/" "Virgilio/traghettate"',
        ]
        original_uid = FakeImapClient.uid

        def uid_without_removal(client, command, *args):
            if command == "STORE":
                client.calls.append(("uid", command, *args))
                return "OK", [b"claimed removal"]
            return original_uid(client, command, *args)

        FakeImapClient.uid = uid_without_removal
        try:
            with self.assertRaises(ImapCompletionError) as ctx:
                self.completion.move_to_done_label("42", "<readonly@example.invalid>")
        finally:
            FakeImapClient.uid = original_uid
        self.assertIn("postcondition", str(ctx.exception))

    def test_completion_move_requires_distinct_existing_folders(self):
        completion = ImapCompletionMailbox(
            ImapReadonlyConfig(
                "imap.example.invalid", "test-user", "test-password",
                mailbox="Virgilio/traghettate",
            ),
            done_folder="Virgilio/traghettate",
            client_factory=FakeImapClient,
        )
        with self.assertRaises(ImapCompletionError) as ctx:
            completion.move_to_done_label("42", "<readonly@example.invalid>")
        self.assertIn("must be different", str(ctx.exception))
        calls = [call for client in FakeImapClient.instances for call in client.calls]
        self.assertFalse(any(call[:2] == ("uid", "COPY") for call in calls))


if __name__ == "__main__":
    unittest.main()
