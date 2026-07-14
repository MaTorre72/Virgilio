"""Readable, local-only projection of Caronte audit events for the GUI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Mapping
from zoneinfo import ZoneInfo

from .traceability import central_event_rows


ROME = ZoneInfo("Europe/Rome")


@dataclass(frozen=True, slots=True)
class ActivityRow:
    occurred_at: datetime
    occurred_text: str
    day: date
    account: str
    message: str
    attachment: str
    action: str
    outcome: str
    problem: str


@dataclass(frozen=True, slots=True)
class ActivityFilters:
    account: str = ""
    outcome: str = ""
    day: date | None = None
    errors: str = "all"


_EVENT_LABELS = {
    "attachment_quarantined": ("Allegato acquisito", "Acquisito nel Limbo"),
    "attachment_staged": ("Allegato preparato", "Pronto in Da archiviare"),
    "da_archiviare_intake": ("Decisione richiesta", "In attesa della decisione umana"),
    "message_completed": ("Messaggio completato", "Archiviazione completata"),
    "duplicate_seen": ("Duplicato riconosciuto", "Gia acquisito in precedenza"),
    "skipped": ("Elemento ignorato", "Nessuna azione necessaria"),
    "failed": ("Operazione non riuscita", "Controllo non completato"),
}


def project_activity(event: Mapping[str, object], *,
                     redact: Callable[[str], str] = lambda value: value) -> ActivityRow:
    """Convert a technical audit row into safe user-facing fields."""

    occurred_at = _rome_datetime(event.get("created_at"))
    event_type = str(event.get("event_type", "") or "").strip()
    result = str(event.get("result", "") or "").strip().lower()
    conflict = event_type.startswith("conflict_") or bool(event.get("conflict_type"))
    failed = conflict or event_type == "failed" or result in {"error", "failed", "failure"}
    if conflict:
        action, message = "Conflitto rilevato", "Il documento richiede un controllo"
        outcome = "Problema"
        problem = "Controlla il documento in Diagnostica avanzata prima di riprovare."
    elif failed:
        action, message = _EVENT_LABELS.get(event_type, ("Operazione non riuscita", "Controllo non completato"))
        outcome = "Problema"
        problem = "Apri Diagnostica avanzata, verifica il dettaglio e riprova il controllo."
    else:
        action, message = _EVENT_LABELS.get(event_type, _fallback_labels(event_type))
        outcome = _outcome_label(event_type, result)
        problem = ""
    attachment = Path(str(event.get("staged_filename", "") or "")).name
    return ActivityRow(
        occurred_at=occurred_at,
        occurred_text=occurred_at.strftime("%d/%m/%Y %H:%M:%S"),
        day=occurred_at.date(),
        account=redact(str(event.get("account_alias", "") or "Casella non indicata")),
        message=redact(message),
        attachment=redact(attachment or "-"),
        action=redact(action),
        outcome=outcome,
        problem=redact(problem),
    )


def filter_activities(rows: Iterable[ActivityRow], filters: ActivityFilters) -> tuple[ActivityRow, ...]:
    """Apply combinable account, outcome, local-day and error filters."""

    selected = []
    for row in rows:
        if filters.account and row.account != filters.account:
            continue
        if filters.outcome and row.outcome != filters.outcome:
            continue
        if filters.day is not None and row.day != filters.day:
            continue
        if filters.errors == "only" and not row.problem:
            continue
        if filters.errors == "without" and row.problem:
            continue
        selected.append(row)
    return tuple(sorted(selected, key=lambda row: row.occurred_at, reverse=True))


def load_activities(state_db: Path, *,
                    redact: Callable[[str], str] = lambda value: value) -> tuple[ActivityRow, ...]:
    """Read the existing local audit store without exposing its schema to the GUI."""

    if not state_db.is_file():
        return ()
    return tuple(project_activity(event, redact=redact) for event in central_event_rows(state_db))


def parse_day(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    return datetime.strptime(value, "%d/%m/%Y").date()


def _rome_datetime(value: object) -> datetime:
    text = str(value or "").strip()
    if not text:
        return datetime.fromtimestamp(0, timezone.utc).astimezone(ROME)
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(ROME)


def _outcome_label(event_type: str, result: str) -> str:
    if event_type == "message_completed" or result == "completed":
        return "Completato"
    if event_type in {"duplicate_seen", "skipped"} or result in {"duplicate_seen", "skipped"}:
        return "Ignorato"
    if event_type == "da_archiviare_intake" or result in {"pending", "waiting"}:
        return "In attesa"
    return "Riuscito"


def _fallback_labels(event_type: str) -> tuple[str, str]:
    words = event_type.replace("_", " ").strip()
    if not words:
        return "Attivita locale", "Evento registrato"
    return "Attivita registrata", words.capitalize()
