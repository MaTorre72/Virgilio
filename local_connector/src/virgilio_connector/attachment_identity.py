"""Canonical, metadata-only identifiers for IMAP attachments."""

from __future__ import annotations


def canonical_attachment_id(uidvalidity: object, message_uid: object, ordinal: int) -> str:
    """Build the stable identifier required by Limbo verification and intake."""

    raw_uidvalidity = str(uidvalidity or "").strip()
    normalized_uidvalidity = (
        "unknown" if not raw_uidvalidity or raw_uidvalidity.lower() == "none"
        else raw_uidvalidity
    )
    normalized_uidvalidity = normalized_uidvalidity.replace("/", "_").replace("\\", "_")
    normalized_uid = str(message_uid or "unknown").strip().replace("/", "_").replace("\\", "_")
    return f"att-{normalized_uidvalidity}-{normalized_uid}-{int(ordinal)}"
