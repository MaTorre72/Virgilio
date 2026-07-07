"""Generate standard Caronte dry-run JSON locally, without any transport."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from uuid import uuid4

from .contract import command_from_json, command_to_json
from .models import (
    Attachment,
    CaronteCommand,
    QuarantineStatus,
    SCHEMA_VERSION,
    CONNECTOR_TYPE,
    REQUESTED_ACTION,
)
from .time_utils import rome_isoformat


@dataclass(frozen=True, slots=True)
class CaronteDryRunConfig:
    connector_id: str = "local-readonly-probe"
    account_alias: str = "gmail-test"
    provider_hint: str = "gmail_imap"


class NoReadyAttachmentsError(RuntimeError):
    """Raised when the latest completed run has nothing eligible for Caronte."""


def generate_caronte_dry_run_files(
    state_db: str | Path,
    output_dir: str | Path,
    *,
    config: CaronteDryRunConfig | None = None,
) -> tuple[Path, ...]:
    """Write one validated dry-run command per message from the latest run.

    This function opens SQLite in query-only mode and has no network or Apps Script
    dependency. Attachment bytes and local paths never enter the JSON payload.
    """
    source = Path(state_db)
    destination = Path(output_dir)
    settings = config or CaronteDryRunConfig()
    commands = _load_commands(source, settings)
    if not commands:
        raise NoReadyAttachmentsError(
            "latest completed run contains no ready_for_caronte attachments"
        )
    destination.mkdir(parents=True, exist_ok=True)
    written = []
    for command in commands:
        payload = command_to_json(command, indent=2) + "\n"
        # Round-trip through the strict contract before persisting the artifact.
        command_from_json(payload)
        target = destination / f"{command.command_id}.json"
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(target)
        written.append(target)
    return tuple(written)


def _load_commands(path: Path, config: CaronteDryRunConfig) -> tuple[CaronteCommand, ...]:
    if not path.is_file():
        raise FileNotFoundError(f"state database not found: {path}")
    uri = f"{path.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        run = db.execute("""SELECT id FROM runs WHERE status='completed'
            ORDER BY id DESC LIMIT 1""").fetchone()
        if run is None:
            return ()
        messages = db.execute("SELECT * FROM messages WHERE run_id=? ORDER BY id",
                              (int(run["id"]),)).fetchall()
        commands = []
        for message in messages:
            rows = db.execute("""SELECT * FROM attachments
                WHERE message_id=? AND status='ready_for_caronte' ORDER BY ordinal""",
                (int(message["id"]),)).fetchall()
            if not rows:
                continue
            command_id = str(uuid4())
            attachments = tuple(Attachment(
                local_temp_id=_local_temp_id(message, row),
                original_filename=str(row["original_filename"]),
                sanitized_filename=str(row["sanitized_filename"]),
                mime_type=str(row["declared_mime_type"]),
                size_bytes=int(row["size_bytes"]), sha256=str(row["sha256"]),
                quarantine_status=QuarantineStatus.READY_FOR_CARONTE,
                scan_engine=str(row["scanner_engine"] or "none"),
                scan_result=str(row["scan_result"] or "unverified"),
            ) for row in rows)
            commands.append(CaronteCommand(
                schema_version=SCHEMA_VERSION, command_id=command_id,
                created_at=rome_isoformat(),
                connector_id=config.connector_id, connector_type=CONNECTOR_TYPE,
                account_alias=config.account_alias, provider_hint=config.provider_hint,
                mailbox=str(message["mailbox"]),
                mailbox_uidvalidity=message["uidvalidity"],
                message_uid=str(message["message_uid"]),
                message_id=str(message["message_id"] or ""), thread_id=None,
                subject=str(message["subject"]), sender=str(message["sender"]),
                date=str(message["message_date"]), user_confirmed_command=False,
                attachments=attachments, requested_action=REQUESTED_ACTION, dry_run=True,
            ))
        return tuple(commands)


def _local_temp_id(message: sqlite3.Row, attachment: sqlite3.Row) -> str:
    uidvalidity = str(message["uidvalidity"] or "unknown").replace("/", "_").replace("\\", "_")
    uid = str(message["message_uid"]).replace("/", "_").replace("\\", "_")
    return f"att-{uidvalidity}-{uid}-{int(attachment['ordinal'])}-{str(attachment['sha256'])[:12]}"
