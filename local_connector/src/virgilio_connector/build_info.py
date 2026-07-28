"""Validated identity of a packaged Caronte build."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping
from uuid import UUID


PRODUCT_NAME = "Caronte"
MANIFEST_FILENAME = "build_manifest.json"
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_SHORT_COMMIT_RE = re.compile(r"^[0-9a-f]{7,12}$")


class BuildInfoError(ValueError):
    """Raised when the packaged identity is missing or cannot be trusted."""


@dataclass(frozen=True, slots=True)
class BuildInfo:
    product_name: str
    version: str
    git_commit: str
    git_short_commit: str
    build_utc: str
    source_branch: str
    working_tree: str
    python_version: str
    pyinstaller_version: str
    build_id: str

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "BuildInfo":
        required = tuple(cls.__dataclass_fields__)
        missing = [key for key in required if key not in values]
        if missing:
            raise BuildInfoError(f"Campi build mancanti: {', '.join(missing)}")
        if any(not isinstance(values[key], str) or not values[key].strip() for key in required):
            raise BuildInfoError("Il manifest della build contiene valori non validi.")
        info = cls(**{key: values[key].strip() for key in required})
        info._validate()
        return info

    def _validate(self) -> None:
        if self.product_name != PRODUCT_NAME:
            raise BuildInfoError("Nome prodotto non valido.")
        if not _COMMIT_RE.fullmatch(self.git_commit):
            raise BuildInfoError("Commit Git non valido.")
        if not _SHORT_COMMIT_RE.fullmatch(self.git_short_commit):
            raise BuildInfoError("Commit Git abbreviato non valido.")
        if not self.git_commit.startswith(self.git_short_commit):
            raise BuildInfoError("I commit Git del manifest non coincidono.")
        if self.working_tree not in {"clean", "dirty"}:
            raise BuildInfoError("Stato working tree non valido.")
        try:
            parsed = datetime.fromisoformat(self.build_utc.replace("Z", "+00:00"))
        except ValueError as exc:
            raise BuildInfoError("Data build non valida.") from exc
        if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
            raise BuildInfoError("La data build deve essere UTC.")
        try:
            UUID(self.build_id)
        except ValueError as exc:
            raise BuildInfoError("Identificativo build non valido.") from exc

    def public_mapping(self) -> dict[str, str]:
        """Return the fields shared by --build-info and the About window."""

        return {
            "version": self.version,
            "commit": self.git_short_commit,
            "build_utc": self.build_utc,
            "build_id": self.build_id,
        }


def manifest_path() -> Path:
    override = os.environ.get("CARONTE_BUILD_MANIFEST_PATH", "").strip()
    if override:
        return Path(override)
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_root / "resources" / MANIFEST_FILENAME


def load_build_info(path: Path | None = None) -> BuildInfo:
    source = path or manifest_path()
    try:
        values = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildInfoError("Informazioni build assenti o illeggibili.") from exc
    if not isinstance(values, dict):
        raise BuildInfoError("Il manifest della build non e` un oggetto JSON.")
    return BuildInfo.from_mapping(values)


def build_info_json(info: BuildInfo) -> str:
    return json.dumps(info.public_mapping(), ensure_ascii=True, sort_keys=True)
