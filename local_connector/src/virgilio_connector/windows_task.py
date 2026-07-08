"""Windows Task Scheduler helpers for the local watch command."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess


class WindowsTaskError(ValueError):
    """Raised when the Windows task configuration is invalid or registration fails."""


@dataclass(frozen=True)
class WindowsTaskRegistrationPlan:
    task_name: str
    config_path: str
    python_exe: str
    repo_root: str
    interval_seconds: int
    task_action: str
    create_args: list[str]
    create_command: str

    def to_payload(self, *, status: str, stdout: str = "", stderr: str = "") -> dict[str, object]:
        payload: dict[str, object] = {
            "status": status,
            "task_name": self.task_name,
            "trigger": "ONLOGON",
            "config_path": self.config_path,
            "python_exe": self.python_exe,
            "repo_root": self.repo_root,
            "interval_seconds": self.interval_seconds,
            "task_action": self.task_action,
            "create_command": self.create_command,
        }
        if stdout:
            payload["stdout"] = stdout
        if stderr:
            payload["stderr"] = stderr
        return payload


def _quote_powershell(value: str) -> str:
    return value.replace("'", "''")


def _resolve_existing_path(path: Path, *, label: str) -> Path:
    resolved = path.expanduser().resolve(strict=False)
    if not resolved.exists():
        raise WindowsTaskError(f"{label} not found: {resolved}")
    return resolved


def build_windows_watch_task(
    *,
    config_path: Path,
    python_exe: Path,
    repo_root: Path,
    interval_seconds: int,
    task_name: str,
    force: bool = False,
) -> WindowsTaskRegistrationPlan:
    if os.name != "nt":
        raise WindowsTaskError("Windows Task Scheduler is supported only on Windows")
    if interval_seconds <= 0:
        raise WindowsTaskError("interval_seconds must be greater than 0")
    if not task_name.strip():
        raise WindowsTaskError("task_name must not be empty")

    resolved_config = _resolve_existing_path(config_path, label="config_path")
    resolved_python = _resolve_existing_path(python_exe, label="python_exe")
    resolved_repo_root = _resolve_existing_path(repo_root, label="repo_root")
    if not resolved_repo_root.is_dir():
        raise WindowsTaskError(f"repo_root must be a directory: {resolved_repo_root}")

    pythonpath = resolved_repo_root / "local_connector" / "src"
    if not pythonpath.is_dir():
        raise WindowsTaskError(f"pythonpath not found: {pythonpath}")

    powershell_exe = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    powershell_script = (
        f"$env:PYTHONPATH='{_quote_powershell(str(pythonpath))}'; "
        f"Set-Location -LiteralPath '{_quote_powershell(str(resolved_repo_root))}'; "
        f"& '{_quote_powershell(str(resolved_python))}' -m virgilio_connector watch "
        f"--config '{_quote_powershell(str(resolved_config))}' --interval-seconds {interval_seconds}"
    )
    action_args = [
        str(powershell_exe),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-WindowStyle",
        "Hidden",
        "-Command",
        powershell_script,
    ]
    task_action = subprocess.list2cmdline(action_args)
    create_args = ["schtasks", "/create", "/tn", task_name, "/sc", "ONLOGON", "/rl", "LIMITED", "/tr", task_action]
    if force:
        create_args.append("/f")
    create_command = subprocess.list2cmdline(create_args)
    return WindowsTaskRegistrationPlan(
        task_name=task_name,
        config_path=str(resolved_config),
        python_exe=str(resolved_python),
        repo_root=str(resolved_repo_root),
        interval_seconds=interval_seconds,
        task_action=task_action,
        create_args=create_args,
        create_command=create_command,
    )


def register_windows_watch_task(plan: WindowsTaskRegistrationPlan) -> dict[str, object]:
    completed = subprocess.run(plan.create_args, capture_output=True, text=True, check=False)
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if completed.returncode != 0:
        message = stderr or stdout or f"schtasks exited with code {completed.returncode}"
        raise WindowsTaskError(message)
    return plan.to_payload(status="created", stdout=stdout, stderr=stderr)
