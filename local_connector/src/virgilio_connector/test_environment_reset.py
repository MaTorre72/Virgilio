"""Metadata-only client and coordinator for the controlled TEST reset."""

from __future__ import annotations

__test__ = False

from dataclasses import dataclass
import json
from pathlib import Path
import re
import sqlite3
from typing import Any, Callable, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .application.maintenance import MaintenanceResetResult, MaintenanceService


TEST_ENVIRONMENT_RESET_ACTION = "reset_test_environment"
_RESET_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{7,127}$")
_FORBIDDEN = frozenset({
    "local_path", "file_path", "path", "bytes", "base64", "content", "raw",
    "token", "secret", "credential",
})


class TestEnvironmentResetError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class TestEnvironmentResetResponse:
    ok: bool
    mode: str
    reset_id: str
    phase: str
    completed: bool
    targets: Mapping[str, Any]
    backups: Mapping[str, Any]
    errors: tuple[Mapping[str, Any], ...]

    @classmethod
    def from_mapping(cls, raw: Any, *, mode: str, reset_id: str) -> "TestEnvironmentResetResponse":
        required = {"ok", "test_mode", "action", "mode", "reset_id", "phase",
                    "completed", "targets", "backups", "errors"}
        if not isinstance(raw, dict) or not required.issubset(raw):
            raise TestEnvironmentResetError("TEST reset response is incomplete")
        if (raw["test_mode"] is not True or raw["action"] != TEST_ENVIRONMENT_RESET_ACTION
                or raw["mode"] != mode or raw["reset_id"] != reset_id):
            raise TestEnvironmentResetError("TEST reset response does not match the request")
        if not isinstance(raw["ok"], bool) or not isinstance(raw["completed"], bool):
            raise TestEnvironmentResetError("TEST reset response status is invalid")
        if not isinstance(raw["targets"], dict) or not isinstance(raw["backups"], dict):
            raise TestEnvironmentResetError("TEST reset response metadata is invalid")
        if not isinstance(raw["errors"], list) or not isinstance(raw["phase"], str):
            raise TestEnvironmentResetError("TEST reset response errors are invalid")
        return cls(raw["ok"], mode, reset_id, raw["phase"], raw["completed"],
                   raw["targets"], raw["backups"], tuple(raw["errors"]))


class TestEnvironmentResetRemote(Protocol):
    def request(self, reset_id: str, mode: str) -> TestEnvironmentResetResponse: ...


class TestEnvironmentResetHttpClient:
    def __init__(self, url: str | None, token: str | None, *, timeout_seconds: float = 30.0,
                 opener: Callable[..., Any] = urlopen) -> None:
        self.url = (url or "").strip()
        self.token = (token or "").strip()
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def request(self, reset_id: str, mode: str) -> TestEnvironmentResetResponse:
        if not _RESET_ID.fullmatch(reset_id):
            raise TestEnvironmentResetError("reset_id is invalid")
        if mode not in {"preview", "prepare", "execute"}:
            raise TestEnvironmentResetError("TEST reset mode is invalid")
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise TestEnvironmentResetError("TEST reset URL must be an absolute HTTPS URL")
        if not self.token:
            raise TestEnvironmentResetError("TEST reset token is not configured")
        payload = {"action": TEST_ENVIRONMENT_RESET_ACTION, "test_mode": True,
                   "reset_id": reset_id, "mode": mode, "token": self.token}
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        try:
            response = self._opener(Request(self.url, data=body, method="POST", headers={
                "Content-Type": "application/json; charset=utf-8", "Accept": "application/json",
            }), timeout=self.timeout_seconds)
            try:
                raw = json.loads(response.read().decode("utf-8"))
            finally:
                close = getattr(response, "close", None)
                if close:
                    close()
        except TimeoutError as exc:
            raise TestEnvironmentResetError("TEST reset request timed out") from exc
        except HTTPError as exc:
            raise TestEnvironmentResetError(f"TEST reset returned HTTP {exc.code}") from exc
        except URLError as exc:
            raise TestEnvironmentResetError("TEST reset network request failed") from exc
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise TestEnvironmentResetError("TEST reset returned invalid JSON") from exc
        if _find_forbidden(raw):
            raise TestEnvironmentResetError("TEST reset response contains forbidden data")
        return TestEnvironmentResetResponse.from_mapping(raw, mode=mode, reset_id=reset_id)


@dataclass(frozen=True, slots=True)
class TestEnvironmentPreview:
    reset_id: str
    local_files: tuple[str, ...]
    local_rows: Mapping[str, int]
    remote: TestEnvironmentResetResponse


@dataclass(frozen=True, slots=True)
class TestEnvironmentResetResult:
    status: str
    reset_id: str
    local: MaintenanceResetResult
    remote: TestEnvironmentResetResponse


class TestEnvironmentResetService:
    def __init__(self, maintenance: MaintenanceService,
                 remote: TestEnvironmentResetRemote) -> None:
        self.maintenance = maintenance
        self.remote = remote

    def preview(self, reset_id: str) -> TestEnvironmentPreview:
        response = self.remote.request(reset_id, "preview")
        if not response.ok:
            raise TestEnvironmentResetError("TEST reset preview was refused")
        root = self.maintenance.data_root
        files = tuple(sorted(
            item.relative_to(root).as_posix() for item in root.rglob("*") if item.is_file()
        )) if root.is_dir() else ()
        return TestEnvironmentPreview(reset_id, files, _local_row_counts(root / "state.db"), response)

    def reset(self, reset_id: str, *, confirmed: bool) -> TestEnvironmentResetResult:
        if not confirmed:
            raise TestEnvironmentResetError("TEST reset requires explicit confirmation")
        preview = self.preview(reset_id)
        prepared = self.remote.request(reset_id, "prepare")
        if not prepared.ok or prepared.phase != "prepared":
            raise TestEnvironmentResetError("TEST remote backups were not completed")
        local = self.maintenance.reset(confirmed=True, reset_id=reset_id)
        if local.status not in {"completed", "idempotent"}:
            raise TestEnvironmentResetError(f"local TEST reset did not complete: {local.status}")
        remote = self.remote.request(reset_id, "execute")
        if not remote.ok or not remote.completed:
            raise TestEnvironmentResetError("TEST remote reset did not complete")
        if not _remote_reset_consistent(preview.remote.targets, remote.targets):
            raise TestEnvironmentResetError("TEST remote reset left data or changed the schema")
        return TestEnvironmentResetResult("completed", reset_id, local, remote)


def _local_row_counts(database: Path) -> dict[str, int]:
    if not database.is_file():
        return {}
    uri = f"file:{database.resolve().as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        return {name: int(connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
                for name in tables}
    finally:
        connection.close()


def _find_forbidden(value: Any, prefix: str = "") -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            current = f"{prefix}.{key}" if prefix else str(key)
            if str(key).lower() in _FORBIDDEN:
                found.append(current)
            found.extend(_find_forbidden(item, current))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_find_forbidden(item, f"{prefix}[{index}]"))
    return tuple(found)


def _remote_reset_consistent(before: Mapping[str, Any], after: Mapping[str, Any]) -> bool:
    try:
        empty = (after["registry"]["rows"] == [] and after["inbox"]["rows"] == []
                 and after["limbo"]["files"] == [])
        schemas = (after["registry"]["schema"] == before["registry"]["schema"]
                   and after["inbox"]["schema"] == before["inbox"]["schema"])
    except (KeyError, TypeError):
        return False
    return empty and schemas
