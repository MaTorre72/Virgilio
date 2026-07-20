"""Safe application projection of existing audit events for Caronte views."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Mapping
from zoneinfo import ZoneInfo

from ..traceability import central_event_rows


ROME = ZoneInfo("Europe/Rome")


@dataclass(frozen=True, slots=True)
class ActivityRow:
    occurred_at: datetime
    occurred_text: str
    day: date
    account: str
    attachment: str
    activity: str
    outcome: str
    recommended_action: str
    technical_detail: str

    @property
    def visible_values(self) -> tuple[str, ...]:
        return (
            self.occurred_text,
            self.account,
            self.attachment,
            self.activity,
            self.outcome,
            self.recommended_action,
        )


@dataclass(frozen=True, slots=True)
class ActivityFilters:
    account: str = ""
    outcome: str = ""
    day: date | None = None


_EVENT_LABELS = {
    "attachment_quarantined": ("Allegato acquisito", "Riuscito"),
    "attachment_staged": ("Documento pronto per la decisione", "Riuscito"),
    "da_archiviare_intake": ("Decisione richiesta", "In attesa"),
    "message_completed": ("Messaggio completato", "Completato"),
    "duplicate_seen": ("Duplicato riconosciuto", "Ignorato"),
    "skipped": ("Elemento ignorato", "Ignorato"),
}


class ActivityService:
    """Read and translate the existing local audit stream without leaking its schema."""

    def __init__(
        self,
        state_db: Path,
        *,
        event_reader: Callable[[Path], Iterable[Mapping[str, object]]] = central_event_rows,
        redact: Callable[[str], str] = lambda value: value,
    ) -> None:
        self._state_db = state_db
        self._event_reader = event_reader
        self._redact = redact
        self._session_rows: list[ActivityRow] = []

    def list_activities(self) -> tuple[ActivityRow, ...]:
        if self._event_reader is central_event_rows and not self._state_db.is_file():
            rows: list[ActivityRow] = []
        else:
            rows = list(
                project_activity(event, redact=self._redact)
                for event in self._event_reader(self._state_db)
            )
        rows.extend(self._session_rows)
        return filter_activities(rows, ActivityFilters())

    def record_control_feedback(
        self,
        *,
        activity: str,
        message: str,
        state: str,
        occurred_at: datetime | None = None,
    ) -> None:
        """Keep a readable Home action visible during the current session."""

        when = occurred_at or datetime.now(ROME)
        outcome = {
            "Controllo in corso": "In corso",
            "Richiede attenzione": "Problema",
        }.get(state, "Riuscito")
        action = (
            "Riprova il controllo; se il problema continua, chiedi assistenza."
            if outcome == "Problema" else message
        )
        self._session_rows.append(ActivityRow(
            occurred_at=when,
            occurred_text=when.astimezone(ROME).strftime("%d/%m/%Y %H:%M"),
            day=when.astimezone(ROME).date(),
            account="Tutte le caselle",
            attachment="-",
            activity=self._redact(activity),
            outcome=outcome,
            recommended_action=self._redact(action),
            technical_detail="Dettaglio tecnico disponibile solo per le attivita registrate.",
        ))


def project_activity(
    event: Mapping[str, object],
    *,
    redact: Callable[[str], str] = lambda value: value,
) -> ActivityRow:
    """Translate one technical event into a bounded, user-facing record."""

    occurred_at = _rome_datetime(event.get("created_at"))
    event_type = str(event.get("event_type", "") or "").strip()
    result = str(event.get("result", "") or "").strip().lower()
    conflict = event_type.startswith("conflict_") or bool(event.get("conflict_type"))
    failed = conflict or event_type == "failed" or result in {"error", "failed", "failure"}
    if conflict:
        activity = "Documento da controllare"
        outcome = "Problema"
        recommended_action = "Controlla il documento prima di riprovare."
    elif failed:
        activity = "Controllo non completato"
        outcome = "Problema"
        recommended_action = "Riprova il controllo; se il problema continua, chiedi assistenza."
    else:
        activity, outcome = _EVENT_LABELS.get(event_type, ("Attivita registrata", "Riuscito"))
        recommended_action = "Nessuna azione necessaria."
    attachment = Path(str(event.get("staged_filename", "") or "")).name or "-"
    technical_detail = (
        f"Tipo evento: {_safe_technical_token(event_type)}; "
        f"esito origine: {_safe_technical_token(result)}"
    )
    return ActivityRow(
        occurred_at=occurred_at,
        occurred_text=occurred_at.strftime("%d/%m/%Y %H:%M"),
        day=occurred_at.date(),
        account=redact(str(event.get("account_alias", "") or "Casella non indicata")),
        attachment=redact(attachment),
        activity=redact(activity),
        outcome=outcome,
        recommended_action=redact(recommended_action),
        technical_detail=redact(technical_detail),
    )


def filter_activities(
    rows: Iterable[ActivityRow], filters: ActivityFilters
) -> tuple[ActivityRow, ...]:
    account = filters.account.strip().casefold()
    outcome = filters.outcome.strip().casefold()
    selected = (
        row
        for row in rows
        if (not account or row.account.casefold() == account)
        and (not outcome or row.outcome.casefold() == outcome)
        and (filters.day is None or row.day == filters.day)
    )
    return tuple(sorted(selected, key=lambda row: row.occurred_at, reverse=True))


def parse_day(value: str) -> date | None:
    value = value.strip()
    return datetime.strptime(value, "%d/%m/%Y").date() if value else None


def _rome_datetime(value: object) -> datetime:
    text = str(value or "").strip()
    if not text:
        return datetime.fromtimestamp(0, timezone.utc).astimezone(ROME)
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(ROME)


def _safe_technical_token(value: str) -> str:
    if not value:
        return "non indicato"
    if len(value) > 80 or any(
        not (character.isalnum() or character in "_-.") for character in value
    ):
        return "non disponibile"
    return value
