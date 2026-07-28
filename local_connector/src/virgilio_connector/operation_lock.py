"""Interprocess exclusion for local pipeline and maintenance operations."""

from __future__ import annotations

from pathlib import Path
import os


class LocalOperationBusyError(RuntimeError):
    """Raised when another process owns the local operation lock."""


class LocalOperationLock:
    """Hold one non-blocking OS lock outside the data root being reset."""

    def __init__(self, local_root: str | Path) -> None:
        root = Path(local_root)
        self.path = root.parent / f".{root.name}.operation.lock"
        self._stream = None

    def __enter__(self) -> "LocalOperationLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stream = None
        try:
            stream = self.path.open("a+b")
            stream.seek(0)
            if stream.read(1) == b"":
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            _lock_stream(stream)
        except OSError as exc:
            if stream is not None:
                stream.close()
            raise LocalOperationBusyError(
                "another local operation is already running"
            ) from exc
        self._stream = stream
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        stream = self._stream
        self._stream = None
        if stream is None:
            return
        try:
            _unlock_stream(stream)
        finally:
            stream.close()


def _lock_stream(stream) -> None:
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        return
    import fcntl

    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_stream(stream) -> None:
    stream.seek(0)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
