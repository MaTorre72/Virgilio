from __future__ import annotations

from pathlib import Path
import sys


INSTALLER_DIR = Path(__file__).resolve().parents[1] / "installer"
sys.path.insert(0, str(INSTALLER_DIR))

from caronte_installer import InstallLayout, install, uninstall  # noqa: E402


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
    setup = tmp_path / "CaronteSetup.exe"
    setup.write_bytes(b"synthetic-installer")
    layout = _layout(tmp_path)
    shortcuts: list[tuple[Path, Path]] = []
    registrations: list[Path] = []

    executable = install(
        payload,
        setup,
        layout,
        shortcut_creator=lambda shortcut, target: (shortcut.parent.mkdir(parents=True), shortcut.write_text(str(target)), shortcuts.append((shortcut, target))),
        register_uninstall=registrations.append,
    )

    assert executable.read_bytes() == b"synthetic-caronte"
    assert (layout.program_dir / "runtime.dll").is_file()
    assert (layout.program_dir / "DisinstallaCaronte.exe").read_bytes() == b"synthetic-installer"
    assert shortcuts == [(layout.start_menu_dir / "Caronte.lnk", executable)]
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
    assert 'name="CaronteSetup"' in spec.read_text(encoding="utf-8")
    assert "CARONTE_INSTALL_ROOT" in smoke_script.read_text(encoding="utf-8")
