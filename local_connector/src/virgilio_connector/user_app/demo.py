"""Synthetic, in-memory content for the repeatable Caronte demonstration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DemoAccount:
    alias: str
    name: str
    email: str
    host: str = "imap.gmail.com"
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class DemoState:
    """Presentation data which deliberately has no persistence adapters."""

    limbo_folder: str = "Cartella Limbo dimostrativa"
    accounts: tuple[DemoAccount, ...] = (
        DemoAccount("demo-principale", "Casella principale", "principale@example.invalid"),
        DemoAccount("demo-seconda", "Seconda casella", "seconda@example.invalid"),
    )
    next_action: str = "Controlla ora per vedere se sono arrivati nuovi documenti."
    recent_activity: str = "Nessuna attivita recente da segnalare."
    problems: str = "Nessun problema da risolvere."
