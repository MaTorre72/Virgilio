"""Local filesystem storage adapter for ready multi-account attachments."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import sqlite3

from .files import sanitize_filename, sha256_file
from .multi_account import LocalStorageConfig
from .readonly_state import ReadonlyStateStore, ensure_state_db
from .traceability import audit_entry, load_machine_id
from .time_utils import rome_isoformat


class StorageAdapterError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class StorageStageResult:
    attachment_id: str
    account_alias: str
    source_relative_path: str
    staged_path: str
    staged_manifest_path: str | None
    sha256: str
    size_bytes: int
    dry_run: bool
    copied: bool
    status: str
    message: str


class LocalFilesystemStorageAdapter:
    def __init__(self, *, state_db: str | Path, local_data_root: str | Path,
                 config: LocalStorageConfig) -> None:
        self.state_db = Path(state_db)
        self.local_data_root = Path(local_data_root).resolve()
        self.config = config

    def stage_ready(self, *, dry_run: bool) -> tuple[StorageStageResult, ...]:
        ensure_state_db(self.local_data_root)
        staging_root = self._validate_configuration()
        rows = self._load_candidate_rows()
        store = ReadonlyStateStore(self.state_db)
        if not dry_run:
            store.initialize()
        results: list[StorageStageResult] = []
        for row in rows:
            result = self._stage_row(row, staging_root, dry_run=dry_run)
            results.append(result)
            if dry_run:
                continue
            if result.status == "staged_storage":
                store.update_storage(int(row["id"]), status="staged_storage",
                    reason=result.message, storage_adapter=self.config.adapter,
                    staged_path=result.staged_path,
                    staged_manifest_path=result.staged_manifest_path,
                    staged_filename=Path(result.staged_path).name)
                store.add_audit_event(machine_id=load_machine_id(self.local_data_root),
                    account_alias=str(row["account_alias"]), entity_type="attachment",
                    entity_id=str(row["attachment_id"]), fingerprint=row["fingerprint"],
                    action="attachment_staged", status=result.status,
                    details={"staged_filename": Path(result.staged_path).name})
            elif result.status == "staging_conflict":
                store.update_storage(int(row["id"]), status="staging_conflict",
                    reason=result.message, storage_adapter=self.config.adapter,
                    staged_path=result.staged_path,
                    staged_manifest_path=result.staged_manifest_path,
                    staged_filename=Path(result.staged_path).name)
        return tuple(results)

    def _validate_configuration(self) -> Path:
        if self.config.staging_dir is None:
            raise StorageAdapterError("storage staging_dir is not configured")
        if self.config.adapter != "local_filesystem":
            raise StorageAdapterError(f"unsupported storage adapter: {self.config.adapter}")
        staging = self.config.staging_dir
        if not staging.is_absolute():
            raise StorageAdapterError("storage staging_dir must be an absolute path")
        if not staging.exists():
            if not self.config.create_staging_dir:
                raise StorageAdapterError("storage staging_dir does not exist")
            staging.mkdir(parents=True, exist_ok=True)
        if not staging.is_dir():
            raise StorageAdapterError("storage staging_dir is not a directory")
        root = staging.resolve()
        if root.is_relative_to(self.local_data_root):
            raise StorageAdapterError("storage staging_dir must stay outside local data root")
        if not os.access(root, os.W_OK):
            raise StorageAdapterError("storage staging_dir is not writable")
        return root

    def _load_candidate_rows(self) -> tuple[sqlite3.Row, ...]:
        if not self.state_db.is_file():
            raise FileNotFoundError(f"state database not found: {self.state_db}")
        uri = f"{self.state_db.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            return tuple(db.execute("""SELECT a.*,m.message_uid,m.message_id,m.subject
                FROM attachments a JOIN messages m ON m.id=a.message_id
                WHERE a.status IN ('ready_for_caronte','staged_storage')
                  AND a.relative_path IS NOT NULL
                  AND a.attachment_id IS NOT NULL
                ORDER BY a.id""").fetchall())

    def _stage_row(self, row: sqlite3.Row, staging_root: Path, *, dry_run: bool) -> StorageStageResult:
        account_alias = str(row["account_alias"])
        attachment_id = str(row["attachment_id"])
        source = self._safe_local_path(str(row["relative_path"]))
        manifest_source = self._safe_local_path(str(row["manifest_path"])) if row["manifest_path"] else None
        if not source.is_file():
            return self._result(row, "", None, dry_run, False, "staging_failed",
                                "quarantine source file is missing")
        source_hash = sha256_file(source)
        if source_hash != str(row["sha256"]):
            return self._result(row, "", None, dry_run, False, "staging_conflict",
                                "quarantine source hash does not match SQLite")
        manifest = self._load_manifest(manifest_source, row)
        staged_dir = staging_root / account_alias if self.config.use_account_subfolders else staging_root
        staged_name = self._staged_filename(account_alias, attachment_id, str(row["sanitized_filename"]))
        target = staged_dir / staged_name
        manifest_target = staged_dir / f"{staged_name}.manifest.json"
        relative_target = self._relative_to_staging(staging_root, target)
        relative_manifest = self._relative_to_staging(staging_root, manifest_target)
        if str(row["status"]) == "staged_storage":
            return self._result(row, relative_target, relative_manifest, dry_run, False,
                                "already_staged", "attachment already staged")
        if target.exists():
            existing_hash = sha256_file(target)
            if existing_hash == str(row["sha256"]):
                return self._result(row, relative_target, relative_manifest, dry_run, False,
                                    "staged_storage", "existing staged file has matching sha256")
            return self._result(row, relative_target, relative_manifest, dry_run, False,
                                "staging_conflict", "staged file exists with different sha256")
        if manifest_target.exists():
            return self._result(row, relative_target, relative_manifest, dry_run, False,
                                "staging_conflict", "staged manifest already exists")
        if dry_run:
            return self._result(row, relative_target, relative_manifest, True, False,
                                "planned", "would copy ready attachment")
        staged_dir.mkdir(parents=True, exist_ok=True)
        self._copy_atomic(source, target)
        copied_hash = sha256_file(target)
        if copied_hash != str(row["sha256"]):
            return self._result(row, relative_target, relative_manifest, False, True,
                                "staging_conflict", "post-copy sha256 mismatch")
        if self.config.copy_manifest:
            staged_manifest = dict(manifest)
            staged_manifest.update({
                "staged_filename": staged_name,
                "storage_adapter": self.config.adapter,
                "staged_at": rome_isoformat(),
                "note": "File staged by local filesystem adapter; no IMAP ack performed.",
            })
            staged_manifest.setdefault("audit_trail", []).append(audit_entry(
                load_machine_id(self.local_data_root), "attachment_staged", "staged_storage",
                account_alias, "attachment", attachment_id,
                {"staged_filename": staged_name}))
            forbidden = {"password", "token", "file_bytes", "base64", "content", "raw"}
            if forbidden & set(staged_manifest):
                raise StorageAdapterError("manifest contains forbidden fields")
            self._write_json_atomic(manifest_target, staged_manifest)
        return self._result(row, relative_target, relative_manifest, False, True,
                            "staged_storage", "attachment staged to local filesystem")

    def _safe_local_path(self, relative_path: str) -> Path:
        path = (self.local_data_root / relative_path).resolve()
        if not path.is_relative_to(self.local_data_root):
            raise StorageAdapterError("local data path escapes root")
        return path

    @staticmethod
    def _staged_filename(account_alias: str, attachment_id: str, sanitized_filename: str) -> str:
        return sanitize_filename(f"{account_alias}__{attachment_id}__{sanitized_filename}", max_length=220)

    @staticmethod
    def _relative_to_staging(staging_root: Path, path: Path) -> str:
        return path.relative_to(staging_root).as_posix()

    @staticmethod
    def _copy_atomic(source: Path, target: Path) -> None:
        partial = target.with_name(target.name + ".uploading")
        with source.open("rb") as reader, partial.open("xb") as writer:
            shutil.copyfileobj(reader, writer, length=1024 * 1024)
            writer.flush()
            os.fsync(writer.fileno())
        partial.rename(target)

    @staticmethod
    def _write_json_atomic(target: Path, payload: dict[str, object]) -> None:
        partial = target.with_name(target.name + ".partial")
        with partial.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        partial.rename(target)

    @staticmethod
    def _load_manifest(path: Path | None, row: sqlite3.Row) -> dict[str, object]:
        if path is None or not path.is_file():
            raise StorageAdapterError("source manifest is missing")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        expected = {
            "attachment_id": row["attachment_id"],
            "account_alias": row["account_alias"],
            "sha256": row["sha256"],
            "quarantine_status": "ready_for_caronte",
        }
        for key, value in expected.items():
            if manifest.get(key) != value:
                raise StorageAdapterError(f"manifest field {key} does not match SQLite")
        return manifest

    @staticmethod
    def _result(row: sqlite3.Row, staged_path: str, staged_manifest_path: str | None,
                dry_run: bool, copied: bool, status: str, message: str) -> StorageStageResult:
        return StorageStageResult(
            str(row["attachment_id"]), str(row["account_alias"]), str(row["relative_path"]),
            staged_path, staged_manifest_path, str(row["sha256"]), int(row["size_bytes"]),
            dry_run, copied, status, message,
        )
