"""Pure quarantine state transitions."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .time_utils import rome_isoformat

from .models import QuarantineStatus


_ALLOWED_TRANSITIONS: dict[QuarantineStatus, frozenset[QuarantineStatus]] = {
    QuarantineStatus.DOWNLOADED: frozenset({QuarantineStatus.QUARANTINED}),
    QuarantineStatus.QUARANTINED: frozenset(
        {
            QuarantineStatus.REJECTED,
            QuarantineStatus.SCAN_FAILED,
            QuarantineStatus.READY_FOR_CARONTE,
        }
    ),
    QuarantineStatus.SCAN_FAILED: frozenset(
        {QuarantineStatus.QUARANTINED, QuarantineStatus.REJECTED}
    ),
    QuarantineStatus.READY_FOR_CARONTE: frozenset(
        {QuarantineStatus.UPLOADED_TO_LIMBO, QuarantineStatus.REJECTED}
    ),
    QuarantineStatus.REJECTED: frozenset(),
    QuarantineStatus.UPLOADED_TO_LIMBO: frozenset(),
}


class InvalidTransition(ValueError):
    """Raised when an attachment state transition is not allowed."""


@dataclass(frozen=True, slots=True)
class QuarantineRecord:
    local_temp_id: str
    status: QuarantineStatus
    updated_at: str
    reason: str

    @classmethod
    def downloaded(cls, local_temp_id: str) -> "QuarantineRecord":
        if not local_temp_id or "/" in local_temp_id or "\\" in local_temp_id:
            raise ValueError("local_temp_id must be a non-empty opaque identifier")
        return cls(
            local_temp_id=local_temp_id,
            status=QuarantineStatus.DOWNLOADED,
            updated_at=_rome_now(),
            reason="attachment bytes stored locally",
        )

    def transition(
        self,
        target: QuarantineStatus,
        *,
        reason: str,
        updated_at: str | None = None,
    ) -> "QuarantineRecord":
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise InvalidTransition(f"cannot transition {self.status} -> {target}")
        if not reason.strip():
            raise ValueError("transition reason must not be empty")
        return replace(
            self,
            status=target,
            updated_at=updated_at or _rome_now(),
            reason=reason,
        )


def can_transition(source: QuarantineStatus, target: QuarantineStatus) -> bool:
    return target in _ALLOWED_TRANSITIONS[source]


def _rome_now() -> str:
    return rome_isoformat()
