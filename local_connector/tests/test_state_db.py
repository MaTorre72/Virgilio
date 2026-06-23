from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from virgilio_connector.models import QuarantineStatus
from virgilio_connector.quarantine import InvalidTransition
from virgilio_connector.state_db import (
    DATABASE_SCHEMA_VERSION,
    StateConflictError,
    StateStore,
    UnsupportedSchemaError,
)
from virgilio_connector.state_models import (
    CommandAttemptStatus,
    MessageStatus,
    NewAttachment,
    NewMessage,
)


DIGEST = "a" * 64
REQUEST_DIGEST = "b" * 64


def new_message(**overrides) -> NewMessage:
    values = {
        "account_alias": "test-user",
        "mailbox": "Virgilio/da-traghettare",
        "mailbox_uidvalidity": "100",
        "message_uid": "42",
        "message_id": "<message@example.invalid>",
        "thread_id": None,
        "subject": "Synthetic subject",
        "sender": "sender@example.invalid",
        "message_date": "2026-06-23T10:00:00+02:00",
    }
    values.update(overrides)
    return NewMessage(**values)


def new_attachment(message_row_id: int, **overrides) -> NewAttachment:
    values = {
        "message_row_id": message_row_id,
        "local_temp_id": "att-0001",
        "local_relative_path": "cmd-test/att-0001/document.pdf",
        "original_filename": "document.pdf",
        "sanitized_filename": "document.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 1024,
        "sha256": DIGEST,
    }
    values.update(overrides)
    return NewAttachment(**values)


class StateStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "state.db"
        self.store = StateStore(self.db_path)
        self.store.initialize()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_initialization_is_idempotent_and_integrity_is_ok(self) -> None:
        self.store.initialize()

        self.assertEqual(self.store.schema_version(), DATABASE_SCHEMA_VERSION)
        self.assertTrue(self.store.integrity_check())

        connection = sqlite3.connect(self.db_path)
        try:
            mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(mode.lower(), "wal")

    def test_schema_has_no_obvious_secret_columns(self) -> None:
        connection = sqlite3.connect(self.db_path)
        try:
            rows = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        finally:
            connection.close()
        schema = " ".join(str(row[0]).lower() for row in rows)

        for forbidden in ("password", "oauth", "access_token", "refresh_token"):
            self.assertNotIn(forbidden, schema)

    def test_register_message_is_idempotent_for_imap_identity(self) -> None:
        first = self.store.register_message(new_message(subject="First"))
        second = self.store.register_message(new_message(subject="Updated"))

        self.assertEqual(first.id, second.id)
        self.assertEqual(second.subject, "Updated")
        self.assertEqual(second.status, MessageStatus.DISCOVERED)
        self.assertEqual(len(self.store.list_events("message", first.id)), 1)

    def test_uidvalidity_separates_reused_uids(self) -> None:
        first = self.store.register_message(new_message(mailbox_uidvalidity="100"))
        second = self.store.register_message(new_message(mailbox_uidvalidity="101"))

        self.assertNotEqual(first.id, second.id)

    def test_attachment_registration_is_idempotent(self) -> None:
        message = self.store.register_message(new_message())
        first = self.store.add_attachment(new_attachment(message.id))
        second = self.store.add_attachment(new_attachment(message.id))

        self.assertEqual(first.id, second.id)
        self.assertEqual(first.quarantine_status, QuarantineStatus.DOWNLOADED)

    def test_attachment_id_conflict_is_rejected(self) -> None:
        message = self.store.register_message(new_message())
        self.store.add_attachment(new_attachment(message.id))

        with self.assertRaises(StateConflictError):
            self.store.add_attachment(new_attachment(message.id, sha256="c" * 64))

    def test_attachment_transition_is_atomic_and_audited(self) -> None:
        message = self.store.register_message(new_message())
        attachment = self.store.add_attachment(new_attachment(message.id))
        quarantined = self.store.transition_attachment(
            attachment.local_temp_id,
            QuarantineStatus.QUARANTINED,
            reason="isolated locally",
        )
        ready = self.store.transition_attachment(
            attachment.local_temp_id,
            QuarantineStatus.READY_FOR_CARONTE,
            reason="scanner requirements satisfied",
            scan_engine="synthetic-scanner",
            scan_result="clean",
        )

        self.assertEqual(quarantined.quarantine_status, QuarantineStatus.QUARANTINED)
        self.assertEqual(ready.scan_result, "clean")
        events = self.store.list_events("attachment", attachment.id)
        self.assertEqual(
            [event.new_state for event in events],
            ["downloaded", "quarantined", "ready_for_caronte"],
        )

    def test_invalid_attachment_transition_keeps_previous_state(self) -> None:
        message = self.store.register_message(new_message())
        attachment = self.store.add_attachment(new_attachment(message.id))

        with self.assertRaises(InvalidTransition):
            self.store.transition_attachment(
                attachment.local_temp_id,
                QuarantineStatus.UPLOADED_TO_LIMBO,
                reason="invalid shortcut",
                drive_file_id="drive-test",
            )

        persisted = self.store.get_attachment(attachment.local_temp_id)
        self.assertEqual(persisted.quarantine_status, QuarantineStatus.DOWNLOADED)
        self.assertIsNone(persisted.drive_file_id)

    def test_uploaded_state_requires_drive_file_id(self) -> None:
        message = self.store.register_message(new_message())
        attachment = self.store.add_attachment(new_attachment(message.id))
        self.store.transition_attachment(
            attachment.local_temp_id,
            QuarantineStatus.QUARANTINED,
            reason="isolated",
        )
        self.store.transition_attachment(
            attachment.local_temp_id,
            QuarantineStatus.READY_FOR_CARONTE,
            reason="ready",
        )

        with self.assertRaises(StateConflictError):
            self.store.transition_attachment(
                attachment.local_temp_id,
                QuarantineStatus.UPLOADED_TO_LIMBO,
                reason="missing Drive confirmation",
            )

    def test_message_ack_requires_uploaded_attachment(self) -> None:
        message = self.store.register_message(new_message())
        for status, reason in (
            (MessageStatus.QUARANTINED, "isolated"),
            (MessageStatus.READY, "ready"),
            (MessageStatus.SUBMITTING, "submitted"),
        ):
            message = self.store.transition_message(message.id, status, reason=reason)
        message = self.store.transition_message(
            message.id,
            MessageStatus.ACK_PENDING,
            reason="response received",
            command_id="cmd-test",
        )

        with self.assertRaises(StateConflictError):
            self.store.transition_message(
                message.id, MessageStatus.ACKNOWLEDGED, reason="invalid ack"
            )

    def test_complete_workflow_can_be_acknowledged(self) -> None:
        message = self.store.register_message(new_message())
        attachment = self.store.add_attachment(new_attachment(message.id))
        self.store.transition_attachment(
            attachment.local_temp_id, QuarantineStatus.QUARANTINED, reason="isolated"
        )
        self.store.transition_attachment(
            attachment.local_temp_id, QuarantineStatus.READY_FOR_CARONTE, reason="ready"
        )
        self.store.transition_attachment(
            attachment.local_temp_id,
            QuarantineStatus.UPLOADED_TO_LIMBO,
            reason="Caronte confirmed upload",
            drive_file_id="drive-test-1",
            bucoliche_row_reference="row-test-1",
        )
        for status, reason in (
            (MessageStatus.QUARANTINED, "isolated"),
            (MessageStatus.READY, "ready"),
            (MessageStatus.SUBMITTING, "submitted"),
        ):
            message = self.store.transition_message(message.id, status, reason=reason)
        message = self.store.transition_message(
            message.id,
            MessageStatus.ACK_PENDING,
            reason="response validated",
            command_id="cmd-test",
        )
        message = self.store.transition_message(
            message.id, MessageStatus.ACKNOWLEDGED, reason="future IMAP ack confirmed"
        )

        self.assertEqual(message.status, MessageStatus.ACKNOWLEDGED)
        self.assertIsNotNone(message.acknowledged_at)

    def test_command_attempts_are_numbered_and_completed_once(self) -> None:
        message = self.store.register_message(new_message())
        first = self.store.start_command_attempt(
            message.id,
            command_id="cmd-test",
            dry_run=False,
            request_sha256=REQUEST_DIGEST,
        )
        first = self.store.complete_command_attempt(
            first.id,
            succeeded=False,
            response_ok=None,
            error_code="TEMPORARY_FAILURE",
            retryable=True,
        )
        second = self.store.start_command_attempt(
            message.id,
            command_id="cmd-test",
            dry_run=False,
            request_sha256=REQUEST_DIGEST,
        )
        second = self.store.complete_command_attempt(
            second.id,
            succeeded=True,
            response_ok=True,
            response_message="synthetic success",
        )

        self.assertEqual(first.status, CommandAttemptStatus.FAILED)
        self.assertEqual(second.status, CommandAttemptStatus.SUCCEEDED)
        self.assertEqual(second.attempt_number, 2)
        with self.assertRaises(StateConflictError):
            self.store.complete_command_attempt(
                second.id, succeeded=True, response_ok=True
            )


class UnsupportedSchemaTests(unittest.TestCase):
    def test_newer_schema_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.db"
            connection = sqlite3.connect(path)
            try:
                connection.execute("PRAGMA user_version = 99")
                connection.commit()
            finally:
                connection.close()

            with self.assertRaises(UnsupportedSchemaError):
                StateStore(path).initialize()


if __name__ == "__main__":
    unittest.main()
