"""Safe local state reset helpers for the Virgilio local connector."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import shutil
import uuid

from .local_paths import LocalDataPaths
from .operation_lock import LocalOperationLock
from .readonly_state import ensure_state_db
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
    preserved: tuple[str, ...]
    reset: tuple[str, ...]
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

    with LocalOperationLock(root):
        if not root.exists():
            return ResetLocalStateResult(
                status="noop", local_root=str(root), backup_path=None,
                machine_id_preserved=False, preserved=(), reset=(),
                message="local data root not found; nothing to reset",
            )

        machine_id_text = _read_machine_id(root / "machine_id")
        backup_path = _backup_path(root)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(root, backup_path)
        if _inventory(root) != _inventory(backup_path):
            shutil.rmtree(backup_path)
            raise ResetLocalStateError("automatic backup verification failed")

        shutil.rmtree(root)
        paths = LocalDataPaths(root)
        paths.create()
        ensure_state_db(root)
        if machine_id_text is not None:
            (root / "machine_id").write_text(machine_id_text + "\n", encoding="utf-8")
            machine_id_preserved = True
        else:
            load_machine_id(root)
            machine_id_preserved = False

        return ResetLocalStateResult(
            status="completed", local_root=str(root), backup_path=str(backup_path),
            machine_id_preserved=machine_id_preserved,
            preserved=("configuration", "credentials", "machine_id"),
            reset=("state.db", "quarantine"),
            message="local data reset completed after verified backup",
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


def _inventory(root: Path) -> dict[str, tuple[int, str]]:
    inventory: dict[str, tuple[int, str]] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        inventory[path.relative_to(root).as_posix()] = (path.stat().st_size, digest)
    return inventory
