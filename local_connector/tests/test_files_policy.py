from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from virgilio_connector.files import sanitize_filename, sha256_file
from virgilio_connector.policy import AttachmentPolicy, PolicyDecision


class FileHelpersTests(unittest.TestCase):
    def test_sanitize_filename_removes_path_and_invalid_characters(self) -> None:
        result = sanitize_filename(r"..\unsafe folder\report:final?.pdf")

        self.assertEqual(result, "report_final.pdf")
        self.assertNotIn("/", result)
        self.assertNotIn("\\", result)

    def test_sanitize_filename_protects_windows_reserved_names(self) -> None:
        self.assertEqual(sanitize_filename("CON.txt"), "_CON.txt")

    def test_sha256_file_matches_standard_library(self) -> None:
        content = b"synthetic attachment content"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "attachment.bin"
            path.write_bytes(content)

            result = sha256_file(path, chunk_size=5)

        self.assertEqual(result, hashlib.sha256(content).hexdigest())


class AttachmentPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = AttachmentPolicy()

    def test_pdf_is_provisionally_allowed(self) -> None:
        self.assertEqual(
            self.policy.evaluate_filename("document.PDF").decision,
            PolicyDecision.ALLOW,
        )

    def test_executable_is_denied(self) -> None:
        self.assertEqual(
            self.policy.evaluate_filename("invoice.exe").decision,
            PolicyDecision.DENY,
        )

    def test_office_file_requires_review_until_decided(self) -> None:
        self.assertEqual(
            self.policy.evaluate_filename("report.docx").decision,
            PolicyDecision.REVIEW,
        )


if __name__ == "__main__":
    unittest.main()
