from __future__ import annotations

from pathlib import Path
import json
import sys
from types import SimpleNamespace

import pytest


INSTALLER_DIR = Path(__file__).resolve().parents[1] / "installer"
sys.path.insert(0, str(INSTALLER_DIR))

import caronte_installer  # noqa: E402
from caronte_installer import InstallLayout, install, uninstall  # noqa: E402


def _write_payload_manifest(payload: Path) -> None:
    resources = payload / "_internal" / "resources"
    resources.mkdir(parents=True)
    (resources / "build_manifest.json").write_text(
        json.dumps(
            {
                "version": "0.11.0",
                "git_commit": "a1b2c3d4e5f67890123456789012345678901234",
                "git_short_commit": "a1b2c3d",
                "build_id": "12345678-1234-4abc-8def-1234567890ab",
            }
        ),
        encoding="utf-8",
    )


def _layout(tmp_path: Path) -> InstallLayout:
    return InstallLayout(
        program_dir=tmp_path / "local" / "Programs" / "Caronte",
        start_menu_dir=tmp_path / "roaming" / "Start Menu" / "Caronte",
        config_dir=tmp_path / "roaming" / "Caronte",
        data_dir=tmp_path / "local" / "Caronte",
    )


def test_install_creates_program_shortcut_and_uninstaller_without_data(tmp_path: Path) -> None:
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / "Caronte.exe").write_bytes(b"synthetic-caronte")
    (payload / "runtime.dll").write_bytes(b"synthetic-runtime")
    _write_payload_manifest(payload)
    setup = tmp_path / "CaronteSetup.exe"
    setup.write_bytes(b"synthetic-installer")
    layout = _layout(tmp_path)
    shortcuts: list[tuple[Path, Path, str]] = []
    registrations: list[Path] = []

    executable = install(
        payload,
        setup,
        layout,
        shortcut_creator=lambda shortcut, target, arguments: (
            shortcut.parent.mkdir(parents=True, exist_ok=True),
            shortcut.write_text(f"{target}\n{arguments}"),
            shortcuts.append((shortcut, target, arguments)),
        ),
        register_uninstall=registrations.append,
    )

    assert executable.read_bytes() == b"synthetic-caronte"
    assert (layout.program_dir / "runtime.dll").is_file()
    assert (layout.program_dir / "DisinstallaCaronte.exe").read_bytes() == b"synthetic-installer"
    assert shortcuts == [
        (layout.start_menu_dir / "Caronte.lnk", executable, ""),
        (
            layout.start_menu_dir / "Caronte Manutenzione.lnk",
            executable,
            f'maintenance-gui --config "{layout.config_dir / "config.yaml"}"',
        ),
    ]
    assert registrations == [layout.program_dir / "DisinstallaCaronte.exe"]
    assert not layout.config_dir.exists()
    assert not layout.data_dir.exists()


def test_uninstall_removes_program_and_shortcut_but_preserves_user_data(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    layout.program_dir.mkdir(parents=True)
    (layout.program_dir / "Caronte.exe").write_bytes(b"program")
    layout.start_menu_dir.mkdir(parents=True)
    (layout.start_menu_dir / "Caronte.lnk").write_bytes(b"shortcut")
    layout.config_dir.mkdir(parents=True)
    (layout.config_dir / "config.yaml").write_text("synthetic: true", encoding="utf-8")
    layout.data_dir.mkdir(parents=True)
    (layout.data_dir / "registro.db").write_bytes(b"synthetic-data")
    unregistered: list[bool] = []

    uninstall(layout, unregister_uninstall=lambda: unregistered.append(True))

    assert not layout.program_dir.exists()
    assert not layout.start_menu_dir.exists()
    assert (layout.config_dir / "config.yaml").is_file()
    assert (layout.data_dir / "registro.db").is_file()
    assert unregistered == [True]


def test_uninstall_removes_automatic_startup_before_program_files(tmp_path: Path) -> None:
    layout = _layout(tmp_path)
    layout.program_dir.mkdir(parents=True)
    (layout.program_dir / "Caronte.exe").write_bytes(b"program")
    calls: list[str] = []

    uninstall(
        layout,
        unregister_uninstall=lambda: calls.append("unregister"),
        remove_automatic_startup=lambda: calls.append("automatic"),
    )

    assert calls == ["automatic", "unregister"]
    assert not layout.program_dir.exists()


def test_automatic_startup_cleanup_removes_gui_worker_and_legacy_task(monkeypatch) -> None:
    saved = {
        "Caronte": "Caronte.exe user-gui",
        "Caronte - controllo automatico": "Caronte.exe watch",
    }
    class FakeKey:
        def __enter__(self): return self
        def __exit__(self, *args): return None

    fake_winreg = SimpleNamespace(
        HKEY_CURRENT_USER=object(),
        KEY_SET_VALUE=1,
        OpenKey=lambda *args: FakeKey(),
        DeleteValue=lambda opened, name: saved.pop(name),
    )
    calls = []
    monkeypatch.setitem(sys.modules, "winreg", fake_winreg)
    monkeypatch.setattr(
        caronte_installer.subprocess,
        "run",
        lambda args, **kwargs: calls.append(args),
    )

    caronte_installer._remove_automatic_startup()

    assert saved == {}
    assert calls == [
        ["schtasks", "/end", "/tn", "Caronte - controllo automatico"],
        ["schtasks", "/delete", "/tn", "Caronte - controllo automatico", "/f"],
    ]


def test_layout_separates_program_configuration_and_data(tmp_path: Path) -> None:
    layout = InstallLayout.from_environment(
        {"USERPROFILE": str(tmp_path), "LOCALAPPDATA": str(tmp_path / "local"), "APPDATA": str(tmp_path / "roaming")}
    )

    assert layout.program_dir == tmp_path / "local" / "Programs" / "Caronte"
    assert layout.config_dir == tmp_path / "roaming" / "Caronte"
    assert layout.data_dir == tmp_path / "local" / "Caronte"
    assert len({layout.program_dir, layout.config_dir, layout.data_dir}) == 3


def test_installer_build_and_smoke_scripts_are_declared() -> None:
    repo = Path(__file__).resolve().parents[2]
    build_script = repo / "scripts" / "dev" / "build_caronte_installer.ps1"
    smoke_script = repo / "scripts" / "dev" / "smoke_caronte_installer.ps1"
    spec = INSTALLER_DIR / "CaronteSetup.spec"

    assert build_script.is_file()
    assert smoke_script.is_file()
    assert spec.is_file()
    spec_text = spec.read_text(encoding="utf-8")
    build_text = build_script.read_text(encoding="utf-8")
    smoke_text = smoke_script.read_text(encoding="utf-8")
    assert "CARONTE_INSTALLER_BASENAME" in spec_text
    assert "CaronteSetup-$($BuildManifest.version)-$($BuildManifest.git_short_commit)" in build_text
    assert "installer_sha256" in build_text
    assert "smoke_installer_result" in build_text
    assert "oauth_client_included" in build_text
    assert "HumanAcceptanceBuild" in build_text
    assert "--build-info" in smoke_text
    assert "CARONTE_UNINSTALL_KEY" in smoke_text
    assert "DisplayVersion" in smoke_text


def test_install_rejects_payload_without_build_identity(tmp_path: Path) -> None:
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / "Caronte.exe").write_bytes(b"synthetic-caronte")

    with pytest.raises(FileNotFoundError, match="identita"):
        install(payload, tmp_path / "setup.exe", _layout(tmp_path))
