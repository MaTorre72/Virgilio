"""Minimal metadata-only HTTP client for the Caronte dry-run bridge."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .contract import command_from_json


BRIDGE_ACTION = "local_imap_dry_run"
FORBIDDEN_FIELDS = frozenset(
    {"local_path", "file_path", "file_bytes", "base64", "content", "raw"}
)


class CaronteDryRunClientError(RuntimeError):
    """Safe client failure without request payload or sensitive response data."""


class CaronteDryRunUrlNotConfigured(CaronteDryRunClientError):
    pass


@dataclass(frozen=True, slots=True)
class CaronteBridgeResponse:
    ok: bool
    dry_run: bool
    accepted_attachments: int
    rejected_attachments: int
    limbo_drive_ids: tuple[Any, ...]
    bucoliche_rows: tuple[Any, ...]
    message: str
    errors: tuple[dict[str, Any], ...]

    @classmethod
    def from_mapping(cls, raw: Any) -> "CaronteBridgeResponse":
        if not isinstance(raw, dict):
            raise CaronteDryRunClientError("Caronte response must be a JSON object")
        required = {
            "ok", "dry_run", "accepted_attachments", "rejected_attachments",
            "limbo_drive_ids", "bucoliche_rows", "message", "errors",
        }
        if not required.issubset(raw):
            raise CaronteDryRunClientError("Caronte response is missing required fields")
        if not isinstance(raw["ok"], bool) or raw["dry_run"] is not True:
            raise CaronteDryRunClientError("Caronte response is not a valid dry-run result")
        for field in ("accepted_attachments", "rejected_attachments"):
            if isinstance(raw[field], bool) or not isinstance(raw[field], int) or raw[field] < 0:
                raise CaronteDryRunClientError(f"Caronte response field {field} is invalid")
        for field in ("limbo_drive_ids", "bucoliche_rows", "errors"):
            if not isinstance(raw[field], list):
                raise CaronteDryRunClientError(f"Caronte response field {field} is invalid")
        if raw["limbo_drive_ids"] or raw["bucoliche_rows"]:
            raise CaronteDryRunClientError("dry-run response must not contain persistent IDs")
        if not isinstance(raw["message"], str):
            raise CaronteDryRunClientError("Caronte response message is invalid")
        return cls(
            ok=raw["ok"], dry_run=True,
            accepted_attachments=raw["accepted_attachments"],
            rejected_attachments=raw["rejected_attachments"],
            limbo_drive_ids=tuple(raw["limbo_drive_ids"]),
            bucoliche_rows=tuple(raw["bucoliche_rows"]), message=raw["message"],
            errors=tuple(raw["errors"]),
        )


class CaronteDryRunHttpClient:
    def __init__(self, url: str | None, *, timeout_seconds: float = 15.0,
                 opener: Callable[..., Any] = urlopen) -> None:
        self.url = (url or "").strip()
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def send_command_file(self, path: str | Path) -> CaronteBridgeResponse:
        if not self.url:
            raise CaronteDryRunUrlNotConfigured(
                "VIRGILIO_CARONTE_DRY_RUN_URL is not configured; network was not attempted"
            )
        parsed_url = urlparse(self.url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise CaronteDryRunClientError("Caronte dry-run URL must be an absolute HTTPS URL")
        command_path = Path(path)
        try:
            raw = json.loads(command_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CaronteDryRunClientError("command file is not readable valid UTF-8 JSON") from exc
        forbidden = _find_forbidden_fields(raw)
        if forbidden:
            raise CaronteDryRunClientError("command contains forbidden non-metadata fields")
        try:
            command = command_from_json(json.dumps(raw, ensure_ascii=False))
        except ValueError as exc:
            raise CaronteDryRunClientError("command does not match the Caronte contract") from exc
        if not command.dry_run:
            raise CaronteDryRunClientError("only dry_run=true commands may be sent")
        envelope = json.dumps(
            {"action": BRIDGE_ACTION, "payload": command.to_dict()},
            ensure_ascii=False, separators=(",", ":"),
        ).encode("utf-8")
        request = Request(
            self.url, data=envelope, method="POST",
            headers={"Content-Type": "application/json; charset=utf-8",
                     "Accept": "application/json"},
        )
        try:
            response = self._opener(request, timeout=self.timeout_seconds)
            try:
                body = response.read()
            finally:
                close = getattr(response, "close", None)
                if close:
                    close()
        except TimeoutError as exc:
            raise CaronteDryRunClientError("Caronte dry-run request timed out") from exc
        except HTTPError as exc:
            raise CaronteDryRunClientError(
                f"Caronte dry-run returned HTTP {exc.code}"
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise CaronteDryRunClientError("Caronte dry-run request timed out") from exc
            raise CaronteDryRunClientError("Caronte dry-run network request failed") from exc
        try:
            decoded = json.loads(body.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise CaronteDryRunClientError("Caronte returned invalid JSON") from exc
        result = CaronteBridgeResponse.from_mapping(decoded)
        if result.accepted_attachments + result.rejected_attachments != len(command.attachments):
            raise CaronteDryRunClientError("Caronte response attachment counts are inconsistent")
        return result


def _find_forbidden_fields(value: Any) -> tuple[str, ...]:
    found: list[str] = []

    def visit(item: Any, path: str) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                child_path = f"{path}.{key}"
                if str(key).lower() in FORBIDDEN_FIELDS:
                    found.append(child_path)
                visit(child, child_path)
        elif isinstance(item, list):
            for index, child in enumerate(item):
                visit(child, f"{path}[{index}]")

    visit(value, "$")
    return tuple(found)
