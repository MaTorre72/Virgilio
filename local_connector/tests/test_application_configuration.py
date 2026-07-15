from dataclasses import replace
import builtins
import importlib
from pathlib import Path
import sys

import pytest

from virgilio_connector.application.configuration import ConfigurationService
from virgilio_connector.multi_account import MultiAccountConfigError, scaffold_local_config


def configuration_file(tmp_path: Path) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(scaffold_local_config(
        email="account.1@example.invalid", staging_dir=(tmp_path / "limbo").resolve()
    ), encoding="utf-8")
    return path


def test_round_trip_has_one_authoritative_source_and_two_accounts(tmp_path):
    path = configuration_file(tmp_path)
    service = ConfigurationService.for_file(path)
    model = service.load()
    second = replace(
        model.accounts[0],
        account_alias="account_2",
        email="account.2@example.invalid",
        username_env="VIRGILIO_IMAP_ACCOUNT_2_USERNAME",
        password_env="VIRGILIO_IMAP_ACCOUNT_2_PASSWORD",
    )

    service.save(replace(model, accounts=(*model.accounts, second)))

    loaded = service.load()
    assert [account.account_alias for account in loaded.accounts] == ["account_1", "account_2"]
    assert loaded.storage == model.storage
    assert service.field_sources() == {"accounts.*": path, "storage.*": path}
    assert "bucoliche:" in path.read_text(encoding="utf-8")


def test_service_import_does_not_require_a_gui_toolkit(monkeypatch):
    module_name = "virgilio_connector.application.configuration"
    original_import = builtins.__import__

    def reject_toolkits(name, *args, **kwargs):
        if name in {"tkinter", "PySide6", "PyQt6"}:
            raise AssertionError(f"unexpected toolkit import: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", reject_toolkits)
    module = importlib.reload(sys.modules[module_name])
    assert module.ConfigurationService is not None


def test_atomic_write_failure_preserves_existing_file(tmp_path, monkeypatch):
    path = configuration_file(tmp_path)
    before = path.read_bytes()
    service = ConfigurationService.for_file(path)

    def fail_replace(self, target):
        raise OSError("synthetic replace failure")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(MultiAccountConfigError, match="previous file preserved"):
        service.save(service.load())
    assert path.read_bytes() == before


def test_scan_cli_uses_shared_configuration_service(tmp_path, monkeypatch, capsys):
    import virgilio_connector.__main__ as cli

    path = configuration_file(tmp_path)
    model = ConfigurationService.for_file(path).load()
    seen = {}

    class FakeService:
        @classmethod
        def for_file(cls, received):
            seen["path"] = received
            return cls()

        def load(self):
            seen["loaded"] = True
            return replace(model, accounts=(replace(model.accounts[0], enabled=False),))

    monkeypatch.setattr(cli, "ConfigurationService", FakeService)
    monkeypatch.setattr(cli, "_local_data_root", lambda: tmp_path / "data")
    monkeypatch.setattr(sys, "argv", [
        "virgilio", "scan-imap-accounts", "--config", str(path), "--dry-run"
    ])

    assert cli.main() == 0
    assert seen == {"path": path, "loaded": True}
    assert '"status":"disabled"' in capsys.readouterr().out
