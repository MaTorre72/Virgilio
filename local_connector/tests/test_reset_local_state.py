from pathlib import Path
import json

import pytest

from virgilio_connector.__main__ import main
from virgilio_connector.reset_local_state import ResetLocalStateError, reset_local_state
from virgilio_connector.operation_lock import LocalOperationBusyError, LocalOperationLock


def seed_local_root(root: Path) -> None:
    (root / "quarantine" / "incoming").mkdir(parents=True, exist_ok=True)
    (root / "quarantine" / "incoming" / "note.txt").write_text("payload", encoding="utf-8")
    (root / "logs").mkdir(parents=True, exist_ok=True)
    (root / "logs" / "run.log").write_text("log", encoding="utf-8")
    (root / "reports").mkdir(parents=True, exist_ok=True)
    (root / "reports" / "report.json").write_text("{}", encoding="utf-8")
    (root / "state.db").write_text("sqlite", encoding="utf-8")
    (root / "machine_id").write_text("machine-test\n", encoding="utf-8")


def test_reset_local_state_creates_backup_and_rebuilds_baseline(tmp_path):
    root = tmp_path / ".local_data"
    seed_local_root(root)

    result = reset_local_state(root, backup=True, confirm=True)

    assert result.status == "completed"
    assert result.backup_path is not None
    backup = Path(result.backup_path)
    assert backup.parent == root.parent
    assert backup.name.startswith(".local_data.backup-")
    assert backup.is_dir()
    assert (backup / "state.db").read_text(encoding="utf-8") == "sqlite"
    assert (backup / "quarantine" / "incoming" / "note.txt").read_text(encoding="utf-8") == "payload"
    assert (backup / "reports" / "report.json").read_text(encoding="utf-8") == "{}"
    assert result.machine_id_preserved is True
    assert (root / "machine_id").read_text(encoding="utf-8") == "machine-test\n"
    assert (root / "state.db").is_file()
    assert (root / "quarantine" / "incoming").is_dir()
    assert not any((root / "quarantine" / "incoming").iterdir())
    assert (root / "logs").is_dir()
    assert result.preserved == ("configuration", "credentials", "machine_id")
    assert result.reset == ("state.db", "quarantine")


def test_reset_refuses_active_worker_lock_without_changing_data(tmp_path):
    root = tmp_path / ".local_data"
    seed_local_root(root)

    with LocalOperationLock(root):
        with pytest.raises(LocalOperationBusyError):
            reset_local_state(root, backup=True, confirm=True)

    assert (root / "state.db").read_text(encoding="utf-8") == "sqlite"
    assert not tuple(tmp_path.glob(".local_data.backup-*"))


def test_backup_is_verified_before_local_root_is_changed(tmp_path, monkeypatch):
    root = tmp_path / ".local_data"
    seed_local_root(root)
    inventories = iter(({"state.db": (6, "source")}, {"state.db": (6, "backup")}))
    monkeypatch.setattr(
        "virgilio_connector.reset_local_state._inventory", lambda path: next(inventories)
    )

    with pytest.raises(ResetLocalStateError, match="verification failed"):
        reset_local_state(root, backup=True, confirm=True)

    assert (root / "state.db").read_text(encoding="utf-8") == "sqlite"
    assert not tuple(tmp_path.glob(".local_data.backup-*"))


def test_reset_local_state_requires_backup_and_confirmation(tmp_path):
    root = tmp_path / ".local_data"
    seed_local_root(root)

    with pytest.raises(ResetLocalStateError, match="--backup"):
        reset_local_state(root, backup=False, confirm=True)
    with pytest.raises(ResetLocalStateError, match="explicit confirmation"):
        reset_local_state(root, backup=True, confirm=False)


def test_reset_local_state_cli_returns_json_and_resets(tmp_path, monkeypatch, capsys):
    root = tmp_path / ".local_data"
    seed_local_root(root)
    monkeypatch.setenv("VIRGILIO_LOCAL_DATA_DIR", str(root))
    monkeypatch.setattr(
        "sys.argv",
        ["virgilio_connector", "reset-local-state", "--backup", "--confirm"],
    )

    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["backup_path"]
    assert Path(payload["backup_path"]).is_dir()
    assert (root / "machine_id").read_text(encoding="utf-8") == "machine-test\n"
    assert (root / "state.db").is_file()
