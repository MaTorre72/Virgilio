"""Shared background process lifecycle for Caronte presentations."""

from __future__ import annotations

from dataclasses import dataclass
import json
from queue import Empty, Queue
import subprocess
import sys
import os
from threading import Lock, Thread
from typing import Callable, Mapping


@dataclass(frozen=True)
class RunnerEvent:
    kind: str
    state: str
    message: str = ""
    returncode: int | None = None
    phase: str = ""
    found: int | None = None
    processed: int | None = None
    remaining: int | None = None


class ManagedOperationRunner:
    """Own one local worker process without blocking a presentation thread."""

    def __init__(
        self,
        *,
        process_factory: Callable[..., object] = subprocess.Popen,
        stop_timeout: float = 3.0,
        environment_provider: Callable[[], Mapping[str, str]] | None = None,
    ) -> None:
        self._process_factory = process_factory
        self._stop_timeout = stop_timeout
        self._environment_provider = environment_provider
        self._process = None
        self._thread: Thread | None = None
        self._lock = Lock()
        self._events: Queue[RunnerEvent] = Queue()
        self._state = "stopped"
        self._stop_requested = False

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def running(self) -> bool:
        return self.state in {"starting", "running", "stopping"}

    def start(self, args: list[str]) -> bool:
        with self._lock:
            if self._state in {"starting", "running", "stopping"}:
                self._events.put(
                    RunnerEvent("rejected", self._state, "Caronte e` gia` in esecuzione.")
                )
                return False
            self._state = "starting"
            self._stop_requested = False
        command = _runtime_command(args)
        environment = dict(os.environ)
        if self._environment_provider is not None:
            environment.update(self._environment_provider())
        self._thread = Thread(
            target=self._run, args=(command, environment), daemon=True
        )
        self._thread.start()
        return True

    def _run(self, command: list[str], environment: Mapping[str, str]) -> None:
        try:
            process = self._process_factory(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                env=dict(environment),
            )
            with self._lock:
                self._process = process
                stop_requested = self._stop_requested
                self._state = "stopping" if stop_requested else "running"
            if stop_requested:
                process.terminate()
            else:
                self._events.put(RunnerEvent("started", "running", "Caronte avviato."))
            stdout, stderr = self._collect_output(process)
            returncode = process.returncode
            combined = stdout.strip()
            if stderr.strip():
                combined = f"{combined}\n\n{stderr.strip()}".strip()
            with self._lock:
                was_stopping = self._state == "stopping"
                self._state = "stopped" if was_stopping or returncode == 0 else "error"
                state = self._state
                self._process = None
            kind = "stopped" if was_stopping else "completed"
            self._events.put(RunnerEvent(kind, state, combined, returncode))
        except Exception as exc:
            with self._lock:
                self._process = None
                self._state = "error"
            self._events.put(RunnerEvent("error", "error", str(exc)))

    def _collect_output(self, process: object) -> tuple[str, str]:
        """Read optional progress lines without exposing them as user output."""
        stdout = getattr(process, "stdout", None)
        if stdout is None:
            return process.communicate()
        output: list[str] = []
        for line in stdout:
            if not self._emit_progress(line):
                output.append(line)
        stderr_stream = getattr(process, "stderr", None)
        stderr = stderr_stream.read() if stderr_stream is not None else ""
        process.wait()
        return "".join(output), stderr

    def _emit_progress(self, line: str) -> bool:
        try:
            payload = json.loads(line)
            progress = payload["caronte_progress"]
            phase = str(progress["phase"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return False
        self._events.put(RunnerEvent(
            "progress", "error" if progress.get("error") else "running",
            phase=phase,
            found=_optional_count(progress.get("found")),
            processed=_optional_count(progress.get("processed")),
            remaining=_optional_count(progress.get("remaining")),
        ))
        return True

    def stop(self) -> bool:
        with self._lock:
            process = self._process
            if self._state == "starting" and process is None:
                self._stop_requested = True
                self._state = "stopping"
                return True
            if process is None or self._state != "running":
                self._events.put(
                    RunnerEvent("rejected", self._state, "Caronte non e` in esecuzione.")
                )
                return False
            self._state = "stopping"
        process.terminate()
        try:
            process.wait(timeout=self._stop_timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=self._stop_timeout)
        return True

    def close(self) -> None:
        if self.running:
            self.stop()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=self._stop_timeout)

    def drain_events(self) -> list[RunnerEvent]:
        events: list[RunnerEvent] = []
        while True:
            try:
                events.append(self._events.get_nowait())
            except Empty:
                return events


def _runtime_command(args: list[str]) -> list[str]:
    """Use the bundled executable directly when running from a frozen build."""

    if getattr(sys, "frozen", False):
        return [sys.executable, *args]
    return [sys.executable, "-m", "virgilio_connector", *args]


def _optional_count(value: object) -> int | None:
    return value if isinstance(value, int) and value >= 0 else None
