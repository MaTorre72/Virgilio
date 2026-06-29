"""SQLite state dedicated to the reversible read-only quarantine probe."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3


ATTACHMENT_STATES = (
    "detected", "rejected_by_extension", "rejected_by_size", "downloaded",
    "quarantined", "ready_for_scan", "quarantined_unverified",
    "ready_for_caronte", "rejected_by_scanner", "rejected_malware",
    "scan_failed", "staged_local_drive", "staged_storage",
    "staging_failed", "staging_conflict", "error",
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
                    attachments_seen INTEGER NOT NULL DEFAULT 0,
                    account_alias TEXT NOT NULL DEFAULT 'default'
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES runs(id),
                    account_alias TEXT NOT NULL DEFAULT 'default',
                    mailbox TEXT NOT NULL, uidvalidity TEXT, message_uid TEXT NOT NULL,
                    message_id TEXT, subject TEXT NOT NULL, sender TEXT NOT NULL,
                    message_date TEXT NOT NULL,
                    message_state TEXT NOT NULL DEFAULT 'open',
                    ack_attempted_at TEXT, ack_completed_at TEXT,
                    ack_strategy TEXT, ack_result TEXT,
                    completed_at TEXT, completion_report_path TEXT,
                    UNIQUE(run_id, account_alias, mailbox, uidvalidity, message_uid)
                );
                CREATE TABLE IF NOT EXISTS attachments (
                    id INTEGER PRIMARY KEY, message_id INTEGER NOT NULL REFERENCES messages(id),
                    account_alias TEXT NOT NULL DEFAULT 'default',
                    attachment_id TEXT,
                    source_email TEXT,
                    ordinal INTEGER NOT NULL, original_filename TEXT,
                    sanitized_filename TEXT, declared_mime_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN (
                        'detected','rejected_by_extension','rejected_by_size','downloaded',
                        'quarantined','ready_for_scan','quarantined_unverified',
                        'ready_for_caronte','rejected_by_scanner','rejected_malware',
                        'scan_failed','staged_local_drive','staged_storage',
                        'staging_failed','staging_conflict','error')),
                    relative_path TEXT, duplicate_of_id INTEGER REFERENCES attachments(id),
                    reason TEXT NOT NULL, scanner_engine TEXT,
                    scan_result TEXT, scanned_at TEXT, staged_filename TEXT,
                    staging_manifest_path TEXT, manifest_path TEXT,
                    storage_adapter TEXT, staged_path TEXT,
                    fingerprint TEXT,
                    staged_at TEXT, created_at TEXT NOT NULL,
                    UNIQUE(message_id, ordinal)
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY, created_at TEXT NOT NULL,
                    machine_id TEXT NOT NULL, account_alias TEXT NOT NULL,
                    entity_type TEXT NOT NULL, entity_id TEXT NOT NULL,
                    fingerprint TEXT, action TEXT NOT NULL, status TEXT NOT NULL,
                    details_json TEXT NOT NULL
                );
            """)
            columns = {row[1] for row in db.execute("PRAGMA table_info(attachments)")}
            if "scanner_engine" not in columns:
                self._migrate_attachments_v2(db)
            columns = {row[1] for row in db.execute("PRAGMA table_info(attachments)")}
            if "staged_filename" not in columns:
                self._migrate_attachments_v3(db)
            self._ensure_account_alias_columns(db)
            self._ensure_attachment_identity_columns(db)
            self._ensure_attachment_storage_states(db)
            self._ensure_attachment_identity_columns(db)

    def start_run(self, account_alias: str = "default") -> int:
        with self._connection() as db:
            cursor = db.execute("""INSERT INTO runs(started_at,dry_run,status,account_alias)
                VALUES(?,0,'running',?)""", (_now(), account_alias))
            return int(cursor.lastrowid)

    def add_message(self, run_id: int, message, account_alias: str = "default") -> int:
        with self._connection() as db:
            cursor = db.execute("""INSERT INTO messages(
                run_id,account_alias,mailbox,uidvalidity,message_uid,message_id,subject,sender,message_date
                ) VALUES(?,?,?,?,?,?,?,?,?)""", (run_id, account_alias, message.mailbox, message.uidvalidity,
                message.message_uid, message.message_id or None, message.subject,
                message.sender, message.date))
            return int(cursor.lastrowid)

    def add_attachment(self, message_id: int, *, ordinal: int, original_filename: str | None,
                       sanitized_filename: str | None, declared_mime_type: str,
                       size_bytes: int, sha256: str, status: str, relative_path: str | None,
                       duplicate_of_id: int | None, reason: str,
                       scanner_engine: str | None = None, scan_result: str | None = None,
                       account_alias: str = "default", attachment_id: str | None = None,
                       source_email: str | None = None, manifest_path: str | None = None) -> int:
        if status not in ATTACHMENT_STATES:
            raise ValueError(f"invalid attachment status: {status}")
        with self._connection() as db:
            cursor = db.execute("""INSERT INTO attachments(
                message_id,account_alias,attachment_id,source_email,
                ordinal,original_filename,sanitized_filename,declared_mime_type,
                size_bytes,sha256,status,relative_path,duplicate_of_id,reason,
                scanner_engine,scan_result,scanned_at,manifest_path,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (message_id, account_alias,
                attachment_id, source_email, ordinal, original_filename,
                sanitized_filename, declared_mime_type, size_bytes, sha256, status,
                relative_path, duplicate_of_id, reason, scanner_engine, scan_result,
                _now() if scanner_engine else None, manifest_path, _now()))
            return int(cursor.lastrowid)

    def set_fingerprint(self, attachment_row_id: int, fingerprint: str) -> None:
        with self._connection() as db:
            db.execute("UPDATE attachments SET fingerprint=? WHERE id=?", (fingerprint, attachment_row_id))

    def add_audit_event(self, *, machine_id: str, account_alias: str,
                        entity_type: str, entity_id: str, fingerprint: str | None,
                        action: str, status: str, details: dict | None = None) -> int:
        with self._connection() as db:
            cursor = db.execute("""INSERT INTO audit_events(created_at,machine_id,
                account_alias,entity_type,entity_id,fingerprint,action,status,details_json)
                VALUES(?,?,?,?,?,?,?,?,?)""", (_now(), machine_id, account_alias,
                entity_type, entity_id, fingerprint, action, status,
                json.dumps(details or {}, ensure_ascii=False, separators=(",", ":"))))
            return int(cursor.lastrowid)

    def find_by_attachment_id(self, attachment_id: str):
        with self._connection() as db:
            return db.execute("""SELECT id, sha256, status, relative_path, manifest_path
                FROM attachments WHERE attachment_id=? ORDER BY id LIMIT 1""",
                (attachment_id,)).fetchone()

    def find_by_sha256(self, sha256: str):
        with self._connection() as db:
            return db.execute("""SELECT id, relative_path, status FROM attachments
                WHERE sha256=? AND status IN ('quarantined_unverified','ready_for_caronte')
                  AND relative_path IS NOT NULL
                ORDER BY id LIMIT 1""", (sha256,)).fetchone()

    @staticmethod
    def _migrate_attachments_v2(db: sqlite3.Connection) -> None:
        db.executescript("""
            ALTER TABLE attachments RENAME TO attachments_v1;
            CREATE TABLE attachments (
                id INTEGER PRIMARY KEY, message_id INTEGER NOT NULL REFERENCES messages(id),
                ordinal INTEGER NOT NULL, original_filename TEXT,
                sanitized_filename TEXT, declared_mime_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN (
                    'detected','rejected_by_extension','rejected_by_size','downloaded',
                    'quarantined','ready_for_scan','quarantined_unverified',
                    'ready_for_caronte','rejected_by_scanner','error')),
                relative_path TEXT, duplicate_of_id INTEGER REFERENCES attachments(id),
                reason TEXT NOT NULL, scanner_engine TEXT, scan_result TEXT,
                scanned_at TEXT, created_at TEXT NOT NULL,
                UNIQUE(message_id, ordinal)
            );
            INSERT INTO attachments(
                id,message_id,ordinal,original_filename,sanitized_filename,
                declared_mime_type,size_bytes,sha256,status,relative_path,
                duplicate_of_id,reason,created_at)
            SELECT id,message_id,ordinal,original_filename,sanitized_filename,
                declared_mime_type,size_bytes,sha256,
                CASE WHEN status='ready_for_scan' THEN 'quarantined_unverified' ELSE status END,
                relative_path,duplicate_of_id,
                CASE WHEN status='ready_for_scan'
                     THEN 'migrated: no scanner evidence available' ELSE reason END,
                created_at
            FROM attachments_v1;
            DROP TABLE attachments_v1;
        """)

    def complete_run(self, run_id: int, *, messages_seen: int, attachments_seen: int,
                     status: str = "completed") -> None:
        with self._connection() as db:
            db.execute("""UPDATE runs SET completed_at=?,status=?,messages_seen=?,attachments_seen=?
                WHERE id=?""", (_now(), status, messages_seen, attachments_seen, run_id))

    def update_scan_by_sha256(self, sha256: str, *, status: str, relative_path: str,
                              scanner_engine: str, scan_result: str, reason: str) -> None:
        if status not in ATTACHMENT_STATES:
            raise ValueError(f"invalid attachment status: {status}")
        with self._connection() as db:
            db.execute("""UPDATE attachments SET status=?,relative_path=?,scanner_engine=?,
                scan_result=?,scanned_at=?,reason=? WHERE sha256=?""",
                (status, relative_path, scanner_engine, scan_result, _now(), reason, sha256))

    def update_staging(self, attachment_id: int, *, status: str, reason: str,
                       staged_filename: str | None = None,
                       manifest_path: str | None = None) -> None:
        if status not in {"staged_local_drive", "staging_failed"}:
            raise ValueError("invalid staging status")
        with self._connection() as db:
            db.execute("""UPDATE attachments SET status=?,reason=?,staged_filename=?,
                staging_manifest_path=?,staged_at=? WHERE id=?""",
                (status, reason, staged_filename, manifest_path, _now(), attachment_id))

    def update_storage(self, attachment_row_id: int, *, status: str, reason: str,
                       storage_adapter: str | None = None, staged_path: str | None = None,
                       staged_manifest_path: str | None = None,
                       staged_filename: str | None = None) -> None:
        if status not in {"staged_storage", "staging_failed", "staging_conflict"}:
            raise ValueError("invalid storage status")
        with self._connection() as db:
            db.execute("""UPDATE attachments SET status=?,reason=?,storage_adapter=?,
                staged_path=?,staging_manifest_path=?,staged_filename=?,staged_at=?
                WHERE id=?""", (status, reason, storage_adapter, staged_path,
                staged_manifest_path, staged_filename, _now(), attachment_row_id))

    def update_message_completion(self, message_row_id: int, *, message_state: str,
                                  ack_strategy: str | None, ack_result: str,
                                  report_path: str | None = None,
                                  attempted: bool = False,
                                  completed: bool = False) -> None:
        allowed = {"ready_for_ack", "acked", "ack_failed", "completed", "completion_skipped"}
        if message_state not in allowed:
            raise ValueError("invalid message_state")
        now = _now()
        with self._connection() as db:
            db.execute("""UPDATE messages SET message_state=?,ack_strategy=?,
                ack_result=?,completion_report_path=COALESCE(?,completion_report_path),
                ack_attempted_at=CASE WHEN ? THEN ? ELSE ack_attempted_at END,
                ack_completed_at=CASE WHEN ? THEN ? ELSE ack_completed_at END,
                completed_at=CASE WHEN ? THEN ? ELSE completed_at END
                WHERE id=?""", (message_state, ack_strategy, ack_result, report_path,
                1 if attempted else 0, now, 1 if completed else 0, now,
                1 if completed else 0, now, message_row_id))

    @staticmethod
    def _migrate_attachments_v3(db: sqlite3.Connection) -> None:
        db.executescript("""
            ALTER TABLE attachments RENAME TO attachments_v2;
            CREATE TABLE attachments (
                id INTEGER PRIMARY KEY, message_id INTEGER NOT NULL REFERENCES messages(id),
                ordinal INTEGER NOT NULL, original_filename TEXT,
                sanitized_filename TEXT, declared_mime_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN (
                    'detected','rejected_by_extension','rejected_by_size','downloaded',
                    'quarantined','ready_for_scan','quarantined_unverified',
                    'ready_for_caronte','rejected_by_scanner','rejected_malware',
                    'scan_failed','staged_local_drive','staged_storage',
                    'staging_failed','staging_conflict','error')),
                relative_path TEXT, duplicate_of_id INTEGER REFERENCES attachments(id),
                reason TEXT NOT NULL, scanner_engine TEXT, scan_result TEXT,
                scanned_at TEXT, staged_filename TEXT, staging_manifest_path TEXT,
                staged_at TEXT, created_at TEXT NOT NULL,
                UNIQUE(message_id, ordinal)
            );
            INSERT INTO attachments(
                id,message_id,ordinal,original_filename,sanitized_filename,
                declared_mime_type,size_bytes,sha256,status,relative_path,
                duplicate_of_id,reason,scanner_engine,scan_result,scanned_at,created_at)
            SELECT id,message_id,ordinal,original_filename,sanitized_filename,
                declared_mime_type,size_bytes,sha256,status,relative_path,
                duplicate_of_id,reason,scanner_engine,scan_result,scanned_at,created_at
            FROM attachments_v2;
            DROP TABLE attachments_v2;
        """)

    @staticmethod
    def _ensure_account_alias_columns(db: sqlite3.Connection) -> None:
        run_columns = {row[1] for row in db.execute("PRAGMA table_info(runs)")}
        if "account_alias" not in run_columns:
            db.execute("ALTER TABLE runs ADD COLUMN account_alias TEXT NOT NULL DEFAULT 'default'")
        message_columns = {row[1] for row in db.execute("PRAGMA table_info(messages)")}
        if "account_alias" not in message_columns:
            db.execute("ALTER TABLE messages ADD COLUMN account_alias TEXT NOT NULL DEFAULT 'default'")
        for name, ddl in {
            "message_state": "ALTER TABLE messages ADD COLUMN message_state TEXT NOT NULL DEFAULT 'open'",
            "ack_attempted_at": "ALTER TABLE messages ADD COLUMN ack_attempted_at TEXT",
            "ack_completed_at": "ALTER TABLE messages ADD COLUMN ack_completed_at TEXT",
            "ack_strategy": "ALTER TABLE messages ADD COLUMN ack_strategy TEXT",
            "ack_result": "ALTER TABLE messages ADD COLUMN ack_result TEXT",
            "completed_at": "ALTER TABLE messages ADD COLUMN completed_at TEXT",
            "completion_report_path": "ALTER TABLE messages ADD COLUMN completion_report_path TEXT",
        }.items():
            if name not in message_columns:
                db.execute(ddl)

    @staticmethod
    def _ensure_attachment_identity_columns(db: sqlite3.Connection) -> None:
        columns = {row[1] for row in db.execute("PRAGMA table_info(attachments)")}
        if "account_alias" not in columns:
            db.execute("ALTER TABLE attachments ADD COLUMN account_alias TEXT NOT NULL DEFAULT 'default'")
        if "attachment_id" not in columns:
            db.execute("ALTER TABLE attachments ADD COLUMN attachment_id TEXT")
        if "source_email" not in columns:
            db.execute("ALTER TABLE attachments ADD COLUMN source_email TEXT")
        if "manifest_path" not in columns:
            db.execute("ALTER TABLE attachments ADD COLUMN manifest_path TEXT")
        if "storage_adapter" not in columns:
            db.execute("ALTER TABLE attachments ADD COLUMN storage_adapter TEXT")
        if "staged_path" not in columns:
            db.execute("ALTER TABLE attachments ADD COLUMN staged_path TEXT")
        if "fingerprint" not in columns:
            db.execute("ALTER TABLE attachments ADD COLUMN fingerprint TEXT")
        db.execute("""CREATE INDEX IF NOT EXISTS idx_attachments_fingerprint
            ON attachments(fingerprint) WHERE fingerprint IS NOT NULL""")
        db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_attachments_attachment_id
            ON attachments(attachment_id) WHERE attachment_id IS NOT NULL""")

    @staticmethod
    def _ensure_attachment_storage_states(db: sqlite3.Connection) -> None:
        row = db.execute("""SELECT sql FROM sqlite_master
            WHERE type='table' AND name='attachments'""").fetchone()
        if row is None or "staged_storage" in str(row[0]):
            return
        db.executescript("""
            ALTER TABLE attachments RENAME TO attachments_before_storage_states;
            CREATE TABLE attachments (
                id INTEGER PRIMARY KEY, message_id INTEGER NOT NULL REFERENCES messages(id),
                account_alias TEXT NOT NULL DEFAULT 'default',
                attachment_id TEXT, source_email TEXT,
                ordinal INTEGER NOT NULL, original_filename TEXT,
                sanitized_filename TEXT, declared_mime_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN (
                    'detected','rejected_by_extension','rejected_by_size','downloaded',
                    'quarantined','ready_for_scan','quarantined_unverified',
                    'ready_for_caronte','rejected_by_scanner','rejected_malware',
                    'scan_failed','staged_local_drive','staged_storage',
                    'staging_failed','staging_conflict','error')),
                relative_path TEXT, duplicate_of_id INTEGER REFERENCES attachments(id),
                reason TEXT NOT NULL, scanner_engine TEXT,
                scan_result TEXT, scanned_at TEXT, staged_filename TEXT,
                staging_manifest_path TEXT, manifest_path TEXT,
                storage_adapter TEXT, staged_path TEXT,
                staged_at TEXT, created_at TEXT NOT NULL,
                UNIQUE(message_id, ordinal)
            );
            INSERT INTO attachments(
                id,message_id,account_alias,attachment_id,source_email,ordinal,
                original_filename,sanitized_filename,declared_mime_type,size_bytes,
                sha256,status,relative_path,duplicate_of_id,reason,scanner_engine,
                scan_result,scanned_at,staged_filename,staging_manifest_path,
                manifest_path,storage_adapter,staged_path,staged_at,created_at)
            SELECT id,message_id,account_alias,attachment_id,source_email,ordinal,
                original_filename,sanitized_filename,declared_mime_type,size_bytes,
                sha256,status,relative_path,duplicate_of_id,reason,scanner_engine,
                scan_result,scanned_at,staged_filename,staging_manifest_path,
                manifest_path,storage_adapter,staged_path,staged_at,created_at
            FROM attachments_before_storage_states;
            DROP TABLE attachments_before_storage_states;
            CREATE UNIQUE INDEX IF NOT EXISTS idx_attachments_attachment_id
                ON attachments(attachment_id) WHERE attachment_id IS NOT NULL;
        """)

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
