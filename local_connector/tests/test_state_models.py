from __future__ import annotations

import unittest

from virgilio_connector.state_models import NewAttachment


BASE_VALUES = {
    "message_row_id": 1,
    "local_temp_id": "att-0001",
    "local_relative_path": "cmd-test/att-0001/document.pdf",
    "original_filename": "document.pdf",
    "sanitized_filename": "document.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 1024,
    "sha256": "a" * 64,
}


class PersistentModelTests(unittest.TestCase):
    def test_windows_absolute_path_is_rejected(self) -> None:
        values = {**BASE_VALUES, "local_relative_path": r"C:\temp\document.pdf"}

        with self.assertRaisesRegex(ValueError, "quarantine root"):
            NewAttachment(**values)

    def test_posix_absolute_path_is_rejected(self) -> None:
        values = {**BASE_VALUES, "local_relative_path": "/tmp/document.pdf"}

        with self.assertRaisesRegex(ValueError, "quarantine root"):
            NewAttachment(**values)

    def test_parent_traversal_is_rejected(self) -> None:
        values = {**BASE_VALUES, "local_relative_path": "cmd/../document.pdf"}

        with self.assertRaisesRegex(ValueError, "quarantine root"):
            NewAttachment(**values)


if __name__ == "__main__":
    unittest.main()
