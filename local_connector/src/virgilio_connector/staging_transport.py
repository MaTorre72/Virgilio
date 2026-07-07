"""Filesystem-only staging transport for a Google Drive Desktop folder."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
from typing import Callable

from .readonly_state import ReadonlyStateStore
from .time_utils import rome_isoformat


MANIFEST_SCHEMA_VERSION = "1.0"
SYNC_NOT_VERIFIED_NOTE = (
    "File copiato in cartella locale sincronizzata; sync cloud non verificata."
)


class StagingTransportError(RuntimeError):
    pass


class StagingDisabledError(StagingTransportError):
    pass


class StagingDirectoryError(StagingTransportError):
    pass


class NoReadyFilesError(StagingTransportError):
    pass


@dataclass(frozen=True, slots=True)
class LocalDriveStagingConfig:
    enabled: bool
    staging_dir: Path | None


@dataclass(frozen=True, slots=True)
class StagingResult:
    attachment_id: str
    source_relative_path: str
    staged_filename: str
    manifest_filename: str
    sha256: str
    size_bytes: int
    dry_run: bool
    copied: bool
    status: str


class LocalDriveStagingTransport:
    def __init__(self, *, state_db: str | Path, local_data_root: str | Path,
                 config: LocalDriveStagingConfig,
                 writable_check: Callable[[Path, int], bool] = os.access) -> None:
        self.state_db = Path(state_db)
        self.local_data_root = Path(local_data_root).resolve()
        self.config = config
        self._writable_check = writable_check

    def stage_ready_files(self, *, dry_run: bool) -> tuple[StagingResult, ...]:
        staging_dir = self._validate_configuration()
        rows = self._load_ready_rows()
        if not rows:
            raise NoReadyFilesError("no ready_for_caronte files are available")
        results = []
        store = ReadonlyStateStore(self.state_db)
        if not dry_run:
            store.initialize()
        for row in rows:
            source = self._source_path(str(row["relative_path"] or ""))
            attachment_id = _attachment_id(row)
            staged_name = self._unique_name(
                staging_dir, attachment_id, str(row["sanitized_filename"])
            )
            manifest_name = f"{staged_name}.manifest.json"
            if dry_run:
                results.append(StagingResult(
                    attachment_id, str(row["relative_path"]), staged_name,
                    manifest_name, str(row["sha256"]), int(row["size_bytes"]),
                    True, False, "planned",
                ))
                continue
            try:
                result = self._copy_one(staging_dir, source, row, attachment_id,
                                        staged_name, manifest_name)
            except (OSError, ValueError, StagingTransportError) as exc:
                store.update_staging(int(row["id"]), status="staging_failed",
                                     reason=f"local staging failed: {type(exc).__name__}")
                raise StagingTransportError(
                    f"local staging failed for attachment {attachment_id}"
                ) from exc
            store.update_staging(
                int(row["id"]), status="staged_local_drive",
                reason=SYNC_NOT_VERIFIED_NOTE, staged_filename=staged_name,
                manifest_path=manifest_name,
            )
            results.append(result)
        return tuple(results)

    def _validate_configuration(self) -> Path:
        if not self.config.enabled:
            raise StagingDisabledError("local Drive staging is disabled")
        if self.config.staging_dir is None or not str(self.config.staging_dir).strip():
            raise StagingDirectoryError("VIRGILIO_LIMBO_LOCAL_SYNC_DIR is not configured")
        if not self.config.staging_dir.is_absolute():
            raise StagingDirectoryError("local Drive staging directory must be an absolute path")
        directory = self.config.staging_dir.resolve()
        if not directory.is_dir():
            raise StagingDirectoryError("configured local Drive staging directory does not exist")
        if directory.is_relative_to(self.local_data_root):
            raise StagingDirectoryError("staging directory must stay outside local quarantine data")
        if not self._writable_check(directory, os.W_OK):
            raise StagingDirectoryError("configured local Drive staging directory is not writable")
        return directory

    def _load_ready_rows(self) -> tuple[sqlite3.Row, ...]:
        if not self.state_db.is_file():
            raise FileNotFoundError(f"state database not found: {self.state_db}")
        uri = f"{self.state_db.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            return tuple(db.execute("""SELECT a.*,
                COALESCE(a.account_alias,m.account_alias,'unknown') AS resolved_account_alias,
                COALESCE(a.source_message_id,m.message_id) AS resolved_source_message_id,
                COALESCE(a.source_message_uid,m.message_uid) AS resolved_source_message_uid,
                m.uidvalidity
                FROM attachments a JOIN messages m ON m.id=a.message_id
                JOIN runs r ON r.id=m.run_id
                WHERE r.status='completed' AND a.status='ready_for_caronte'
                  AND a.relative_path IS NOT NULL ORDER BY a.id""").fetchall())

    def _source_path(self, relative_path: str) -> Path:
        source = (self.local_data_root / relative_path).resolve()
        if not source.is_relative_to(self.local_data_root):
            raise StagingTransportError("source path escapes local data root")
        if not source.is_file():
            raise StagingTransportError("quarantine source file is unavailable")
        return source

    @staticmethod
    def _unique_name(directory: Path, attachment_id: str, sanitized_filename: str) -> str:
        source = Path(sanitized_filename)
        stem = f"{attachment_id}-{source.stem}"
        suffix = source.suffix
        candidate = f"{stem}{suffix}"
        counter = 2
        while any((directory / name).exists() for name in (
            candidate, f"{candidate}.manifest.json", f"{candidate}.uploading"
        )):
            candidate = f"{stem}-{counter}{suffix}"
            counter += 1
        return candidate

    def _copy_one(self, directory: Path, source: Path, row: sqlite3.Row,
                  attachment_id: str, staged_name: str,
                  manifest_name: str) -> StagingResult:
        target = directory / staged_name
        partial = directory / f"{staged_name}.uploading"
        with source.open("rb") as reader, partial.open("xb") as writer:
            shutil.copyfileobj(reader, writer, length=1024 * 1024)
            writer.flush()
            os.fsync(writer.fileno())
        copied_hash = _sha256(partial)
        if copied_hash != str(row["sha256"]):
            raise StagingTransportError("post-copy SHA-256 mismatch")
        partial.rename(target)
        manifest = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "connector_type": "local_imap",
            "attachment_id": attachment_id,
            "original_filename": row["original_filename"],
            "sanitized_filename": row["sanitized_filename"],
            "staged_filename": staged_name,
            "sha256": copied_hash,
            "size_bytes": int(row["size_bytes"]),
            "mime_type": row["declared_mime_type"],
            "scan_engine": row["scanner_engine"],
            "scan_result": row["scan_result"],
            "quarantine_status": "ready_for_caronte",
            "source_message_id": row["resolved_source_message_id"],
            "source_message_uid": row["resolved_source_message_uid"],
            "account_alias": row["resolved_account_alias"],
            "staged_at": rome_isoformat(),
            "dry_run": False,
            "note": SYNC_NOT_VERIFIED_NOTE,
        }
        manifest_target = directory / manifest_name
        manifest_partial = directory / f"{manifest_name}.partial"
        with manifest_partial.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(manifest, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        manifest_partial.rename(manifest_target)
        return StagingResult(
            attachment_id, str(row["relative_path"]), staged_name, manifest_name,
            copied_hash, int(row["size_bytes"]), False, True, "staged_local_drive",
        )


def _attachment_id(row: sqlite3.Row) -> str:
    raw_uidvalidity = str(row["uidvalidity"] or "").strip()
    uidvalidity = "unknown" if not raw_uidvalidity or raw_uidvalidity.lower() == "none" else raw_uidvalidity
    uidvalidity = uidvalidity.replace("/", "_").replace("\\", "_")
    uid = str(row["resolved_source_message_uid"]).replace("/", "_").replace("\\", "_")
    return f"att-{uidvalidity}-{uid}-{int(row['ordinal'])}-{str(row['sha256'])[:12]}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
