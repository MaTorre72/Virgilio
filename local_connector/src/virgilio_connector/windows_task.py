"""Windows Task Scheduler helpers for the local watch command."""

from __future__ import annotations

from dataclasses import dataclass
import json
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


@dataclass(frozen=True)
class WindowsTaskStatus:
    task_name: str
    installed: bool
    state: str = ""
    last_run_time: str = ""
    next_run_time: str = ""
    last_result: int | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "status": "installed" if self.installed else "not_installed",
            "task_name": self.task_name,
            "installed": self.installed,
            "state": self.state,
            "last_run_time": self.last_run_time,
            "next_run_time": self.next_run_time,
            "last_result": self.last_result,
        }


def _quote_powershell(value: str) -> str:
    return value.replace("'", "''")


def _task_name(value: str) -> str:
    value = value.strip()
    if not value:
        raise WindowsTaskError("task_name must not be empty")
    if "\r" in value or "\n" in value:
        raise WindowsTaskError("task_name must be a single line")
    return value


def _powershell_executable() -> Path:
    return (Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" /
            "WindowsPowerShell" / "v1.0" / "powershell.exe")


def _run_hidden(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a scheduler command without creating a console beside Caronte."""

    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


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
    task_name = _task_name(task_name)

    resolved_config = _resolve_existing_path(config_path, label="config_path")
    resolved_python = _resolve_existing_path(python_exe, label="python_exe")
    resolved_repo_root = _resolve_existing_path(repo_root, label="repo_root")
    if not resolved_repo_root.is_dir():
        raise WindowsTaskError(f"repo_root must be a directory: {resolved_repo_root}")

    pythonpath = resolved_repo_root / "local_connector" / "src"
    if not pythonpath.is_dir():
        raise WindowsTaskError(f"pythonpath not found: {pythonpath}")

    powershell_exe = _powershell_executable()
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


def build_windows_frozen_watch_task(
    *,
    config_path: Path,
    executable: Path,
    interval_seconds: int,
    task_name: str,
    force: bool = False,
) -> WindowsTaskRegistrationPlan:
    """Plan the sign-in worker for the installed, self-contained Caronte."""

    if os.name != "nt":
        raise WindowsTaskError("Windows Task Scheduler is supported only on Windows")
    if interval_seconds <= 0:
        raise WindowsTaskError("interval_seconds must be greater than 0")
    task_name = _task_name(task_name)
    resolved_config = _resolve_existing_path(config_path, label="config_path")
    resolved_executable = _resolve_existing_path(executable, label="executable")
    if not resolved_executable.is_file():
        raise WindowsTaskError(f"executable must be a file: {resolved_executable}")
    action_args = [
        str(resolved_executable), "watch", "--config", str(resolved_config),
        "--human", "--interval-seconds", str(interval_seconds),
    ]
    task_action = subprocess.list2cmdline(action_args)
    create_args = ["schtasks", "/create", "/tn", task_name, "/sc", "ONLOGON", "/rl", "LIMITED", "/tr", task_action]
    if force:
        create_args.append("/f")
    return WindowsTaskRegistrationPlan(
        task_name=task_name,
        config_path=str(resolved_config),
        python_exe="",
        repo_root="",
        interval_seconds=interval_seconds,
        task_action=task_action,
        create_args=create_args,
        create_command=subprocess.list2cmdline(create_args),
    )


def register_windows_watch_task(plan: WindowsTaskRegistrationPlan) -> dict[str, object]:
    completed = _run_hidden(plan.create_args)
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if completed.returncode != 0:
        message = stderr or stdout or f"schtasks exited with code {completed.returncode}"
        raise WindowsTaskError(message)
    return plan.to_payload(status="created", stdout=stdout, stderr=stderr)


def query_windows_watch_task(task_name: str) -> WindowsTaskStatus:
    """Read Task Scheduler state through stable PowerShell object properties."""

    if os.name != "nt":
        raise WindowsTaskError("Windows Task Scheduler is supported only on Windows")
    task_name = _task_name(task_name)
    quoted_name = _quote_powershell(task_name)
    script = (
        f"$task = Get-ScheduledTask -TaskName '{quoted_name}' -ErrorAction SilentlyContinue; "
        "if ($null -eq $task) { "
        f"[pscustomobject]@{{task_name='{quoted_name}';installed=$false}} | ConvertTo-Json -Compress; "
        "exit 0 }; "
        "$info = $task | Get-ScheduledTaskInfo; "
        "[pscustomobject]@{task_name=$task.TaskName;installed=$true;state=[string]$task.State;"
        "last_run_time=if($info.LastRunTime.Year -gt 1900){$info.LastRunTime.ToString('o')}else{''};"
        "next_run_time=if($info.NextRunTime.Year -gt 1900){$info.NextRunTime.ToString('o')}else{''};"
        "last_result=[int]$info.LastTaskResult} | ConvertTo-Json -Compress"
    )
    args = [str(_powershell_executable()), "-NoProfile", "-NonInteractive", "-Command", script]
    completed = _run_hidden(args)
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if completed.returncode != 0:
        raise WindowsTaskError(stderr or stdout or
                               f"PowerShell exited with code {completed.returncode}")
    try:
        payload = json.loads(stdout)
        installed = bool(payload["installed"])
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise WindowsTaskError("unexpected Task Scheduler status response") from exc
    last_result = payload.get("last_result")
    return WindowsTaskStatus(
        task_name=str(payload.get("task_name") or task_name),
        installed=installed,
        state=str(payload.get("state") or ""),
        last_run_time=str(payload.get("last_run_time") or ""),
        next_run_time=str(payload.get("next_run_time") or ""),
        last_result=int(last_result) if last_result is not None else None,
    )


def unregister_windows_watch_task(task_name: str) -> dict[str, object]:
    """Remove the user task; repeated removal is a successful no-op."""

    task_name = _task_name(task_name)
    current = query_windows_watch_task(task_name)
    if not current.installed:
        return {"status": "not_installed", "task_name": task_name, "removed": False}
    if current.state.lower() == "running":
        _run_hidden(["schtasks", "/end", "/tn", task_name])
    args = ["schtasks", "/delete", "/tn", task_name, "/f"]
    completed = _run_hidden(args)
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if completed.returncode != 0:
        raise WindowsTaskError(stderr or stdout or
                               f"schtasks exited with code {completed.returncode}")
    payload: dict[str, object] = {
        "status": "removed", "task_name": task_name, "removed": True,
    }
    if stdout:
        payload["stdout"] = stdout
    if stderr:
        payload["stderr"] = stderr
    return payload
