"""Offline orchestration of the connector ports and persistent state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import mimetypes
from pathlib import Path
from uuid import uuid4

from .ack import evaluate_ack
from .contract import command_to_json
from .files import sanitize_filename, sha256_file
from .models import Attachment, CaronteCommand, QuarantineStatus
from .policy import AttachmentPolicy, PolicyDecision
from .ports import AntivirusPort, CarontePort, MailboxPort, MessageReference
from .state_db import StateStore
from .state_models import MessageStatus, NewAttachment, NewMessage


@dataclass(frozen=True, slots=True)
class ConnectorConfig:
    connector_id: str
    account_alias: str
    provider_hint: str = "generic_imap"
    dry_run: bool = False


@dataclass(frozen=True, slots=True)
class ProcessingResult:
    message: MessageReference
    status: MessageStatus
    command_id: str | None
    acknowledged: bool


class ConnectorOrchestrator:
    """Runs one deterministic polling cycle; adapters own all side effects."""

    def __init__(self, *, mailbox: MailboxPort, antivirus: AntivirusPort,
                 caronte: CarontePort, store: StateStore, config: ConnectorConfig,
                 policy: AttachmentPolicy | None = None) -> None:
        self.mailbox, self.antivirus, self.caronte = mailbox, antivirus, caronte
        self.store, self.config = store, config
        self.policy = policy or AttachmentPolicy()

    def run_once(self) -> tuple[ProcessingResult, ...]:
        return tuple(self._process(message) for message in self.mailbox.list_pending())

    def _process(self, ref: MessageReference) -> ProcessingResult:
        message = self.store.register_message(NewMessage(
            account_alias=self.config.account_alias, mailbox=ref.mailbox,
            mailbox_uidvalidity=ref.uidvalidity or "unknown", message_uid=ref.message_uid,
            message_id=ref.message_id, thread_id=ref.thread_id, subject=ref.subject,
            sender=ref.sender, message_date=ref.date,
        ))
        if message.status in {MessageStatus.ACKNOWLEDGED, MessageStatus.REJECTED}:
            return ProcessingResult(ref, message.status, message.command_id,
                                    message.status is MessageStatus.ACKNOWLEDGED)
        ready = []
        for source in self.mailbox.download_attachments(ref):
            digest = sha256_file(source.local_path)
            record = self.store.add_attachment(NewAttachment(
                message_row_id=message.id, local_temp_id=source.local_temp_id,
                local_relative_path=source.local_path.name,
                original_filename=source.original_filename,
                sanitized_filename=sanitize_filename(source.original_filename),
                mime_type=mimetypes.guess_type(source.original_filename)[0] or "application/octet-stream",
                size_bytes=source.local_path.stat().st_size, sha256=digest,
            ))
            if record.quarantine_status is not QuarantineStatus.DOWNLOADED:
                continue
            self.store.transition_attachment(record.local_temp_id, QuarantineStatus.QUARANTINED,
                                             reason="isolated by mailbox adapter")
            decision = self.policy.evaluate_filename(source.original_filename)
            if decision.decision is not PolicyDecision.ALLOW:
                self.store.transition_attachment(record.local_temp_id, QuarantineStatus.REJECTED,
                                                 reason=decision.reason)
                continue
            scan = self.antivirus.scan(source.local_path)
            target = QuarantineStatus.READY_FOR_CARONTE if scan.clean else QuarantineStatus.REJECTED
            record = self.store.transition_attachment(record.local_temp_id, target,
                reason="scanner accepted attachment" if scan.clean else "scanner rejected attachment",
                scan_engine=scan.engine, scan_result=scan.result)
            if scan.clean:
                ready.append(record)
        message = self.store.transition_message(message.id, MessageStatus.QUARANTINED,
                                                reason="attachments evaluated")
        if not ready:
            message = self.store.transition_message(message.id, MessageStatus.REJECTED,
                                                    reason="no acceptable attachments")
            return ProcessingResult(ref, message.status, None, False)
        message = self.store.transition_message(message.id, MessageStatus.READY,
                                                reason="attachments ready")
        command_id = f"cmd-{uuid4()}"
        command = CaronteCommand(
            schema_version="1.0", command_id=command_id,
            created_at=datetime.now(timezone.utc).isoformat(), connector_id=self.config.connector_id,
            connector_type="local_imap", account_alias=self.config.account_alias,
            provider_hint=self.config.provider_hint, mailbox=ref.mailbox,
            mailbox_uidvalidity=ref.uidvalidity, message_uid=ref.message_uid,
            message_id=ref.message_id, thread_id=ref.thread_id, subject=ref.subject,
            sender=ref.sender, date=ref.date, user_confirmed_command=True,
            attachments=tuple(Attachment(x.local_temp_id, x.original_filename,
                x.sanitized_filename, x.mime_type, x.size_bytes, x.sha256,
                x.quarantine_status, x.scan_engine, x.scan_result) for x in ready),
            requested_action="stage_attachments_in_limbo", dry_run=self.config.dry_run)
        request_digest = hashlib.sha256(command_to_json(command).encode()).hexdigest()
        attempt = self.store.start_command_attempt(message.id, command_id=command_id,
            dry_run=self.config.dry_run, request_sha256=request_digest)
        message = self.store.transition_message(message.id, MessageStatus.SUBMITTING,
                                                reason="command submitted", command_id=command_id)
        response = self.caronte.submit(command)
        decision = evaluate_ack(command, response)
        self.store.complete_command_attempt(attempt.id, succeeded=response.ok,
            response_ok=response.ok, response_message=response.message,
            error_code=None if response.ok else "CARONTE_REJECTED", retryable=False)
        if decision.allowed:
            drive = {x.local_temp_id: x.drive_file_id for x in response.limbo_drive_ids}
            rows = {x.local_temp_id: x.row_reference for x in response.bucoliche_rows}
            for item in response.accepted_attachments:
                if item.local_temp_id in drive:
                    self.store.transition_attachment(item.local_temp_id,
                        QuarantineStatus.UPLOADED_TO_LIMBO, reason="Caronte confirmed upload",
                        drive_file_id=drive[item.local_temp_id],
                        bucoliche_row_reference=rows.get(item.local_temp_id))
            message = self.store.transition_message(message.id, MessageStatus.ACK_PENDING,
                reason="valid Caronte response", command_id=command_id)
            self.mailbox.acknowledge(ref)
            message = self.store.transition_message(message.id, MessageStatus.ACKNOWLEDGED,
                                                    reason="mailbox ack completed")
            return ProcessingResult(ref, message.status, command_id, True)
        message = self.store.transition_message(message.id, MessageStatus.ERROR,
                                                reason=decision.reason, last_error=decision.reason)
        return ProcessingResult(ref, message.status, command_id, False)
