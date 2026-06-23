from __future__ import annotations

import json
import unittest

from fixtures import clone, command_payload, response_payload
from virgilio_connector.ack import evaluate_ack
from virgilio_connector.contract import command_from_json, response_from_json


class AckPolicyTests(unittest.TestCase):
    def _decision(self, command_data=None, response_data=None, **kwargs):
        command = command_from_json(json.dumps(command_data or command_payload()))
        response = response_from_json(json.dumps(response_data or response_payload()))
        return evaluate_ack(command, response, **kwargs)

    def test_ack_is_allowed_after_confirmed_drive_upload(self) -> None:
        decision = self._decision()

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.acknowledged_attachment_ids, ("att-0001",))

    def test_dry_run_is_never_acknowledged(self) -> None:
        decision = self._decision(command_data=command_payload(dry_run=True))

        self.assertFalse(decision.allowed)
        self.assertIn("dry_run", decision.reason)

    def test_missing_drive_id_blocks_ack(self) -> None:
        response = clone(response_payload())
        response["limbo_drive_ids"] = []

        decision = self._decision(response_data=response)

        self.assertFalse(decision.allowed)
        self.assertIn("Drive id", decision.reason)

    def test_hash_mismatch_blocks_ack(self) -> None:
        response = clone(response_payload())
        response["accepted_attachments"][0]["sha256"] = "b" * 64

        decision = self._decision(response_data=response)

        self.assertFalse(decision.allowed)
        self.assertIn("hash", decision.reason)

    def test_partial_success_is_blocked_by_default(self) -> None:
        response = clone(response_payload())
        response["rejected_attachments"] = [
            {
                "local_temp_id": "att-0002",
                "code": "TYPE_REJECTED",
                "message": "Synthetic rejection",
            }
        ]

        decision = self._decision(response_data=response)

        self.assertFalse(decision.allowed)
        self.assertIn("partial", decision.reason)

    def test_partial_success_requires_explicit_opt_in(self) -> None:
        response = clone(response_payload())
        response["rejected_attachments"] = [
            {
                "local_temp_id": "att-0002",
                "code": "TYPE_REJECTED",
                "message": "Synthetic rejection",
            }
        ]

        decision = self._decision(response_data=response, allow_partial=True)

        self.assertTrue(decision.allowed)


if __name__ == "__main__":
    unittest.main()
