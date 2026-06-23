"""Immutable domain models for the connector/Caronte contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import re
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"
CONNECTOR_TYPE = "local_imap"
REQUESTED_ACTION = "stage_attachments_in_limbo"
TRIGGER_MAILBOX = "Virgilio/da-traghettare"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ContractValidationError(ValueError):
    """Raised when a command or response violates the documented contract."""


class QuarantineStatus(StrEnum):
    DOWNLOADED = "downloaded"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"
    SCAN_FAILED = "scan_failed"
    READY_FOR_CARONTE = "ready_for_caronte"
    UPLOADED_TO_LIMBO = "uploaded_to_limbo"


def require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractValidationError(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContractValidationError(f"{field} must be an array")
    return value


def require_string(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ContractValidationError(f"{field} must be a string")
    if not allow_empty and not value.strip():
        raise ContractValidationError(f"{field} must not be empty")
    return value


def require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ContractValidationError(f"{field} must be a boolean")
    return value


def require_non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContractValidationError(f"{field} must be a non-negative integer")
    return value


def require_sha256(value: Any, field: str = "sha256") -> str:
    digest = require_string(value, field)
    if not _SHA256_RE.fullmatch(digest):
        raise ContractValidationError(f"{field} must be 64 lowercase hex characters")
    return digest


def require_aware_datetime(value: Any, field: str) -> str:
    text = require_string(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractValidationError(f"{field} must be an ISO 8601 datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContractValidationError(f"{field} must include a timezone")
    return text


def reject_unknown_fields(
    data: Mapping[str, Any], *, allowed: set[str], context: str
) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ContractValidationError(
            f"{context} contains unknown fields: {', '.join(unknown)}"
        )


@dataclass(frozen=True, slots=True)
class Attachment:
    local_temp_id: str
    original_filename: str
    sanitized_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    quarantine_status: QuarantineStatus
    scan_engine: str
    scan_result: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "Attachment":
        data = require_mapping(raw, "attachment")
        fields = {
            "local_temp_id", "original_filename", "sanitized_filename",
            "mime_type", "size_bytes", "sha256", "quarantine_status",
            "scan_engine", "scan_result",
        }
        reject_unknown_fields(data, allowed=fields, context="attachment")
        try:
            status = QuarantineStatus(
                require_string(data.get("quarantine_status"), "quarantine_status")
            )
        except ValueError as exc:
            raise ContractValidationError("invalid quarantine_status") from exc
        local_temp_id = require_string(data.get("local_temp_id"), "local_temp_id")
        if "/" in local_temp_id or "\\" in local_temp_id:
            raise ContractValidationError("local_temp_id must be opaque, not a path")
        return cls(
            local_temp_id=local_temp_id,
            original_filename=require_string(data.get("original_filename"), "original_filename"),
            sanitized_filename=require_string(data.get("sanitized_filename"), "sanitized_filename"),
            mime_type=require_string(data.get("mime_type"), "mime_type"),
            size_bytes=require_non_negative_int(data.get("size_bytes"), "size_bytes"),
            sha256=require_sha256(data.get("sha256")),
            quarantine_status=status,
            scan_engine=require_string(data.get("scan_engine"), "scan_engine"),
            scan_result=require_string(data.get("scan_result"), "scan_result"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "local_temp_id": self.local_temp_id,
            "original_filename": self.original_filename,
            "sanitized_filename": self.sanitized_filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "quarantine_status": self.quarantine_status.value,
            "scan_engine": self.scan_engine,
            "scan_result": self.scan_result,
        }


@dataclass(frozen=True, slots=True)
class CaronteCommand:
    schema_version: str
    command_id: str
    created_at: str
    connector_id: str
    connector_type: str
    account_alias: str
    provider_hint: str
    mailbox: str
    mailbox_uidvalidity: str | None
    message_uid: str
    message_id: str
    thread_id: str | None
    subject: str
    sender: str
    date: str
    user_confirmed_command: bool
    attachments: tuple[Attachment, ...]
    requested_action: str
    dry_run: bool

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "CaronteCommand":
        data = require_mapping(raw, "command")
        fields = {
            "schema_version", "command_id", "created_at", "connector_id",
            "connector_type", "account_alias", "provider_hint", "mailbox",
            "mailbox_uidvalidity", "message_uid", "message_id", "thread_id",
            "subject", "from", "date", "user_confirmed_command", "attachments",
            "requested_action", "dry_run",
        }
        reject_unknown_fields(data, allowed=fields, context="command")
        schema_version = require_string(data.get("schema_version"), "schema_version")
        if schema_version != SCHEMA_VERSION:
            raise ContractValidationError(f"unsupported schema_version: {schema_version}")
        connector_type = require_string(data.get("connector_type"), "connector_type")
        if connector_type != CONNECTOR_TYPE:
            raise ContractValidationError(f"connector_type must be {CONNECTOR_TYPE}")
        requested_action = require_string(data.get("requested_action"), "requested_action")
        if requested_action != REQUESTED_ACTION:
            raise ContractValidationError(f"requested_action must be {REQUESTED_ACTION}")
        dry_run = require_bool(data.get("dry_run"), "dry_run")
        confirmed = require_bool(data.get("user_confirmed_command"), "user_confirmed_command")
        if not dry_run and not confirmed:
            raise ContractValidationError(
                "user_confirmed_command must be true for operational commands"
            )
        attachments = tuple(
            Attachment.from_mapping(require_mapping(item, "attachment"))
            for item in require_list(data.get("attachments"), "attachments")
        )
        ids = [item.local_temp_id for item in attachments]
        if len(ids) != len(set(ids)):
            raise ContractValidationError("attachment local_temp_id values must be unique")
        if not dry_run and any(
            item.quarantine_status is not QuarantineStatus.READY_FOR_CARONTE
            for item in attachments
        ):
            raise ContractValidationError(
                "operational commands may include only ready_for_caronte attachments"
            )
        uidvalidity_raw = data.get("mailbox_uidvalidity")
        thread_id_raw = data.get("thread_id")
        return cls(
            schema_version=schema_version,
            command_id=require_string(data.get("command_id"), "command_id"),
            created_at=require_aware_datetime(data.get("created_at"), "created_at"),
            connector_id=require_string(data.get("connector_id"), "connector_id"),
            connector_type=connector_type,
            account_alias=require_string(data.get("account_alias"), "account_alias"),
            provider_hint=require_string(data.get("provider_hint"), "provider_hint"),
            mailbox=require_string(data.get("mailbox"), "mailbox"),
            mailbox_uidvalidity=(None if uidvalidity_raw is None else require_string(uidvalidity_raw, "mailbox_uidvalidity")),
            message_uid=require_string(data.get("message_uid"), "message_uid"),
            message_id=require_string(data.get("message_id"), "message_id", allow_empty=True),
            thread_id=(None if thread_id_raw is None else require_string(thread_id_raw, "thread_id")),
            subject=require_string(data.get("subject"), "subject", allow_empty=True),
            sender=require_string(data.get("from"), "from"),
            date=require_aware_datetime(data.get("date"), "date"),
            user_confirmed_command=confirmed,
            attachments=attachments,
            requested_action=requested_action,
            dry_run=dry_run,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "command_id": self.command_id,
            "created_at": self.created_at,
            "connector_id": self.connector_id,
            "connector_type": self.connector_type,
            "account_alias": self.account_alias,
            "provider_hint": self.provider_hint,
            "mailbox": self.mailbox,
            "mailbox_uidvalidity": self.mailbox_uidvalidity,
            "message_uid": self.message_uid,
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "subject": self.subject,
            "from": self.sender,
            "date": self.date,
            "user_confirmed_command": self.user_confirmed_command,
            "attachments": [item.to_dict() for item in self.attachments],
            "requested_action": self.requested_action,
            "dry_run": self.dry_run,
        }


@dataclass(frozen=True, slots=True)
class AcceptedAttachment:
    local_temp_id: str
    sha256: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "AcceptedAttachment":
        data = require_mapping(raw, "accepted_attachment")
        reject_unknown_fields(data, allowed={"local_temp_id", "sha256"}, context="accepted_attachment")
        return cls(
            local_temp_id=require_string(data.get("local_temp_id"), "local_temp_id"),
            sha256=require_sha256(data.get("sha256")),
        )

    def to_dict(self) -> dict[str, str]:
        return {"local_temp_id": self.local_temp_id, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class RejectedAttachment:
    local_temp_id: str
    code: str
    message: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "RejectedAttachment":
        data = require_mapping(raw, "rejected_attachment")
        reject_unknown_fields(data, allowed={"local_temp_id", "code", "message"}, context="rejected_attachment")
        return cls(
            local_temp_id=require_string(data.get("local_temp_id"), "local_temp_id"),
            code=require_string(data.get("code"), "code"),
            message=require_string(data.get("message"), "message"),
        )

    def to_dict(self) -> dict[str, str]:
        return {"local_temp_id": self.local_temp_id, "code": self.code, "message": self.message}


@dataclass(frozen=True, slots=True)
class LimboDriveFile:
    local_temp_id: str
    drive_file_id: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "LimboDriveFile":
        data = require_mapping(raw, "limbo_drive_id")
        reject_unknown_fields(data, allowed={"local_temp_id", "drive_file_id"}, context="limbo_drive_id")
        return cls(
            local_temp_id=require_string(data.get("local_temp_id"), "local_temp_id"),
            drive_file_id=require_string(data.get("drive_file_id"), "drive_file_id"),
        )

    def to_dict(self) -> dict[str, str]:
        return {"local_temp_id": self.local_temp_id, "drive_file_id": self.drive_file_id}


@dataclass(frozen=True, slots=True)
class BucolicheRow:
    local_temp_id: str
    row_reference: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "BucolicheRow":
        data = require_mapping(raw, "bucoliche_row")
        reject_unknown_fields(data, allowed={"local_temp_id", "row_reference"}, context="bucoliche_row")
        return cls(
            local_temp_id=require_string(data.get("local_temp_id"), "local_temp_id"),
            row_reference=require_string(data.get("row_reference"), "row_reference"),
        )

    def to_dict(self) -> dict[str, str]:
        return {"local_temp_id": self.local_temp_id, "row_reference": self.row_reference}


@dataclass(frozen=True, slots=True)
class ContractError:
    code: str
    message: str
    retryable: bool
    local_temp_id: str | None = None

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ContractError":
        data = require_mapping(raw, "error")
        reject_unknown_fields(data, allowed={"code", "message", "retryable", "local_temp_id"}, context="error")
        temp_id = data.get("local_temp_id")
        return cls(
            code=require_string(data.get("code"), "code"),
            message=require_string(data.get("message"), "message"),
            retryable=require_bool(data.get("retryable"), "retryable"),
            local_temp_id=(None if temp_id is None else require_string(temp_id, "local_temp_id")),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.local_temp_id is not None:
            result["local_temp_id"] = self.local_temp_id
        return result


@dataclass(frozen=True, slots=True)
class CaronteResponse:
    schema_version: str
    command_id: str
    ok: bool
    accepted_attachments: tuple[AcceptedAttachment, ...]
    rejected_attachments: tuple[RejectedAttachment, ...]
    limbo_drive_ids: tuple[LimboDriveFile, ...]
    bucoliche_rows: tuple[BucolicheRow, ...]
    message: str
    errors: tuple[ContractError, ...]

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "CaronteResponse":
        data = require_mapping(raw, "response")
        fields = {
            "schema_version", "command_id", "ok", "accepted_attachments",
            "rejected_attachments", "limbo_drive_ids", "bucoliche_rows",
            "message", "errors",
        }
        reject_unknown_fields(data, allowed=fields, context="response")
        schema_version = require_string(data.get("schema_version"), "schema_version")
        if schema_version != SCHEMA_VERSION:
            raise ContractValidationError(f"unsupported schema_version: {schema_version}")
        response = cls(
            schema_version=schema_version,
            command_id=require_string(data.get("command_id"), "command_id"),
            ok=require_bool(data.get("ok"), "ok"),
            accepted_attachments=tuple(
                AcceptedAttachment.from_mapping(require_mapping(item, "accepted_attachment"))
                for item in require_list(data.get("accepted_attachments"), "accepted_attachments")
            ),
            rejected_attachments=tuple(
                RejectedAttachment.from_mapping(require_mapping(item, "rejected_attachment"))
                for item in require_list(data.get("rejected_attachments"), "rejected_attachments")
            ),
            limbo_drive_ids=tuple(
                LimboDriveFile.from_mapping(require_mapping(item, "limbo_drive_id"))
                for item in require_list(data.get("limbo_drive_ids"), "limbo_drive_ids")
            ),
            bucoliche_rows=tuple(
                BucolicheRow.from_mapping(require_mapping(item, "bucoliche_row"))
                for item in require_list(data.get("bucoliche_rows"), "bucoliche_rows")
            ),
            message=require_string(data.get("message"), "message", allow_empty=True),
            errors=tuple(
                ContractError.from_mapping(require_mapping(item, "error"))
                for item in require_list(data.get("errors"), "errors")
            ),
        )
        response._validate_unique_ids()
        return response

    def _validate_unique_ids(self) -> None:
        groups = {
            "accepted_attachments": [x.local_temp_id for x in self.accepted_attachments],
            "rejected_attachments": [x.local_temp_id for x in self.rejected_attachments],
            "limbo_drive_ids": [x.local_temp_id for x in self.limbo_drive_ids],
            "bucoliche_rows": [x.local_temp_id for x in self.bucoliche_rows],
        }
        for field, ids in groups.items():
            if len(ids) != len(set(ids)):
                raise ContractValidationError(f"{field} contains duplicate local_temp_id")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "command_id": self.command_id,
            "ok": self.ok,
            "accepted_attachments": [x.to_dict() for x in self.accepted_attachments],
            "rejected_attachments": [x.to_dict() for x in self.rejected_attachments],
            "limbo_drive_ids": [x.to_dict() for x in self.limbo_drive_ids],
            "bucoliche_rows": [x.to_dict() for x in self.bucoliche_rows],
            "message": self.message,
            "errors": [x.to_dict() for x in self.errors],
        }
