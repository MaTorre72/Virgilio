"""SQLite state dedicated to the reversible read-only quarantine probe."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


ATTACHMENT_STATES = (
    "detected", "rejected_by_extension", "rejected_by_size", "downloaded",
    "quarantined", "ready_for_scan", "error",
)


class ReadonlyStateStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                PRAGMA foreign_keys=ON;
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY, started_at TEXT NOT NULL,
                    completed_at TEXT, dry_run INTEGER NOT NULL,
                    status TEXT NOT NULL, messages_seen INTEGER NOT NULL DEFAULT 0,
                    attachments_seen INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES runs(id),
                    mailbox TEXT NOT NULL, uidvalidity TEXT, message_uid TEXT NOT NULL,
                    message_id TEXT, subject TEXT NOT NULL, sender TEXT NOT NULL,
                    message_date TEXT NOT NULL,
                    UNIQUE(run_id, mailbox, uidvalidity, message_uid)
                );
                CREATE TABLE IF NOT EXISTS attachments (
                    id INTEGER PRIMARY KEY, message_id INTEGER NOT NULL REFERENCES messages(id),
                    ordinal INTEGER NOT NULL, original_filename TEXT,
                    sanitized_filename TEXT, declared_mime_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN (
                        'detected','rejected_by_extension','rejected_by_size','downloaded',
                        'quarantined','ready_for_scan','error')),
                    relative_path TEXT, duplicate_of_id INTEGER REFERENCES attachments(id),
                    reason TEXT NOT NULL, created_at TEXT NOT NULL,
                    UNIQUE(message_id, ordinal)
                );
            """)

    def start_run(self) -> int:
        with self._connection() as db:
            cursor = db.execute("INSERT INTO runs(started_at,dry_run,status) VALUES(?,0,'running')",
                                (_now(),))
            return int(cursor.lastrowid)

    def add_message(self, run_id: int, message) -> int:
        with self._connection() as db:
            cursor = db.execute("""INSERT INTO messages(
                run_id,mailbox,uidvalidity,message_uid,message_id,subject,sender,message_date
                ) VALUES(?,?,?,?,?,?,?,?)""", (run_id, message.mailbox, message.uidvalidity,
                message.message_uid, message.message_id or None, message.subject,
                message.sender, message.date))
            return int(cursor.lastrowid)

    def add_attachment(self, message_id: int, *, ordinal: int, original_filename: str | None,
                       sanitized_filename: str | None, declared_mime_type: str,
                       size_bytes: int, sha256: str, status: str, relative_path: str | None,
                       duplicate_of_id: int | None, reason: str) -> int:
        if status not in ATTACHMENT_STATES:
            raise ValueError(f"invalid attachment status: {status}")
        with self._connection() as db:
            cursor = db.execute("""INSERT INTO attachments(
                message_id,ordinal,original_filename,sanitized_filename,declared_mime_type,
                size_bytes,sha256,status,relative_path,duplicate_of_id,reason,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (message_id, ordinal, original_filename,
                sanitized_filename, declared_mime_type, size_bytes, sha256, status,
                relative_path, duplicate_of_id, reason, _now()))
            return int(cursor.lastrowid)

    def find_by_sha256(self, sha256: str):
        with self._connection() as db:
            return db.execute("""SELECT id, relative_path FROM attachments
                WHERE sha256=? AND status='ready_for_scan' AND relative_path IS NOT NULL
                ORDER BY id LIMIT 1""", (sha256,)).fetchone()

    def complete_run(self, run_id: int, *, messages_seen: int, attachments_seen: int,
                     status: str = "completed") -> None:
        with self._connection() as db:
            db.execute("""UPDATE runs SET completed_at=?,status=?,messages_seen=?,attachments_seen=?
                WHERE id=?""", (_now(), status, messages_seen, attachments_seen, run_id))

    @contextmanager
    def _connection(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        finally:
            db.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
