"""Per-user Windows installer for the standalone Caronte distribution."""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, Mapping


PRODUCT_NAME = "Caronte"
PRODUCT_VERSION = "0.11.0"
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Caronte"
STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_VALUE = "Caronte"
AUTOMATIC_TASK_NAME = "Caronte - controllo automatico"


@dataclass(frozen=True, slots=True)
class InstallLayout:
    program_dir: Path
    start_menu_dir: Path
    config_dir: Path
    data_dir: Path

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> "InstallLayout":
        values = os.environ if environ is None else environ
        home = Path(values.get("USERPROFILE") or Path.home())
        local = Path(values.get("LOCALAPPDATA") or home / "AppData" / "Local")
        roaming = Path(values.get("APPDATA") or home / "AppData" / "Roaming")
        return cls(
            program_dir=Path(values.get("CARONTE_INSTALL_ROOT") or local / "Programs" / PRODUCT_NAME),
            start_menu_dir=Path(
                values.get("CARONTE_START_MENU_ROOT")
                or roaming / "Microsoft" / "Windows" / "Start Menu" / "Programs" / PRODUCT_NAME
            ),
            config_dir=roaming / PRODUCT_NAME,
            data_dir=local / PRODUCT_NAME,
        )


def payload_root() -> Path:
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_root / "payload" / PRODUCT_NAME


def _create_shortcut(shortcut: Path, target: Path) -> None:
    shortcut.parent.mkdir(parents=True, exist_ok=True)
    escaped_shortcut = str(shortcut).replace("'", "''")
    escaped_target = str(target).replace("'", "''")
    command = (
        "$shell=New-Object -ComObject WScript.Shell;"
        f"$link=$shell.CreateShortcut('{escaped_shortcut}');"
        f"$link.TargetPath='{escaped_target}';"
        f"$link.WorkingDirectory='{str(target.parent).replace("'", "''")}';"
        "$link.Save()"
    )
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        check=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _register_uninstall(uninstaller: Path) -> None:
    import winreg

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, PRODUCT_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, PRODUCT_VERSION)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Virgilio")
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(uninstaller.parent))
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller}" /UNINSTALL')
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)


def _unregister_uninstall() -> None:
    import winreg

    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
    except FileNotFoundError:
        pass


def _remove_automatic_startup() -> None:
    """Remove both sign-in integrations, stopping a scheduled worker first."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, STARTUP_VALUE)
            except FileNotFoundError:
                pass
    except FileNotFoundError:
        pass
    subprocess.run(["schtasks", "/end", "/tn", AUTOMATIC_TASK_NAME], capture_output=True, text=True, check=False,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    subprocess.run(["schtasks", "/delete", "/tn", AUTOMATIC_TASK_NAME, "/f"], capture_output=True, text=True, check=False,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def install(
    source: Path,
    installer_executable: Path,
    layout: InstallLayout,
    *,
    shortcut_creator: Callable[[Path, Path], None] = _create_shortcut,
    register_uninstall: Callable[[Path], None] = _register_uninstall,
) -> Path:
    executable = source / "Caronte.exe"
    if not executable.is_file():
        raise FileNotFoundError("Il pacchetto di Caronte non e` completo.")
    if layout.program_dir.exists():
        raise FileExistsError("Caronte e` gia` installato. Disinstallarlo prima di continuare.")
    if layout.program_dir in (layout.config_dir, layout.data_dir):
        raise ValueError("La cartella del programma deve essere separata dai dati utente.")

    staging = layout.program_dir.with_name(layout.program_dir.name + ".installing")
    if staging.exists():
        shutil.rmtree(staging)
    staging.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(source, staging)
        uninstaller = staging / "DisinstallaCaronte.exe"
        shutil.copy2(installer_executable, uninstaller)
        staging.replace(layout.program_dir)
        installed_executable = layout.program_dir / "Caronte.exe"
        installed_uninstaller = layout.program_dir / "DisinstallaCaronte.exe"
        shortcut_creator(layout.start_menu_dir / "Caronte.lnk", installed_executable)
        register_uninstall(installed_uninstaller)
        return installed_executable
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if layout.program_dir.exists():
            shutil.rmtree(layout.program_dir)
        raise


def uninstall(
    layout: InstallLayout,
    *,
    unregister_uninstall: Callable[[], None] = _unregister_uninstall,
    remove_automatic_startup: Callable[[], None] = _remove_automatic_startup,
) -> None:
    remove_automatic_startup()
    if layout.start_menu_dir.exists():
        shutil.rmtree(layout.start_menu_dir)
    if layout.program_dir.exists():
        shutil.rmtree(layout.program_dir)
    unregister_uninstall()


def _confirm(message: str, title: str) -> bool:
    return ctypes.windll.user32.MessageBoxW(None, message, title, 0x21) == 1


def _notify(message: str, *, error: bool = False) -> None:
    ctypes.windll.user32.MessageBoxW(None, message, PRODUCT_NAME, 0x10 if error else 0x40)


def _run_relocated_uninstaller(layout: InstallLayout) -> int:
    temporary = Path(tempfile.gettempdir()) / f"Caronte-uninstall-{os.getpid()}.exe"
    shutil.copy2(sys.executable, temporary)
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen(
        [str(temporary), "/UNINSTALL-FINAL", f"/PARENT={os.getpid()}"],
        creationflags=flags,
        close_fds=True,
    )
    return 0


def _wait_for_process(process_id: int) -> None:
    synchronize = 0x00100000
    handle = ctypes.windll.kernel32.OpenProcess(synchronize, False, process_id)
    if handle:
        try:
            ctypes.windll.kernel32.WaitForSingleObject(handle, 30_000)
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)


def _schedule_self_delete(executable: Path) -> None:
    escaped = str(executable).replace("'", "''")
    command = f"Wait-Process -Id {os.getpid()}; Remove-Item -LiteralPath '{escaped}' -Force"
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", command],
        creationflags=flags,
        close_fds=True,
    )


def main() -> int:
    args = {value.upper() for value in sys.argv[1:]}
    silent = "/S" in args or "--SILENT" in args
    layout = InstallLayout.from_environment()
    try:
        if "/UNINSTALL" in args:
            if not silent and not _confirm("Vuoi disinstallare Caronte? I tuoi dati saranno conservati.", PRODUCT_NAME):
                return 0
            return _run_relocated_uninstaller(layout)
        if "/UNINSTALL-FINAL" in args:
            parent = next((value for value in args if value.startswith("/PARENT=")), None)
            if parent is not None:
                _wait_for_process(int(parent.partition("=")[2]))
            uninstall(layout)
            _schedule_self_delete(Path(sys.executable))
            return 0
        if not silent and not _confirm("Vuoi installare Caronte per questo utente?", PRODUCT_NAME):
            return 0
        installed = install(payload_root(), Path(sys.executable), layout)
        if "/NO-LAUNCH" not in args:
            subprocess.Popen([str(installed)], close_fds=True)
        if not silent:
            _notify("Caronte e` stato installato.")
        return 0
    except Exception as exc:
        if not silent:
            _notify(str(exc), error=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
