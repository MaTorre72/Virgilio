"""Safe local state reset helpers for the Virgilio local connector."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shutil
import uuid

from .local_paths import LocalDataPaths
from .time_utils import rome_timestamp
from .traceability import load_machine_id


class ResetLocalStateError(RuntimeError):
    """Raised when a local reset cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class ResetLocalStateResult:
    status: str
    local_root: str
    backup_path: str | None
    machine_id_preserved: bool
    message: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))


def reset_local_state(local_root: str | Path, *, backup: bool, confirm: bool) -> ResetLocalStateResult:
    root = Path(local_root)
    if not backup:
        raise ResetLocalStateError("reset-local-state requires --backup")
    if not confirm:
        raise ResetLocalStateError("reset-local-state requires explicit confirmation")

    if root.exists() and not root.is_dir():
        raise ResetLocalStateError(f"local data root is not a directory: {root}")

    if not root.exists():
        return ResetLocalStateResult(
            status="noop",
            local_root=str(root),
            backup_path=None,
            machine_id_preserved=False,
            message="local data root not found; nothing to reset",
        )

    machine_id_text = _read_machine_id(root / "machine_id")
    backup_path = _backup_path(root)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(root), str(backup_path))

    paths = LocalDataPaths(root)
    paths.create()
    if machine_id_text is not None:
        (root / "machine_id").write_text(machine_id_text + "\n", encoding="utf-8")
        machine_id_preserved = True
    else:
        load_machine_id(root)
        machine_id_preserved = False

    return ResetLocalStateResult(
        status="completed",
        local_root=str(root),
        backup_path=str(backup_path),
        machine_id_preserved=machine_id_preserved,
        message="local data reset completed",
    )


def _read_machine_id(path: Path) -> str | None:
    if not path.is_file():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return value or None


def _backup_path(root: Path) -> Path:
    stamp = rome_timestamp()
    suffix = uuid.uuid4().hex[:8]
    return root.parent / f"{root.name}.backup-{stamp}-{suffix}"
