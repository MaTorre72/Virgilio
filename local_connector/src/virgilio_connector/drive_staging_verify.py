"""Read-only cloud visibility check for locally staged Drive Desktop files."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DRIVE_STAGING_VERIFY_ACTION = "verify_drive_staging"


class DriveStagingVerifyError(RuntimeError):
    pass


class DriveStagingVerifyUrlNotConfigured(DriveStagingVerifyError):
    pass


@dataclass(frozen=True, slots=True)
class DriveStagingVerifyResponse:
    ok: bool
    dry_run: bool
    action: str
    attachment_id: str
    staged_filename: str
    file_found: bool
    manifest_found: bool
    manifest_consistent: bool
    cloud_visible: bool
    drive_file_id: str
    manifest_file_id: str
    message: str
    errors: tuple[dict[str, Any], ...]

    @classmethod
    def from_mapping(cls, raw: Any) -> "DriveStagingVerifyResponse":
        if not isinstance(raw, dict):
            raise DriveStagingVerifyError("Drive verify response must be a JSON object")
        required = {
            "ok", "dry_run", "action", "attachment_id", "staged_filename",
            "file_found", "manifest_found", "manifest_consistent",
            "inbox_preview", "cloud_visible", "message", "errors",
        }
        if not required.issubset(raw):
            raise DriveStagingVerifyError("Drive verify response is missing required fields")
        if raw["dry_run"] is not True or raw["action"] != DRIVE_STAGING_VERIFY_ACTION:
            raise DriveStagingVerifyError("response is not a Drive staging dry-run result")
        for field in ("ok", "file_found", "manifest_found", "manifest_consistent", "cloud_visible"):
            if not isinstance(raw[field], bool):
                raise DriveStagingVerifyError(f"Drive verify response field {field} is invalid")
        if not isinstance(raw["errors"], list) or not isinstance(raw["message"], str):
            raise DriveStagingVerifyError("Drive verify response error fields are invalid")
        if raw["cloud_visible"] and not (
            raw["ok"] and raw["file_found"] and raw["manifest_found"] and raw["manifest_consistent"]
        ):
            raise DriveStagingVerifyError("cloud_visible response is inconsistent")
        preview = raw["inbox_preview"]
        if preview is not None and not isinstance(preview, dict):
            raise DriveStagingVerifyError("Drive verify response inbox_preview is invalid")
        drive_file_id_raw = (preview or {}).get("drive_file_id", "")
        manifest_file_id_raw = (preview or {}).get("manifest_file_id", "")
        if not isinstance(drive_file_id_raw, str) or not isinstance(
            manifest_file_id_raw, str
        ):
            raise DriveStagingVerifyError("Drive verify response identifiers are invalid")
        drive_file_id = drive_file_id_raw.strip()
        manifest_file_id = manifest_file_id_raw.strip()
        if raw["cloud_visible"] and (not drive_file_id or not manifest_file_id):
            raise DriveStagingVerifyError(
                "cloud-visible response is missing Drive identifiers"
            )
        if any("/" in value or "\\" in value for value in (drive_file_id, manifest_file_id)):
            raise DriveStagingVerifyError("Drive verify response identifiers are invalid")
        return cls(
            ok=raw["ok"], dry_run=True, action=raw["action"],
            attachment_id=str(raw["attachment_id"]),
            staged_filename=str(raw["staged_filename"]),
            file_found=raw["file_found"], manifest_found=raw["manifest_found"],
            manifest_consistent=raw["manifest_consistent"],
            cloud_visible=raw["cloud_visible"],
            drive_file_id=drive_file_id,
            manifest_file_id=manifest_file_id,
            message=raw["message"],
            errors=tuple(raw["errors"]),
        )


class DriveStagingVerifyClient:
    def __init__(self, url: str | None, *, timeout_seconds: float = 15.0,
                 opener: Callable[..., Any] = urlopen) -> None:
        self.url = (url or "").strip()
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def verify_manifest(self, manifest_path: str | Path) -> DriveStagingVerifyResponse:
        if not self.url:
            raise DriveStagingVerifyUrlNotConfigured(
                "VIRGILIO_CARONTE_DRIVE_VERIFY_URL is not configured; network was not attempted"
            )
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise DriveStagingVerifyError("Drive verify URL must be an absolute HTTPS URL")
        manifest = _read_manifest(manifest_path)
        payload = _payload_from_manifest(manifest)
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = Request(
            self.url, data=body, method="POST",
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
            raise DriveStagingVerifyError("Drive staging verify request timed out") from exc
        except HTTPError as exc:
            raise DriveStagingVerifyError(f"Drive staging verify returned HTTP {exc.code}") from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise DriveStagingVerifyError("Drive staging verify request timed out") from exc
            raise DriveStagingVerifyError("Drive staging verify network request failed") from exc
        try:
            decoded = json.loads(response_body.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise DriveStagingVerifyError("Drive staging verify returned invalid JSON") from exc
        result = DriveStagingVerifyResponse.from_mapping(decoded)
        if (result.attachment_id != payload["attachment_id"] or
                result.staged_filename != payload["staged_filename"]):
            raise DriveStagingVerifyError("Drive verify response does not match the request")
        return result


def _read_manifest(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DriveStagingVerifyError("local staging manifest was not found") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DriveStagingVerifyError("local staging manifest is not valid UTF-8 JSON") from exc
    if not isinstance(raw, dict):
        raise DriveStagingVerifyError("local staging manifest must be a JSON object")
    return raw


def _payload_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    required = {"attachment_id", "staged_filename", "sha256", "size_bytes"}
    if not required.issubset(manifest):
        raise DriveStagingVerifyError("local staging manifest is missing required fields")
    attachment_id = manifest["attachment_id"]
    filename = manifest["staged_filename"]
    digest = manifest["sha256"]
    size = manifest["size_bytes"]
    if not isinstance(attachment_id, str) or not attachment_id.startswith("att-"):
        raise DriveStagingVerifyError("manifest attachment_id is invalid")
    if (not isinstance(filename, str) or not filename.strip() or
            Path(filename).name != filename or "/" in filename or "\\" in filename):
        raise DriveStagingVerifyError("manifest staged_filename is invalid")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise DriveStagingVerifyError("manifest sha256 is invalid")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise DriveStagingVerifyError("manifest size_bytes is invalid")
    return {
        "action": DRIVE_STAGING_VERIFY_ACTION,
        "dry_run": True,
        "attachment_id": attachment_id,
        "staged_filename": filename,
        "sha256": digest,
        "size_bytes": size,
    }
