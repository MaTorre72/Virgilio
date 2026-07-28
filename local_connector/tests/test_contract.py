from __future__ import annotations

import json
import unittest

from fixtures import clone, command_payload, response_payload
from virgilio_connector.contract import (
    command_from_json,
    command_to_json,
    response_from_json,
    response_to_json,
)
from virgilio_connector.models import ContractValidationError, QuarantineStatus


class CommandContractTests(unittest.TestCase):
    def test_command_round_trip(self) -> None:
        command = command_from_json(json.dumps(command_payload()))

        self.assertEqual(command.connector_type, "local_imap")
        self.assertEqual(command.sender, "sender@example.invalid")
        self.assertEqual(
            command.attachments[0].quarantine_status,
            QuarantineStatus.READY_FOR_CARONTE,
        )
        self.assertEqual(
            command_from_json(command_to_json(command)).to_dict(), command.to_dict()
        )

    def test_operational_command_requires_confirmation(self) -> None:
        payload = clone(command_payload())
        payload["user_confirmed_command"] = False

        with self.assertRaisesRegex(ContractValidationError, "must be true"):
            command_from_json(json.dumps(payload))

    def test_operational_command_rejects_non_ready_attachment(self) -> None:
        payload = clone(command_payload())
        payload["attachments"][0]["quarantine_status"] = "quarantined"

        with self.assertRaisesRegex(ContractValidationError, "ready_for_caronte"):
            command_from_json(json.dumps(payload))

    def test_dry_run_can_describe_non_ready_attachment(self) -> None:
        payload = clone(command_payload(dry_run=True))
        payload["attachments"][0]["quarantine_status"] = "quarantined"

        command = command_from_json(json.dumps(payload))

        self.assertTrue(command.dry_run)

    def test_unknown_fields_are_rejected(self) -> None:
        payload = clone(command_payload())
        payload["password"] = "must-never-be-accepted"

        with self.assertRaisesRegex(ContractValidationError, "unknown fields"):
            command_from_json(json.dumps(payload))

    def test_datetime_requires_timezone(self) -> None:
        payload = clone(command_payload())
        payload["created_at"] = "2026-06-23T10:15:30"

        with self.assertRaisesRegex(ContractValidationError, "timezone"):
            command_from_json(json.dumps(payload))


class ResponseContractTests(unittest.TestCase):
    def test_response_round_trip(self) -> None:
        response = response_from_json(json.dumps(response_payload()))

        self.assertTrue(response.ok)
        self.assertEqual(
            response_from_json(response_to_json(response)).to_dict(), response.to_dict()
        )

    def test_duplicate_drive_ids_are_rejected(self) -> None:
        payload = clone(response_payload())
        payload["limbo_drive_ids"].append(payload["limbo_drive_ids"][0].copy())

        with self.assertRaisesRegex(ContractValidationError, "duplicate"):
            response_from_json(json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
