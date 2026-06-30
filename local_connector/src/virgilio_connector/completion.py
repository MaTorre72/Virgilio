"""Controlled local completion for staged IMAP messages."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from contextlib import closing
from typing import Callable, Mapping, Sequence

from .imap_readonly import ImapCompletionMailbox
from .local_paths import LocalDataPaths
from .multi_account import LocalImapAccount, MultiAccountConfigError
from .readonly_state import ReadonlyStateStore, ensure_state_db
from .traceability import load_machine_id


BLOCKING_ATTACHMENT_STATES = {
    "scan_failed", "rejected_malware", "staging_failed", "staging_conflict",
}


class CompletionError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CompletionResult:
    account_alias: str
    message_row_id: int
    message_uid: str
    message_id: str
    subject: str
    staged_attachments: tuple[str, ...]
    status: str
    dry_run: bool
    ack_strategy: str | None
    report_path: str | None = None
    reason: str | None = None


class LocalCompletionRunner:
    def __init__(self, accounts: Sequence[LocalImapAccount], *,
                 paths: LocalDataPaths | None = None,
                 environ: Mapping[str, str] | None = None,
                 mailbox_factory: Callable[[LocalImapAccount], object] | None = None) -> None:
        self.accounts = {account.account_alias: account for account in accounts}
        self.paths = paths or LocalDataPaths()
        self.environ = environ
        self.mailbox_factory = mailbox_factory or self._default_mailbox

    def complete(self, *, dry_run: bool) -> tuple[CompletionResult, ...]:
        ensure_state_db(self.paths.root)
        candidates = self._load_candidates()
        store = ReadonlyStateStore(self.paths.state_db)
        if not dry_run:
            store.initialize()
        results: list[CompletionResult] = []
        for candidate in candidates:
            result = self._complete_one(candidate, store, dry_run=dry_run)
            results.append(result)
        report_path = None if dry_run else self._write_report(results)
        if report_path:
            for result in results:
                if result.status in {"completed", "already_completed", "already_acked", "ack_failed", "completion_skipped"}:
                    store.update_message_completion(
                        result.message_row_id,
                        message_state=("completed" if result.status in {"completed", "already_completed", "already_acked"}
                                       else "ack_failed" if result.status == "ack_failed"
                                       else "completion_skipped"),
                        ack_strategy=result.ack_strategy,
                        ack_result=result.status,
                        report_path=report_path,
                        attempted=False,
                        completed=result.status in {"completed", "already_completed", "already_acked"},
                    )
                    if result.status != "already_completed":
                        action = ("message_completed" if result.status in
                                  {"completed", "already_acked"}
                                  else "failed" if result.status == "ack_failed" else "skipped")
                        machine_id = load_machine_id(self.paths.root)
                        for attachment_id, fingerprint in self._attachment_audit_targets(result.message_row_id):
                            store.add_audit_event(machine_id=machine_id,
                                account_alias=result.account_alias, entity_type="attachment",
                                entity_id=attachment_id, fingerprint=fingerprint,
                                action=action, status=result.status,
                                details={"reason": result.reason or ""})
        return tuple(CompletionResult(**{**asdict(item), "report_path": report_path or item.report_path})
                     for item in results)

    def _complete_one(self, row: sqlite3.Row, store: ReadonlyStateStore,
                      *, dry_run: bool) -> CompletionResult:
        staged = tuple(str(row["staged_attachment_ids"]).split("|")) if row["staged_attachment_ids"] else ()
        base = {
            "account_alias": str(row["account_alias"]),
            "message_row_id": int(row["message_row_id"]),
            "message_uid": str(row["message_uid"]),
            "message_id": str(row["message_id"] or ""),
            "subject": str(row["subject"] or ""),
            "staged_attachments": staged,
            "dry_run": dry_run,
        }
        if str(row["message_state"]) in {"completed", "acked"}:
            return CompletionResult(**base, status="already_completed",
                                    ack_strategy=row["ack_strategy"],
                                    reason="message already completed")
        account = self.accounts.get(str(row["account_alias"]))
        if account is None:
            return CompletionResult(**base, status="completion_skipped",
                                    ack_strategy=None,
                                    reason="account_alias not configured")
        if int(row["blocking_count"]) > 0:
            return CompletionResult(**base, status="completion_skipped",
                                    ack_strategy=None,
                                    reason="message has blocking attachment states")
        if int(row["staged_count"]) <= 0:
            return CompletionResult(**base, status="completion_skipped",
                                    ack_strategy=None,
                                    reason="message has no staged_storage attachment")
        if not account.ack_enabled:
            return CompletionResult(**base, status="completion_skipped",
                                    ack_strategy=account.ack_strategy,
                                    reason="ack_enabled is false")
        if account.ack_strategy != "add_done_label_only":
            return CompletionResult(**base, status="completion_skipped",
                                    ack_strategy=account.ack_strategy,
                                    reason=f"unsupported ack strategy: {account.ack_strategy}")
        if dry_run:
            return CompletionResult(**base, status="planned",
                                    ack_strategy=account.ack_strategy,
                                    reason="would add done label only")
        mailbox = self.mailbox_factory(account)
        try:
            if not mailbox.input_contains_uid(str(row["message_uid"])):
                if mailbox.done_contains_message_id(str(row["message_id"] or "")):
                    store.update_message_completion(int(row["message_row_id"]),
                        message_state="completed", ack_strategy=account.ack_strategy,
                        ack_result="already_acked", attempted=False, completed=True)
                    return CompletionResult(**base, status="already_acked",
                                            ack_strategy=account.ack_strategy,
                                            reason="message already present in done folder")
                store.update_message_completion(int(row["message_row_id"]),
                    message_state="ack_failed", ack_strategy=account.ack_strategy,
                    ack_result="message_not_found", attempted=True, completed=False)
                return CompletionResult(**base, status="ack_failed",
                                        ack_strategy=account.ack_strategy,
                                        reason="message not found in input or done folder")
            store.update_message_completion(int(row["message_row_id"]),
                message_state="ready_for_ack", ack_strategy=account.ack_strategy,
                ack_result="attempting", attempted=True, completed=False)
            mailbox.add_done_label_only(str(row["message_uid"]))
            store.update_message_completion(int(row["message_row_id"]),
                message_state="completed", ack_strategy=account.ack_strategy,
                ack_result="completed", attempted=False, completed=True)
            return CompletionResult(**base, status="completed",
                                    ack_strategy=account.ack_strategy,
                                    reason="done label added; input message not removed")
        except Exception as exc:
            store.update_message_completion(int(row["message_row_id"]),
                message_state="ack_failed", ack_strategy=account.ack_strategy,
                ack_result=f"ack_failed: {type(exc).__name__}", attempted=True,
                completed=False)
            return CompletionResult(**base, status="ack_failed",
                                    ack_strategy=account.ack_strategy,
                                    reason=f"ack failed: {exc}")

    def _load_candidates(self) -> tuple[sqlite3.Row, ...]:
        if not self.paths.state_db.is_file():
            raise FileNotFoundError(f"state database not found: {self.paths.state_db}")
        uri = f"{self.paths.state_db.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            return tuple(db.execute(f"""SELECT m.id AS message_row_id,m.account_alias,
                m.message_uid,m.message_id,m.subject,m.message_state,m.ack_strategy,
                SUM(CASE WHEN a.status='staged_storage' THEN 1 ELSE 0 END) AS staged_count,
                SUM(CASE WHEN a.status IN ({','.join('?' for _ in BLOCKING_ATTACHMENT_STATES)})
                    THEN 1 ELSE 0 END) AS blocking_count,
                GROUP_CONCAT(CASE WHEN a.status='staged_storage' THEN a.attachment_id END, '|')
                    AS staged_attachment_ids
                FROM messages m LEFT JOIN attachments a ON a.message_id=m.id
                GROUP BY m.id
                HAVING staged_count > 0 OR blocking_count > 0
                    OR m.message_state IN ('completed','acked')
                ORDER BY m.account_alias,m.id""", tuple(BLOCKING_ATTACHMENT_STATES)).fetchall())

    def _write_report(self, results: Sequence[CompletionResult]) -> str:
        reports = self.paths.root / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = reports / f"completion_report_{timestamp}.json"
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "messages_candidates": len(results),
            "messages_completed": sum(1 for item in results if item.status in {"completed", "already_completed", "already_acked"}),
            "messages_skipped": sum(1 for item in results if item.status == "completion_skipped"),
            "errors": [asdict(item) for item in results if item.status == "ack_failed"],
            "results": [asdict(item) for item in results],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path.relative_to(self.paths.root).as_posix()

    def _attachment_audit_targets(self, message_row_id: int) -> tuple[tuple[str, str], ...]:
        uri = f"{self.paths.state_db.resolve().as_uri()}?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as db:
            rows = db.execute("""SELECT attachment_id,fingerprint FROM attachments
                WHERE message_id=? AND attachment_id IS NOT NULL AND fingerprint IS NOT NULL
                ORDER BY id""", (message_row_id,)).fetchall()
        return tuple((str(row[0]), str(row[1])) for row in rows)

    def _default_mailbox(self, account: LocalImapAccount):
        config = account.to_imap_config(self.environ)
        return ImapCompletionMailbox(config, done_folder=account.done_folder)
