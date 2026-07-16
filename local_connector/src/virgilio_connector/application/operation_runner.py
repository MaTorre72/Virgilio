"""Shared background process lifecycle for Caronte presentations."""

from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
import subprocess
import sys
from threading import Lock, Thread
from typing import Callable


@dataclass(frozen=True)
class RunnerEvent:
    kind: str
    state: str
    message: str = ""
    returncode: int | None = None


class ManagedOperationRunner:
    """Own one local worker process without blocking a presentation thread."""

    def __init__(
        self,
        *,
        process_factory: Callable[..., object] = subprocess.Popen,
        stop_timeout: float = 3.0,
    ) -> None:
        self._process_factory = process_factory
        self._stop_timeout = stop_timeout
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
        command = [sys.executable, "-m", "virgilio_connector", *args]
        self._thread = Thread(target=self._run, args=(command,), daemon=True)
        self._thread.start()
        return True

    def _run(self, command: list[str]) -> None:
        try:
            process = self._process_factory(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            with self._lock:
                self._process = process
                stop_requested = self._stop_requested
                self._state = "stopping" if stop_requested else "running"
            if stop_requested:
                process.terminate()
            else:
                self._events.put(RunnerEvent("started", "running", "Caronte avviato."))
            stdout, stderr = process.communicate()
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
