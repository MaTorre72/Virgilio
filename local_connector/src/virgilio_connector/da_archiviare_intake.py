"""Metadata-only adapter from local staged manifests to Da archiviare."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DA_ARCHIVIARE_INTAKE_ACTION = "intake_virgilio_inbox"
FORBIDDEN_FIELDS = frozenset(
    {"local_path", "file_path", "staged_path", "manifest_path",
     "file_bytes", "base64", "content", "raw"}
)


class DaArchiviareIntakeError(RuntimeError):
    """Raised when a local staged manifest cannot be adapted safely."""


class DaArchiviareIntakeClientError(DaArchiviareIntakeError):
    """Raised when the HTTP intake client cannot complete safely."""


class DaArchiviareIntakeUrlNotConfigured(DaArchiviareIntakeClientError):
    pass


class DaArchiviareIntakeTokenNotConfigured(DaArchiviareIntakeClientError):
    pass


@dataclass(frozen=True, slots=True)
class DaArchiviareIntakeResponse:
    ok: bool
    action: str
    inbox_id: str
    created: bool
    updated: bool
    idempotent: bool
    row: int
    message: str
    errors: tuple[dict[str, Any], ...]

    @classmethod
    def from_mapping(cls, raw: Any) -> "DaArchiviareIntakeResponse":
        if not isinstance(raw, dict):
            raise DaArchiviareIntakeClientError("Da archiviare response must be a JSON object")
        required = {
            "ok", "action", "inbox_id", "created", "updated",
            "idempotent", "row", "message", "errors",
        }
        if not required.issubset(raw):
            raise DaArchiviareIntakeClientError(
                "Da archiviare response is missing required fields"
            )
        if not isinstance(raw["ok"], bool):
            raise DaArchiviareIntakeClientError("Da archiviare response field ok is invalid")
        if not isinstance(raw["action"], str) or raw["action"] != DA_ARCHIVIARE_INTAKE_ACTION:
            raise DaArchiviareIntakeClientError("response is not a Da archiviare intake result")
        if not isinstance(raw["inbox_id"], str):
            raise DaArchiviareIntakeClientError("Da archiviare response field inbox_id is invalid")
        for field in ("created", "updated", "idempotent"):
            if not isinstance(raw[field], bool):
                raise DaArchiviareIntakeClientError(
                    f"Da archiviare response field {field} is invalid"
                )
        if isinstance(raw["row"], bool) or not isinstance(raw["row"], int) or raw["row"] < 0:
            raise DaArchiviareIntakeClientError("Da archiviare response field row is invalid")
        if not isinstance(raw["message"], str) or not isinstance(raw["errors"], list):
            raise DaArchiviareIntakeClientError("Da archiviare response error fields are invalid")
        if raw["ok"] and not raw["inbox_id"]:
            raise DaArchiviareIntakeClientError("successful Da archiviare response is inconsistent")
        if raw["ok"] and raw["row"] < 1:
            raise DaArchiviareIntakeClientError("successful Da archiviare response row is invalid")
        if raw["created"] and raw["updated"]:
            raise DaArchiviareIntakeClientError("created response cannot also be updated")
        if raw["idempotent"] and (raw["created"] or raw["updated"]):
            raise DaArchiviareIntakeClientError("idempotent response is inconsistent")
        if raw["ok"] and not (raw["created"] or raw["updated"] or raw["idempotent"]):
            raise DaArchiviareIntakeClientError("successful Da archiviare response is incomplete")
        return cls(
            ok=raw["ok"],
            action=raw["action"],
            inbox_id=raw["inbox_id"],
            created=raw["created"],
            updated=raw["updated"],
            idempotent=raw["idempotent"],
            row=raw["row"],
            message=raw["message"],
            errors=tuple(raw["errors"]),
        )


class DaArchiviareIntakeHttpClient:
    def __init__(self, url: str | None, token: str | None, *, timeout_seconds: float = 15.0,
                 opener: Callable[..., Any] = urlopen) -> None:
        self.url = (url or "").strip()
        self.token = (token or "").strip()
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def create_record(self, manifest_path: str | Path, *, drive_file_id: str,
                      manifest_file_id: str, form_url: str = "") -> DaArchiviareIntakeResponse:
        if not self.url:
            raise DaArchiviareIntakeUrlNotConfigured(
                "VIRGILIO_CARONTE_INTAKE_URL is not configured; network was not attempted"
            )
        if not self.token:
            raise DaArchiviareIntakeTokenNotConfigured(
                "VIRGILIO_TOKEN is not configured; network was not attempted"
            )
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise DaArchiviareIntakeClientError("Da archiviare URL must be an absolute HTTPS URL")
        payload = build_da_archiviare_intake_payload(
            manifest_path,
            drive_file_id=drive_file_id,
            manifest_file_id=manifest_file_id,
            form_url=form_url,
        )
        envelope = dict(payload)
        envelope["token"] = self.token
        forbidden = _find_forbidden_fields(envelope)
        if forbidden:
            raise DaArchiviareIntakeClientError(
                "payload contains forbidden fields: " + ", ".join(forbidden)
            )
        body = json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = Request(
            self.url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json; charset=utf-8",
                     "Accept": "application/json"},
        )
        try:
            response = self._opener(request, timeout=self.timeout_seconds)
            try:
                response_body = response.read()
            finally:
                close = getattr(response, "close", None)
                if close:
                    close()
        except TimeoutError as exc:
            raise DaArchiviareIntakeClientError("Da archiviare request timed out") from exc
        except HTTPError as exc:
            raise DaArchiviareIntakeClientError(
                f"Da archiviare returned HTTP {exc.code}"
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise DaArchiviareIntakeClientError("Da archiviare request timed out") from exc
            raise DaArchiviareIntakeClientError("Da archiviare network request failed") from exc
        try:
            decoded = json.loads(response_body.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise DaArchiviareIntakeClientError("Da archiviare returned invalid JSON") from exc
        result = DaArchiviareIntakeResponse.from_mapping(decoded)
        if result.ok and not result.inbox_id:
            raise DaArchiviareIntakeClientError("successful Da archiviare response is incomplete")
        return result


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
