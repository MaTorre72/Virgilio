"""Synthetic contract fixtures. No real addresses, IDs, or credentials."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


DIGEST = "a" * 64


def command_payload(*, dry_run: bool = False) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "command_id": "cmd-test-0001",
        "created_at": "2026-06-23T10:15:30+02:00",
        "connector_id": "workstation-test:connector-test",
        "connector_type": "local_imap",
        "account_alias": "test-user",
        "provider_hint": "generic_imap",
        "mailbox": "Virgilio/da-traghettare",
        "mailbox_uidvalidity": "12345",
        "message_uid": "42",
        "message_id": "<message@example.invalid>",
        "thread_id": None,
        "subject": "Synthetic document",
        "from": "sender@example.invalid",
        "date": "2026-06-23T09:52:00+02:00",
        "user_confirmed_command": True,
        "attachments": [
            {
                "local_temp_id": "att-0001",
                "original_filename": "document.pdf",
                "sanitized_filename": "document.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 1024,
                "sha256": DIGEST,
                "quarantine_status": "ready_for_caronte",
                "scan_engine": "test-scanner",
                "scan_result": "clean",
            }
        ],
        "requested_action": "stage_attachments_in_limbo",
        "dry_run": dry_run,
    }


def response_payload() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "command_id": "cmd-test-0001",
        "ok": True,
        "accepted_attachments": [
            {"local_temp_id": "att-0001", "sha256": DIGEST}
        ],
        "rejected_attachments": [],
        "limbo_drive_ids": [
            {"local_temp_id": "att-0001", "drive_file_id": "drive-test-1"}
        ],
        "bucoliche_rows": [
            {"local_temp_id": "att-0001", "row_reference": "row-test-1"}
        ],
        "message": "Synthetic success",
        "errors": [],
    }


def clone(payload: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(payload)
