from pathlib import Path
import sqlite3
from unittest.mock import patch

from virgilio_connector.scanner import (
    ScanVerdict,
    UnconfiguredScanner,
    WindowsDefenderScanner,
    select_scanner,
)
from virgilio_connector.readonly_state import ReadonlyStateStore


def test_unconfigured_scanner_is_conservatively_unverified(tmp_path):
    result = UnconfiguredScanner().scan(tmp_path / "document.pdf")
    assert result.verdict is ScanVerdict.UNVERIFIED


def test_defender_clean_exit_is_clean_and_disables_remediation(tmp_path):
    executable = tmp_path / "MpCmdRun.exe"
    executable.write_bytes(b"synthetic")
    document = tmp_path / "document.pdf"
    document.write_bytes(b"synthetic")
    scanner = WindowsDefenderScanner(executable)
    with patch("virgilio_connector.scanner.subprocess.run") as run:
        run.return_value.returncode = 0
        result = scanner.scan(document)
    assert result.verdict is ScanVerdict.CLEAN
    command = run.call_args.args[0]
    assert "-DisableRemediation" in command
    assert command[command.index("-File") + 1] == str(document)


def test_defender_nonzero_exit_is_never_interpreted_as_clean(tmp_path):
    executable = tmp_path / "MpCmdRun.exe"
    executable.write_bytes(b"synthetic")
    document = tmp_path / "document.pdf"
    document.write_bytes(b"synthetic")
    scanner = WindowsDefenderScanner(executable)
    with patch("virgilio_connector.scanner.subprocess.run") as run:
        run.return_value.returncode = 2
        result = scanner.scan(document)
    assert result.verdict is ScanVerdict.UNVERIFIED


def test_clamav_mode_keeps_abstract_unconfigured_boundary():
    scanner = select_scanner("clamav")
    assert scanner.available is False
    assert "ClamAV" in scanner.reason


def test_existing_ready_for_scan_rows_migrate_to_unverified(tmp_path):
    path = tmp_path / "state.db"
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE messages(id INTEGER PRIMARY KEY);
            CREATE TABLE attachments(
                id INTEGER PRIMARY KEY, message_id INTEGER NOT NULL REFERENCES messages(id),
                ordinal INTEGER NOT NULL, original_filename TEXT, sanitized_filename TEXT,
                declared_mime_type TEXT NOT NULL, size_bytes INTEGER NOT NULL,
                sha256 TEXT NOT NULL, status TEXT NOT NULL, relative_path TEXT,
                duplicate_of_id INTEGER, reason TEXT NOT NULL, created_at TEXT NOT NULL,
                UNIQUE(message_id, ordinal));
            INSERT INTO messages(id) VALUES(1);
            INSERT INTO attachments VALUES(
                1,1,1,'test.pdf','test.pdf','application/pdf',4,
                'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                'ready_for_scan','quarantine/incoming/test.pdf',NULL,'old','2026-06-23');
        """)
    ReadonlyStateStore(path).initialize()
    with sqlite3.connect(path) as db:
        row = db.execute("SELECT status,scanner_engine FROM attachments").fetchone()
    assert row == ("quarantined_unverified", None)
