"""Metadata-only client for the controlled Drive staging test intake."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


INTAKE_DRIVE_STAGING_TEST_ACTION = "intake_drive_staging_test"


class DriveStagingIntakeTestError(RuntimeError):
    pass


class DriveStagingIntakeTestUrlNotConfigured(DriveStagingIntakeTestError):
    pass


@dataclass(frozen=True, slots=True)
class DriveStagingIntakeTestResponse:
    ok: bool
    test_mode: bool
    action: str
    attachment_id: str
    staged_filename: str
    drive_file_found: bool
    manifest_found: bool
    manifest_consistent: bool
    test_row_written: bool
    state: str
    message: str
    errors: tuple[dict[str, Any], ...]

    @classmethod
    def from_mapping(cls, raw: Any) -> "DriveStagingIntakeTestResponse":
        if not isinstance(raw, dict):
            raise DriveStagingIntakeTestError("intake test response must be a JSON object")
        required = {
            "ok", "test_mode", "action", "attachment_id", "staged_filename",
            "drive_file_found", "manifest_found", "manifest_consistent",
            "test_row_written", "state", "message", "errors",
        }
        if not required.issubset(raw):
            raise DriveStagingIntakeTestError("intake test response is missing required fields")
        if raw["test_mode"] is not True or raw["action"] != INTAKE_DRIVE_STAGING_TEST_ACTION:
            raise DriveStagingIntakeTestError("response is not a staging test intake result")
        for field in ("ok", "drive_file_found", "manifest_found",
                      "manifest_consistent", "test_row_written"):
            if not isinstance(raw[field], bool):
                raise DriveStagingIntakeTestError(f"intake response field {field} is invalid")
        if not isinstance(raw["message"], str) or not isinstance(raw["errors"], list):
            raise DriveStagingIntakeTestError("intake response error fields are invalid")
        if raw["ok"] and (not raw["test_row_written"] or raw["state"] != "presa_in_carico_test"):
            raise DriveStagingIntakeTestError("successful intake response is inconsistent")
        return cls(
            ok=raw["ok"], test_mode=True, action=raw["action"],
            attachment_id=str(raw["attachment_id"]),
            staged_filename=str(raw["staged_filename"]),
            drive_file_found=raw["drive_file_found"],
            manifest_found=raw["manifest_found"],
            manifest_consistent=raw["manifest_consistent"],
            test_row_written=raw["test_row_written"], state=str(raw["state"]),
            message=raw["message"], errors=tuple(raw["errors"]),
        )


class DriveStagingIntakeTestClient:
    def __init__(self, url: str | None, *, timeout_seconds: float = 15.0,
                 opener: Callable[..., Any] = urlopen) -> None:
        self.url = (url or "").strip()
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def intake_manifest(self, manifest_path: str | Path) -> DriveStagingIntakeTestResponse:
        if not self.url:
            raise DriveStagingIntakeTestUrlNotConfigured(
                "VIRGILIO_CARONTE_INTAKE_TEST_URL is not configured; network was not attempted"
            )
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise DriveStagingIntakeTestError("intake test URL must be an absolute HTTPS URL")
        payload = _intake_payload_from_manifest(_read_intake_manifest(manifest_path))
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = Request(self.url, data=body, method="POST", headers={
            "Content-Type": "application/json; charset=utf-8", "Accept": "application/json",
        })
        try:
            response = self._opener(request, timeout=self.timeout_seconds)
            try:
                response_body = response.read()
            finally:
                close = getattr(response, "close", None)
                if close:
                    close()
        except TimeoutError as exc:
            raise DriveStagingIntakeTestError("staging intake test request timed out") from exc
        except HTTPError as exc:
            raise DriveStagingIntakeTestError(f"staging intake test returned HTTP {exc.code}") from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise DriveStagingIntakeTestError("staging intake test request timed out") from exc
            raise DriveStagingIntakeTestError("staging intake test network request failed") from exc
        try:
            decoded = json.loads(response_body.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise DriveStagingIntakeTestError("staging intake test returned invalid JSON") from exc
        result = DriveStagingIntakeTestResponse.from_mapping(decoded)
        if result.attachment_id != payload["attachment_id"] or result.staged_filename != payload["staged_filename"]:
            raise DriveStagingIntakeTestError("intake response does not match the request")
        return result


def _read_intake_manifest(path: str | Path) -> dict[str, Any]:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DriveStagingIntakeTestError("local staging manifest was not found") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DriveStagingIntakeTestError("local staging manifest is not valid UTF-8 JSON") from exc
    if not isinstance(raw, dict):
        raise DriveStagingIntakeTestError("local staging manifest must be a JSON object")
    return raw


def _intake_payload_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "connector_type", "account_alias", "source_message_id", "source_message_uid",
        "attachment_id", "original_filename", "staged_filename", "sha256", "size_bytes",
        "mime_type", "scan_engine", "scan_result", "quarantine_status", "note",
    )
    if not set(fields).issubset(manifest):
        raise DriveStagingIntakeTestError("local staging manifest is missing required fields")
    filename = manifest["staged_filename"]
    digest = manifest["sha256"]
    size = manifest["size_bytes"]
    if not isinstance(filename, str) or Path(filename).name != filename or "/" in filename or "\\" in filename:
        raise DriveStagingIntakeTestError("manifest staged_filename is invalid")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise DriveStagingIntakeTestError("manifest sha256 is invalid")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise DriveStagingIntakeTestError("manifest size_bytes is invalid")
    payload = {field: manifest[field] for field in fields}
    payload.update({"action": INTAKE_DRIVE_STAGING_TEST_ACTION, "test_mode": True})
    return payload
