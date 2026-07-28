"""Pure acknowledgement policy; this module never touches a mailbox."""

from __future__ import annotations

from dataclasses import dataclass

from .models import CaronteCommand, CaronteResponse


@dataclass(frozen=True, slots=True)
class AckDecision:
    allowed: bool
    reason: str
    acknowledged_attachment_ids: tuple[str, ...] = ()


def evaluate_ack(
    command: CaronteCommand,
    response: CaronteResponse,
    *,
    allow_partial: bool = False,
) -> AckDecision:
    """Return whether a future IMAP adapter may acknowledge the message.

    Partial success is blocked by default because its operational policy is
    still open. Callers must opt in explicitly once that decision is made.
    """

    if command.dry_run:
        return AckDecision(False, "dry_run commands cannot be acknowledged")
    if response.command_id != command.command_id:
        return AckDecision(False, "response command_id does not match")
    if not response.ok:
        return AckDecision(False, "Caronte reported failure")
    if not response.accepted_attachments:
        return AckDecision(False, "no attachment was accepted")
    if not allow_partial and (response.rejected_attachments or response.errors):
        return AckDecision(False, "partial success policy is not enabled")

    command_attachments = {item.local_temp_id: item for item in command.attachments}
    accepted_ids = {item.local_temp_id for item in response.accepted_attachments}
    drive_ids = {
        item.local_temp_id: item.drive_file_id for item in response.limbo_drive_ids
    }

    if accepted_ids - set(command_attachments):
        return AckDecision(False, "response accepted unknown attachments")

    for accepted in response.accepted_attachments:
        source = command_attachments[accepted.local_temp_id]
        if accepted.sha256 != source.sha256:
            return AckDecision(False, "response attachment hash does not match")
        if not drive_ids.get(accepted.local_temp_id):
            return AckDecision(False, "accepted attachment has no Limbo Drive id")

    return AckDecision(
        True,
        "at least one attachment was confirmed in Limbo Drive",
        tuple(sorted(accepted_ids)),
    )
