"""Operational handoff from synchronized Limbo files to Da archiviare."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Sequence

from .da_archiviare_intake import (
    DaArchiviareIntakeError,
    DaArchiviareIntakeHttpClient,
    DaArchiviareIntakeResponse,
)
from .drive_staging_verify import (
    DriveStagingVerifyClient,
    DriveStagingVerifyError,
)
from .local_paths import LocalDataPaths
from .readonly_state import ReadonlyStateStore, ensure_state_db
from .storage_adapter import StorageStageResult
from .traceability import load_machine_id


SUCCESS_STATUSES = frozenset({"created", "updated", "idempotent"})


@dataclass(frozen=True, slots=True)
class OperationalHandoffResult:
    attachment_id: str
    account_alias: str
    status: str
    message: str
    inbox_id: str = ""
    drive_file_id: str = ""
    manifest_file_id: str = ""
    form_url: str = ""
    notification_status: str = ""


class OperationalHandoffRunner:
    """Compose the existing metadata-only verify and intake clients."""

    def __init__(
        self,
        *,
        paths: LocalDataPaths,
        staging_root: Path,
        verifier: DriveStagingVerifyClient,
        intake: DaArchiviareIntakeHttpClient,
    ) -> None:
        self.paths = paths
        self.staging_root = Path(staging_root).resolve()
        self.verifier = verifier
        self.intake = intake

    def deliver(
        self,
        storage_results: Sequence[StorageStageResult],
        *,
        dry_run: bool,
    ) -> tuple[OperationalHandoffResult, ...]:
        ensure_state_db(self.paths.root)
        results: list[OperationalHandoffResult] = []
        for staged in storage_results:
            if staged.status not in {"staged_storage", "already_staged", "planned"}:
                continue
            if self._already_delivered(staged):
                results.append(self._result(
                    staged, "already_delivered",
                    "Documento gia presente in Da archiviare.",
                ))
                continue
            if dry_run:
                results.append(self._result(
                    staged, "planned",
                    "Il documento verrebbe verificato e inviato a Da archiviare.",
                ))
                continue
            identity: dict[str, str] = {"fingerprint": ""}
            try:
                manifest_path = self._manifest_path(staged)
                identity = self._manifest_identity(manifest_path, staged)
                verified = self.verifier.verify_manifest(manifest_path)
            except (DriveStagingVerifyError, OSError, ValueError) as exc:
                self._record(
                    staged, "waiting", {"error": str(exc)},
                    fingerprint=identity["fingerprint"] or None,
                )
                results.append(self._result(
                    staged, "waiting",
                    "Documento in attesa della sincronizzazione del Limbo.",
                ))
                continue
            if not verified.cloud_visible:
                self._record(staged, "waiting", {
                    "message": verified.message,
                    "errors": [dict(item) for item in verified.errors],
                }, fingerprint=identity["fingerprint"])
                results.append(self._result(
                    staged, "waiting",
                    "Documento in attesa della sincronizzazione del Limbo.",
                ))
                continue
            try:
                intake_result = self.intake.create_record(
                    manifest_path,
                    drive_file_id=verified.drive_file_id,
                    manifest_file_id=verified.manifest_file_id,
                )
            except DaArchiviareIntakeError as exc:
                self._record(staged, "failed", {
                    "error": str(exc),
                    "drive_file_id": verified.drive_file_id,
                    "manifest_file_id": verified.manifest_file_id,
                }, fingerprint=identity["fingerprint"])
                results.append(self._result(
                    staged, "failed",
                    "Invio a Da archiviare non riuscito.",
                    drive_file_id=verified.drive_file_id,
                    manifest_file_id=verified.manifest_file_id,
                ))
                continue
            status = self._intake_status(intake_result)
            self._record(staged, status, {
                "inbox_id": intake_result.inbox_id,
                "drive_file_id": verified.drive_file_id,
                "manifest_file_id": verified.manifest_file_id,
                "created": intake_result.created,
                "updated": intake_result.updated,
                "idempotent": intake_result.idempotent,
                "message": intake_result.message,
                "errors": [dict(item) for item in intake_result.errors],
                "form_url": intake_result.form_url,
                "notification_status": intake_result.notification_status,
            }, fingerprint=identity["fingerprint"])
            if not intake_result.ok:
                results.append(self._result(
                    staged, "failed",
                    "Invio a Da archiviare non riuscito.",
                    drive_file_id=verified.drive_file_id,
                    manifest_file_id=verified.manifest_file_id,
                ))
                continue
            results.append(self._result(
                staged, status,
                "Documento inviato a Da archiviare.",
                inbox_id=intake_result.inbox_id,
                drive_file_id=verified.drive_file_id,
                manifest_file_id=verified.manifest_file_id,
                form_url=intake_result.form_url,
                notification_status=intake_result.notification_status,
            ))
        return tuple(results)

    def _manifest_path(self, staged: StorageStageResult) -> Path:
        if not staged.staged_manifest_path:
            raise ValueError("staged manifest path is missing")
        manifest_path = (self.staging_root / staged.staged_manifest_path).resolve()
        if not manifest_path.is_relative_to(self.staging_root):
            raise ValueError("staged manifest path escapes Limbo")
        if not manifest_path.is_file():
            raise ValueError("staged manifest was not found")
        return manifest_path

    @staticmethod
    def _manifest_identity(
        manifest_path: Path,
        staged: StorageStageResult,
    ) -> dict[str, str]:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("staged manifest must be an object")
        attachment_id = str(raw.get("attachment_id", "")).strip()
        account_alias = str(raw.get("account_alias", "")).strip()
        fingerprint = str(raw.get("fingerprint", "")).strip()
        if attachment_id != staged.attachment_id or account_alias != staged.account_alias:
            raise ValueError("staged manifest identity is inconsistent")
        if not fingerprint:
            raise ValueError("staged manifest fingerprint is missing")
        return {"fingerprint": fingerprint}

    def _already_delivered(self, staged: StorageStageResult) -> bool:
        uri = f"{self.paths.state_db.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as db:
            row = db.execute(
                """SELECT 1 FROM audit_events
                   WHERE entity_id=? AND account_alias=?
                     AND action='da_archiviare_intake'
                     AND status IN (?,?,?)
                   LIMIT 1""",
                (
                    staged.attachment_id,
                    staged.account_alias,
                    *sorted(SUCCESS_STATUSES),
                ),
            ).fetchone()
        return row is not None

    def _record(
        self,
        staged: StorageStageResult,
        status: str,
        details: dict[str, object],
        *,
        fingerprint: str | None = None,
    ) -> None:
        store = ReadonlyStateStore(self.paths.state_db)
        store.initialize()
        store.add_audit_event(
            machine_id=load_machine_id(self.paths.root),
            account_alias=staged.account_alias,
            entity_type="attachment",
            entity_id=staged.attachment_id,
            fingerprint=fingerprint,
            action="da_archiviare_intake",
            status=status,
            details=details,
        )

    @staticmethod
    def _intake_status(result: DaArchiviareIntakeResponse) -> str:
        if not result.ok:
            return "failed"
        if result.created:
            return "created"
        if result.updated:
            return "updated"
        return "idempotent"

    @staticmethod
    def _result(
        staged: StorageStageResult,
        status: str,
        message: str,
        *,
        inbox_id: str = "",
        drive_file_id: str = "",
        manifest_file_id: str = "",
        form_url: str = "",
        notification_status: str = "",
    ) -> OperationalHandoffResult:
        return OperationalHandoffResult(
            attachment_id=staged.attachment_id,
            account_alias=staged.account_alias,
            status=status,
            message=message,
            inbox_id=inbox_id,
            drive_file_id=drive_file_id,
            manifest_file_id=manifest_file_id,
            form_url=form_url,
            notification_status=notification_status,
        )
