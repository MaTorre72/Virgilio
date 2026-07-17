"""Read-only mailbox connection check shared by Caronte presentations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Queue
from threading import Lock, Thread
from typing import Callable

from ..imap_readonly import ImapReadonlyConfig, ImapReadonlyMailbox


@dataclass(frozen=True, slots=True)
class AccountConnectionRequest:
    email: str
    password: str = field(repr=False)
    host: str = "imap.gmail.com"
    port: int = 993


class ReadonlyAccountConnectionService:
    """Check mailbox access without exposing mutating operations."""

    def __init__(
        self,
        local_root: Path,
        *,
        mailbox_factory: Callable[..., ImapReadonlyMailbox] = ImapReadonlyMailbox,
    ) -> None:
        self._local_root = Path(local_root)
        self._mailbox_factory = mailbox_factory

    def check(self, request: AccountConnectionRequest) -> str:
        mailbox = self._mailbox_factory(
            ImapReadonlyConfig(
                host=request.host,
                port=request.port,
                username=request.email,
                password=request.password,
            ),
            self._local_root,
        )
        count = len(mailbox.list_pending())
        return f"Collegamento riuscito: {count} messaggi visibili."


@dataclass(frozen=True, slots=True)
class AccountConnectionFeedback:
    ok: bool
    message: str


class BackgroundAccountConnectionCheck:
    """Run one read-only connection check without blocking the presentation."""

    def __init__(self, check: Callable[[object], str]) -> None:
        self._check = check
        self._results: Queue[AccountConnectionFeedback] = Queue()
        self._lock = Lock()
        self._running = False

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    def start(self, request: object) -> bool:
        with self._lock:
            if self._running:
                return False
            self._running = True
        Thread(target=self._run, args=(request,), daemon=True).start()
        return True

    def _run(self, request: object) -> None:
        try:
            message = self._check(request)
            feedback = AccountConnectionFeedback(True, str(message))
        except Exception as exc:
            feedback = AccountConnectionFeedback(False, _safe_connection_error(exc))
        finally:
            with self._lock:
                self._running = False
        self._results.put(feedback)

    def poll(self) -> AccountConnectionFeedback | None:
        try:
            return self._results.get_nowait()
        except Empty:
            return None


def _safe_connection_error(exc: Exception) -> str:
    """Translate known failure families without echoing exception details."""

    category = f"{type(exc).__name__} {exc}".casefold()
    if any(word in category for word in ("auth", "login", "credential", "password")):
        return "Accesso rifiutato. Controlla le credenziali della casella e riprova."
    if any(word in category for word in ("timeout", "network", "socket", "connect", "reachable")):
        return "Casella non raggiungibile. Controlla la connessione e riprova."
    return "Verifica non riuscita. Controlla i dati della casella e riprova."
