from __future__ import annotations

import unittest

from virgilio_connector.models import QuarantineStatus
from virgilio_connector.quarantine import InvalidTransition, QuarantineRecord


class QuarantineStateTests(unittest.TestCase):
    def test_happy_path_to_uploaded_limbo(self) -> None:
        record = QuarantineRecord.downloaded("att-0001")
        record = record.transition(
            QuarantineStatus.QUARANTINED,
            reason="isolated in local quarantine",
        )
        record = record.transition(
            QuarantineStatus.READY_FOR_CARONTE,
            reason="policy and scanner requirements satisfied",
        )
        record = record.transition(
            QuarantineStatus.UPLOADED_TO_LIMBO,
            reason="Caronte returned a Drive file id",
        )

        self.assertEqual(record.status, QuarantineStatus.UPLOADED_TO_LIMBO)

    def test_direct_upload_from_downloaded_is_forbidden(self) -> None:
        record = QuarantineRecord.downloaded("att-0001")

        with self.assertRaises(InvalidTransition):
            record.transition(
                QuarantineStatus.UPLOADED_TO_LIMBO,
                reason="invalid shortcut",
            )

    def test_scan_failure_can_return_to_quarantine(self) -> None:
        record = QuarantineRecord.downloaded("att-0001")
        record = record.transition(QuarantineStatus.QUARANTINED, reason="isolated")
        record = record.transition(QuarantineStatus.SCAN_FAILED, reason="scanner absent")
        record = record.transition(QuarantineStatus.QUARANTINED, reason="retry requested")

        self.assertEqual(record.status, QuarantineStatus.QUARANTINED)

    def test_terminal_state_cannot_transition(self) -> None:
        record = QuarantineRecord.downloaded("att-0001")
        record = record.transition(QuarantineStatus.QUARANTINED, reason="isolated")
        record = record.transition(QuarantineStatus.REJECTED, reason="extension denied")

        with self.assertRaises(InvalidTransition):
            record.transition(QuarantineStatus.QUARANTINED, reason="not allowed")


if __name__ == "__main__":
    unittest.main()
