"""Metadata-only adapter from local staged manifests to Da archiviare."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


DA_ARCHIVIARE_INTAKE_ACTION = "intake_virgilio_inbox"
FORBIDDEN_FIELDS = frozenset(
    {"local_path", "file_path", "staged_path", "manifest_path",
     "file_bytes", "base64", "content", "raw"}
)


class DaArchiviareIntakeError(RuntimeError):
    """Raised when a local staged manifest cannot be adapted safely."""


def build_da_archiviare_intake_payload(
    manifest_path: str | Path,
    *,
    drive_file_id: str,
    manifest_file_id: str,
    form_url: str = "",
) -> dict[str, Any]:
    """Build the metadata-only payload for the Da archiviare intake."""
    manifest = _load_json_object(manifest_path)
    payload = {
        "action": DA_ARCHIVIARE_INTAKE_ACTION,
        "manifest": _prepare_manifest(manifest),
        "drive_file_id": _normalized_identifier(drive_file_id, "drive_file_id"),
        "manifest_file_id": _normalized_identifier(manifest_file_id, "manifest_file_id"),
        "form_url": _normalized_optional_string(form_url),
    }
    forbidden = _find_forbidden_fields(payload)
    if forbidden:
        raise DaArchiviareIntakeError(
            "payload contains forbidden fields: " + ", ".join(forbidden)
        )
    return payload


def _load_json_object(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DaArchiviareIntakeError(f"local staged manifest not found: {source}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DaArchiviareIntakeError(
            f"local staged manifest is not valid UTF-8 JSON: {source}"
        ) from exc
    if not isinstance(raw, dict):
        raise DaArchiviareIntakeError("local staged manifest must be a JSON object")
    return raw


def _prepare_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    normalized = _clone_json_object(manifest)
    required_text = (
        "connector_type", "account_alias", "source_message_id", "source_message_uid",
        "attachment_id", "original_filename", "staged_filename", "sha256",
        "scan_result", "quarantine_status",
    )
    missing = [field for field in required_text if _normalized_string(normalized.get(field)) == ""]
    if missing:
        raise DaArchiviareIntakeError(
            "local staged manifest is missing required fields: " + ", ".join(missing)
        )
    if _normalized_string(normalized.get("connector_type")) != "local_imap":
        raise DaArchiviareIntakeError("connector_type must be local_imap")
    if _normalized_string(normalized.get("quarantine_status")) != "ready_for_caronte":
        raise DaArchiviareIntakeError("quarantine_status must be ready_for_caronte")
    if _normalized_string(normalized.get("scan_result")) != "clean":
        raise DaArchiviareIntakeError("scan_result must be clean")
    if normalized.get("dry_run") not in {False, None}:
        raise DaArchiviareIntakeError("dry_run must be false for Da archiviare intake")
    staged_filename = _normalized_string(normalized.get("staged_filename"))
    if Path(staged_filename).name != staged_filename or "/" in staged_filename or "\\" in staged_filename:
        raise DaArchiviareIntakeError("staged_filename is invalid")
    sha256 = _normalized_string(normalized.get("sha256"))
    if len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256):
        raise DaArchiviareIntakeError("sha256 is invalid")
    size_bytes = normalized.get("size_bytes")
    if isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes < 0:
        raise DaArchiviareIntakeError("size_bytes is invalid")
    return normalized


def _clone_json_object(value: Mapping[str, Any]) -> dict[str, Any]:
    try:
        cloned = json.loads(json.dumps(value, ensure_ascii=False))
    except (TypeError, ValueError) as exc:
        raise DaArchiviareIntakeError("manifest must be JSON serializable") from exc
    if not isinstance(cloned, dict):
        raise DaArchiviareIntakeError("manifest must serialize to a JSON object")
    return cloned


def _normalized_identifier(value: str, field_name: str) -> str:
    normalized = _normalized_string(value)
    if not normalized:
        raise DaArchiviareIntakeError(f"{field_name} is required")
    if "/" in normalized or "\\" in normalized:
        raise DaArchiviareIntakeError(f"{field_name} must not contain a path")
    return normalized


def _normalized_optional_string(value: str) -> str:
    return _normalized_string(value)


def _normalized_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _find_forbidden_fields(value: Any, path: str = "$") -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key).lower() in FORBIDDEN_FIELDS:
                found.append(child_path)
            found.extend(_find_forbidden_fields(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_find_forbidden_fields(child, f"{path}[{index}]"))
    return tuple(found)
