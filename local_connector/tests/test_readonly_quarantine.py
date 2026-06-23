from pathlib import Path
import sqlite3

import pytest

from virgilio_connector.imap_readonly import DetectedAttachment
from virgilio_connector.local_paths import LocalDataPaths
from virgilio_connector.ports import MessageReference
from virgilio_connector.readonly_quarantine import ReadonlyQuarantineRunner
from virgilio_connector.scanner import LocalScanResult, ScanVerdict


class FakeReadonlyMailbox:
    def __init__(self, attachments):
        self.message = MessageReference("Virgilio/da-traghettare", "123", "42",
            "<test@example.invalid>", "Synthetic subject", "sender@example.invalid",
            "2026-06-23T10:00:00+02:00")
        self.attachments = tuple(attachments)
        self.mutating_calls = []

    def list_pending(self):
        return (self.message,)

    def detect_attachments(self, message):
        return self.attachments

    def acknowledge(self, message):
        self.mutating_calls.append("acknowledge")
        raise AssertionError("must never be called")


def attachment(filename, payload=b"content", mime="application/octet-stream", ordinal=1):
    return DetectedAttachment(ordinal, filename, mime, payload)


class FakeScanner:
    def __init__(self, verdict):
        self.verdict = verdict

    @property
    def available(self):
        return True

    def scan(self, path):
        return LocalScanResult("fake", self.verdict, f"fake {self.verdict.value}")


def run(tmp_path, attachments, *, dry_run=False, max_bytes=1024, scanner=None):
    mailbox = FakeReadonlyMailbox(attachments)
    paths = LocalDataPaths(tmp_path / ".local_data")
    result = ReadonlyQuarantineRunner(mailbox=mailbox, paths=paths,
        max_attachment_bytes=max_bytes, scanner=scanner).run(dry_run=dry_run)
    return result, paths, mailbox


@pytest.mark.parametrize("filename,mime", [
    ("report.pdf", "application/pdf"),
    ("photo.jpg", "image/jpeg"),
    ("scan.png", "image/png"),
])
def test_allowed_pdf_and_images_are_quarantined(tmp_path, filename, mime):
    result, paths, _ = run(tmp_path, [attachment(filename, mime=mime)])
    assert result[0].decision == "quarantined_unverified"
    assert result[0].saved is True
    assert len(list(paths.incoming.rglob(f"*{filename}"))) == 1


@pytest.mark.parametrize("filename", ["archive.zip", "payload.exe", "macro.docm"])
def test_forbidden_extensions_are_not_saved(tmp_path, filename):
    result, paths, _ = run(tmp_path, [attachment(filename)])
    assert result[0].decision == "rejected_by_extension"
    assert not list(paths.incoming.rglob("*.*"))


@pytest.mark.parametrize("filename", ["document.docx", "sheet.xlsx", "slides.pptx"])
def test_office_without_macros_is_not_automatically_allowed(tmp_path, filename):
    result, paths, _ = run(tmp_path, [attachment(filename)])
    assert result[0].decision == "rejected_by_extension"
    assert not list(paths.incoming.rglob("*.*"))


def test_attachment_without_name_is_rejected(tmp_path):
    result, _, _ = run(tmp_path, [attachment(None)])
    assert result[0].decision == "rejected_by_extension"
    assert result[0].sanitized_filename is None


def test_problematic_filename_is_sanitized(tmp_path):
    result, paths, _ = run(tmp_path, [attachment("../bad:name?.pdf")])
    assert result[0].sanitized_filename == "bad_name.pdf"
    assert len(list(paths.incoming.rglob("*bad_name.pdf"))) == 1


def test_duplicate_sha256_reuses_first_file(tmp_path):
    items = [attachment("first.pdf", b"same", ordinal=1),
             attachment("second.pdf", b"same", ordinal=2)]
    result, paths, _ = run(tmp_path, items)
    assert [item.saved for item in result] == [True, False]
    assert len([p for p in paths.incoming.rglob("*") if p.is_file()]) == 1
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT COUNT(*) FROM attachments").fetchone()[0] == 2
        assert db.execute("SELECT duplicate_of_id FROM attachments WHERE ordinal=2").fetchone()[0]


def test_dry_run_writes_no_files_or_database(tmp_path):
    result, paths, _ = run(tmp_path, [attachment("report.pdf")], dry_run=True)
    assert result[0].saved is False
    assert not paths.root.exists()


def test_size_limit_rejects_attachment(tmp_path):
    result, _, _ = run(tmp_path, [attachment("large.pdf", b"12345")], max_bytes=4)
    assert result[0].decision == "rejected_by_size"


def test_sqlite_records_message_and_attachment_metadata(tmp_path):
    _, paths, mailbox = run(tmp_path, [attachment("report.pdf", b"abc", "application/pdf")])
    with sqlite3.connect(paths.state_db) as db:
        row = db.execute("""SELECT m.message_uid,m.message_id,m.subject,m.sender,m.message_date,
            a.declared_mime_type,a.size_bytes,a.sha256,a.status
            FROM messages m JOIN attachments a ON a.message_id=m.id""").fetchone()
    assert row[:5] == ("42", mailbox.message.message_id, mailbox.message.subject,
                       mailbox.message.sender, mailbox.message.date)
    assert row[5] == "application/pdf"
    assert row[6] == 3
    assert len(row[7]) == 64
    assert row[8] == "quarantined_unverified"


def test_pipeline_never_invokes_mailbox_mutation(tmp_path):
    _, _, mailbox = run(tmp_path, [attachment("report.pdf")])
    assert mailbox.mutating_calls == []


def test_clean_scanner_promotes_to_ready_for_caronte(tmp_path):
    result, paths, _ = run(tmp_path, [attachment("report.pdf")],
                           scanner=FakeScanner(ScanVerdict.CLEAN))
    assert result[0].decision == "ready_for_caronte"
    assert len([p for p in paths.ready.rglob("*") if p.is_file()]) == 1
    assert not [p for p in paths.incoming.rglob("*") if p.is_file()]


def test_infected_scanner_rejects_attachment(tmp_path):
    result, paths, _ = run(tmp_path, [attachment("report.pdf")],
                           scanner=FakeScanner(ScanVerdict.INFECTED))
    assert result[0].decision == "rejected_by_scanner"
    assert len([p for p in paths.rejected.rglob("*") if p.is_file()]) == 1


def test_unverified_scanner_never_promotes_to_caronte(tmp_path):
    result, paths, _ = run(tmp_path, [attachment("report.pdf")])
    assert result[0].decision == "quarantined_unverified"
    with sqlite3.connect(paths.state_db) as db:
        assert db.execute("SELECT COUNT(*) FROM attachments WHERE status='ready_for_caronte'").fetchone()[0] == 0
