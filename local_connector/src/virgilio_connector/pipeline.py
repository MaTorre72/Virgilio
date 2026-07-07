"""Single-command local pipeline composed from existing connector blocks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from time import perf_counter
from typing import Callable, Sequence

from .completion import LocalCompletionRunner
from .local_paths import LocalDataPaths
from .multi_account import LocalImapAccount, MultiAccountImapProcessor, MultiAccountReadonlyScanner
from .storage_adapter import LocalFilesystemStorageAdapter
from .readonly_state import ensure_state_db
from .time_utils import rome_isoformat, rome_timestamp


@dataclass(frozen=True, slots=True)
class PipelineResult:
    report_path: str | None
    dry_run: bool
    status: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    human_summary: tuple[str, ...] = ()


class LocalPipelineRunner:
    def __init__(self, accounts: Sequence[LocalImapAccount], *, paths: LocalDataPaths,
                 processor_factory: Callable[[], MultiAccountImapProcessor],
                 storage_factory: Callable[[], LocalFilesystemStorageAdapter],
                 completion_factory: Callable[[], LocalCompletionRunner],
                 scanner_factory: Callable[[], MultiAccountReadonlyScanner] | None = None,
                 config_path: Path | None = None) -> None:
        self.accounts = tuple(accounts)
        self.paths = paths
        self.processor_factory = processor_factory
        self.storage_factory = storage_factory
        self.completion_factory = completion_factory
        self.scanner_factory = scanner_factory
        self.config_path = config_path

    def run(self, *, dry_run: bool) -> PipelineResult:
        started = perf_counter()
        phase_times: dict[str, float] = {}
        errors: list[str] = []
        _, initial_warnings = ensure_state_db(self.paths.root)
        warnings: list[str] = list(initial_warnings)
        scan = self._phase("scan", phase_times, errors, lambda: (
            self.scanner_factory().scan(dry_run=dry_run) if self.scanner_factory else ()
        ))
        process = self._phase("process", phase_times, errors,
                              lambda: self.processor_factory().process(dry_run=dry_run))
        storage = self._phase("storage", phase_times, errors,
                              lambda: self.storage_factory().stage_ready(dry_run=dry_run))
        completion = self._phase("completion", phase_times, errors,
                                 lambda: self.completion_factory().complete(dry_run=dry_run))
        if not storage:
            warnings.append("storage: skipped_no_ready_attachments")
        if not completion:
            warnings.append("completion: skipped_no_staged_messages")
        status = ("completed_with_errors" if errors else
                  "completed_with_warnings" if warnings else "completed")
        report = {
            "timestamp": rome_isoformat(),
            "config": str(self.config_path) if self.config_path else None,
            "accounts": [item.account_alias for item in self.accounts if item.enabled],
            "messages_found": sum(getattr(item, "messages_seen", 0) for item in scan),
            "attachments_processed": len(process),
            "attachments_staged": sum(1 for item in storage if getattr(item, "status", "") in {"staged_storage", "already_staged"}),
            "messages_completed": sum(1 for item in completion if getattr(item, "status", "") in {"completed", "already_completed", "already_acked"}),
            "messages_skipped": sum(1 for item in completion if getattr(item, "status", "") == "completion_skipped"),
            "errors": errors,
            "warnings": warnings,
            "duration_seconds": round(perf_counter() - started, 3),
            "phase_durations": phase_times,
            "phases": {
                "scan": [asdict(item) for item in scan],
                "process": [asdict(item) for item in process],
                "storage": [asdict(item) for item in storage],
                "completion": [asdict(item) for item in completion],
            },
        }
        report["human_summary"] = self._human_summary(report, status=status, dry_run=dry_run)
        report_path = None if dry_run else self._write_report(report)
        return PipelineResult(report_path, dry_run, status, tuple(errors), tuple(warnings),
                              tuple(report["human_summary"]))

    @staticmethod
    def _phase(name: str, timings: dict[str, float], errors: list[str], call):
        start = perf_counter()
        try:
            return tuple(call())
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
            return ()
        finally:
            timings[name] = round(perf_counter() - start, 3)

    def _write_report(self, payload: dict[str, object]) -> str:
        reports = self.paths.root / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        name = f"pipeline_report_{rome_timestamp()}.json"
        path = reports / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path.relative_to(self.paths.root).as_posix()

    @staticmethod
    def _human_summary(report: dict[str, object], *, status: str, dry_run: bool) -> list[str]:
        accounts = report["accounts"] or ["nessun account abilitato"]
        lines = [
            f"Esito pipeline: {status} ({'dry-run' if dry_run else 'run reale'})",
            f"Account abilitate: {', '.join(accounts)}",
            ("Messaggi trovati: {messages_found}; allegati processati: {attachments_processed}; "
             "allegati staged: {attachments_staged}; messaggi completati: {messages_completed}; "
             "messaggi saltati: {messages_skipped}").format(**report),
            f"Durata totale: {report['duration_seconds']}s",
        ]
        for warning in report["warnings"]:
            lines.append(f"Warning: {warning}")
        for error in report["errors"]:
            lines.append(f"Errore: {error}")
        if report["errors"]:
            lines.append("Azione consigliata: correggere gli errori e ripetere il dry-run.")
        elif report["warnings"]:
            lines.append("Azione consigliata: verificare i warning prima del run successivo.")
        else:
            lines.append("Azione consigliata: report pulito, pronto per il passo successivo.")
        return lines
