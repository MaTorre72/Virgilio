"""Command-line entrypoint for explicit, opt-in connector actions."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import sqlite3

from .caronte_http import CaronteDryRunClientError, CaronteDryRunHttpClient
from .bucoliche import BucolicheAppendOnlyAdapter, BucolicheError, load_bucoliche_config
from .completion import CompletionError, LocalCompletionRunner
from .staging_transport import (
    LocalDriveStagingConfig,
    LocalDriveStagingTransport,
    StagingTransportError,
)
from .drive_staging_verify import (
    DriveStagingVerifyClient,
    DriveStagingVerifyError,
)
from .drive_staging_intake_test import (
    DriveStagingIntakeTestClient,
    DriveStagingIntakeTestError,
)
from .doctor import LocalDoctor
from .local_paths import LocalDataPaths
from .multi_account import (
    LocalStorageConfig,
    MultiAccountConfigError,
    MultiAccountImapProcessor,
    MultiAccountReadonlyScanner,
    load_storage_config,
    load_multi_account_config,
)
from .pipeline import LocalPipelineRunner
from .pilot_readiness import BucolicheDoctor, PilotCheck, has_bucoliche_section
from .scanner import select_scanner
from .storage_adapter import LocalFilesystemStorageAdapter, StorageAdapterError
from .traceability import LocalConflictChecker, export_central_events, load_rules


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    _load_env_file(Path(".env"))
    parser = argparse.ArgumentParser(prog="python -m virgilio_connector")
    commands = parser.add_subparsers(dest="command", required=True)
    sender = commands.add_parser("send-caronte-dry-run")
    sender.add_argument("--command-file", type=Path, required=True)
    staging = commands.add_parser("stage-ready-files")
    staging.add_argument("--dry-run", action="store_true")
    verifier = commands.add_parser("verify-drive-staging")
    verifier.add_argument("--manifest", type=Path, required=True)
    intake = commands.add_parser("intake-drive-staging-test")
    intake.add_argument("--manifest", type=Path, required=True)
    scanner = commands.add_parser("scan-imap-accounts")
    scanner.add_argument("--config", type=Path, required=True)
    scanner.add_argument("--dry-run", action="store_true")
    processor = commands.add_parser("process-imap-accounts")
    processor.add_argument("--config", type=Path, required=True)
    processor.add_argument("--dry-run", action="store_true")
    storage = commands.add_parser("stage-ready-attachments")
    storage.add_argument("--config", type=Path, required=True)
    storage.add_argument("--dry-run", action="store_true")
    completer = commands.add_parser("complete-staged-messages")
    completer.add_argument("--config", type=Path, required=True)
    completer.add_argument("--dry-run", action="store_true")
    pipeline = commands.add_parser("run-local-pipeline")
    pipeline.add_argument("--config", type=Path, required=True)
    pipeline.add_argument("--dry-run", action="store_true")
    doctor = commands.add_parser("doctor")
    doctor.add_argument("--config", type=Path, required=True)
    conflicts = commands.add_parser("check-local-conflicts")
    conflicts.add_argument("--config", type=Path, required=True)
    exporter = commands.add_parser("export-central-events")
    exporter.add_argument("--config", type=Path, required=True)
    exporter.add_argument("--format", choices=("jsonl", "csv"), default="jsonl")
    bucoliche = commands.add_parser("export-to-bucoliche")
    bucoliche.add_argument("--config", type=Path, required=True)
    bucoliche.add_argument("--dry-run", action="store_true")
    doctor_bucoliche = commands.add_parser("doctor-bucoliche")
    doctor_bucoliche.add_argument("--config", type=Path, required=True)
    pilot_check = commands.add_parser("pilot-check")
    pilot_check.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "send-caronte-dry-run":
        client = CaronteDryRunHttpClient(
            os.environ.get("VIRGILIO_CARONTE_DRY_RUN_URL"),
            timeout_seconds=float(os.environ.get("VIRGILIO_CARONTE_TIMEOUT_SECONDS", "15")),
        )
        try:
            result = client.send_command_file(args.command_file)
        except CaronteDryRunClientError as exc:
            parser.exit(2, f"error: {exc}\n")
        print(json.dumps(asdict(result), ensure_ascii=False, separators=(",", ":")))
        return 0 if result.ok else 1
    if args.command == "stage-ready-files":
        enabled_text = os.environ.get("VIRGILIO_LOCAL_DRIVE_STAGING_ENABLED", "false")
        if enabled_text.lower() not in {"true", "false"}:
            parser.exit(2, "error: VIRGILIO_LOCAL_DRIVE_STAGING_ENABLED must be true or false\n")
        staging_text = os.environ.get("VIRGILIO_LOCAL_DRIVE_STAGING_DIR", "").strip()
        local_root = Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data"))
        transport = LocalDriveStagingTransport(
            state_db=local_root / "state.db", local_data_root=local_root,
            config=LocalDriveStagingConfig(
                enabled=enabled_text.lower() == "true",
                staging_dir=Path(staging_text) if staging_text else None,
                account_alias=os.environ.get("VIRGILIO_ACCOUNT_ALIAS", "gmail-test"),
            ),
        )
        try:
            results = transport.stage_ready_files(dry_run=args.dry_run)
        except (StagingTransportError, FileNotFoundError) as exc:
            parser.exit(2, f"error: {exc}\n")
        print(json.dumps([asdict(item) for item in results], ensure_ascii=False,
                         separators=(",", ":")))
        return 0
    if args.command == "verify-drive-staging":
        client = DriveStagingVerifyClient(
            os.environ.get("VIRGILIO_CARONTE_DRIVE_VERIFY_URL"),
            timeout_seconds=float(os.environ.get("VIRGILIO_CARONTE_TIMEOUT_SECONDS", "15")),
        )
        try:
            result = client.verify_manifest(args.manifest)
        except DriveStagingVerifyError as exc:
            parser.exit(2, f"error: {exc}\n")
        print(json.dumps(asdict(result), ensure_ascii=False, separators=(",", ":")))
        return 0 if result.ok else 1
    if args.command == "intake-drive-staging-test":
        client = DriveStagingIntakeTestClient(
            os.environ.get("VIRGILIO_CARONTE_INTAKE_TEST_URL"),
            timeout_seconds=float(os.environ.get("VIRGILIO_CARONTE_TIMEOUT_SECONDS", "15")),
        )
        try:
            result = client.intake_manifest(args.manifest)
        except DriveStagingIntakeTestError as exc:
            parser.exit(2, f"error: {exc}\n")
        print(json.dumps(asdict(result), ensure_ascii=False, separators=(",", ":")))
        return 0 if result.ok else 1
    if args.command == "scan-imap-accounts":
        try:
            accounts = load_multi_account_config(args.config)
            results = MultiAccountReadonlyScanner(
                accounts,
                paths=LocalDataPaths(Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data"))),
            ).scan(dry_run=args.dry_run)
        except MultiAccountConfigError as exc:
            parser.exit(2, f"error: {exc}\n")
        print(json.dumps([asdict(item) for item in results], ensure_ascii=False,
                         separators=(",", ":")))
        return 0 if all(item.status in {"ok", "disabled"} for item in results) else 1
    if args.command == "process-imap-accounts":
        try:
            accounts = load_multi_account_config(args.config)
            results = MultiAccountImapProcessor(
                accounts,
                paths=LocalDataPaths(Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data"))),
                scanner=select_scanner(os.environ.get("VIRGILIO_SCANNER", "auto")),
                rules=load_rules(args.config),
                max_attachment_bytes=int(os.environ.get("VIRGILIO_MAX_ATTACHMENT_BYTES", "26214400")),
            ).process(dry_run=args.dry_run)
        except (MultiAccountConfigError, ValueError) as exc:
            parser.exit(2, f"error: {exc}\n")
        print(json.dumps([asdict(item) for item in results], ensure_ascii=False,
                         separators=(",", ":")))
        return 0 if all(item.quarantine_status != "error" for item in results) else 1
    if args.command == "stage-ready-attachments":
        local_root = Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data"))
        try:
            # Validate account configuration too; the storage rows are keyed by account_alias.
            load_multi_account_config(args.config)
            storage_config = load_storage_config(args.config)
            results = LocalFilesystemStorageAdapter(
                state_db=local_root / "state.db",
                local_data_root=local_root,
                config=storage_config,
            ).stage_ready(dry_run=args.dry_run)
        except (MultiAccountConfigError, StorageAdapterError, FileNotFoundError) as exc:
            parser.exit(2, f"error: {exc}\n")
        print(json.dumps([asdict(item) for item in results], ensure_ascii=False,
                         separators=(",", ":")))
        return 0 if all(item.status not in {"staging_failed", "staging_conflict"}
                        for item in results) else 1
    if args.command == "complete-staged-messages":
        local_root = Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data"))
        try:
            accounts = load_multi_account_config(args.config)
            results = LocalCompletionRunner(
                accounts,
                paths=LocalDataPaths(local_root),
            ).complete(dry_run=args.dry_run)
        except (MultiAccountConfigError, CompletionError, FileNotFoundError) as exc:
            parser.exit(2, f"error: {exc}\n")
        print(json.dumps([asdict(item) for item in results], ensure_ascii=False,
                         separators=(",", ":")))
        return 0 if all(item.status != "ack_failed" for item in results) else 1
    if args.command == "run-local-pipeline":
        local_root = Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data"))
        try:
            accounts = load_multi_account_config(args.config)
            storage_config = load_storage_config(args.config)
            paths = LocalDataPaths(local_root)
            result = LocalPipelineRunner(
                accounts, paths=paths, config_path=args.config,
                scanner_factory=lambda: MultiAccountReadonlyScanner(accounts, paths=paths),
                processor_factory=lambda: MultiAccountImapProcessor(
                    accounts, paths=paths,
                    scanner=select_scanner(os.environ.get("VIRGILIO_SCANNER", "auto")),
                    rules=load_rules(args.config),
                    max_attachment_bytes=int(os.environ.get("VIRGILIO_MAX_ATTACHMENT_BYTES", "26214400")),
                ),
                storage_factory=lambda: LocalFilesystemStorageAdapter(
                    state_db=paths.state_db, local_data_root=paths.root, config=storage_config,
                ),
                completion_factory=lambda: LocalCompletionRunner(accounts, paths=paths),
            ).run(dry_run=args.dry_run)
        except (MultiAccountConfigError, ValueError) as exc:
            parser.exit(2, f"error: {exc}\n")
        print(json.dumps(asdict(result), ensure_ascii=False, separators=(",", ":")))
        return 0 if result.status == "ok" else 1
    if args.command == "doctor":
        local_root = Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data"))
        try:
            accounts = load_multi_account_config(args.config)
            storage_config = load_storage_config(args.config)
            result = LocalDoctor(
                accounts, storage=storage_config, paths=LocalDataPaths(local_root),
                scanner=select_scanner(os.environ.get("VIRGILIO_SCANNER", "auto")),
            ).run()
        except MultiAccountConfigError as exc:
            parser.exit(2, json.dumps({
                "status": "BLOCKED", "errors": [str(exc)], "warnings": [], "accounts": []
            }, ensure_ascii=False, separators=(",", ":")) + "\n")
        print(result.to_json())
        return 0 if result.status in {"READY", "READY_WITH_WARNINGS"} else 1
    if args.command == "check-local-conflicts":
        local_root = Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data"))
        try:
            load_multi_account_config(args.config)
            result = LocalConflictChecker(local_root / "state.db").check()
        except (MultiAccountConfigError, FileNotFoundError, sqlite3.Error) as exc:
            parser.exit(2, f"error: {exc}\n")
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 1 if result["status"] == "CONFLICTS" else 0
    if args.command == "export-central-events":
        local_root = Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data"))
        try:
            load_multi_account_config(args.config)
            target = export_central_events(local_root / "state.db", local_root, args.format)
        except (MultiAccountConfigError, FileNotFoundError, sqlite3.Error, ValueError) as exc:
            parser.exit(2, f"error: {exc}\n")
        print(json.dumps({"path": target.relative_to(local_root).as_posix()}, separators=(",", ":")))
        return 0
    if args.command == "export-to-bucoliche":
        local_root = Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data"))
        try:
            load_multi_account_config(args.config)
            result = BucolicheAppendOnlyAdapter(state_db=local_root / "state.db",
                config=load_bucoliche_config(args.config)).export(dry_run=args.dry_run)
        except (MultiAccountConfigError, BucolicheError, sqlite3.Error) as exc:
            parser.exit(2, f"error: {exc}\n")
        print(json.dumps(asdict(result), ensure_ascii=False, separators=(",", ":")))
        return 1 if result.status == "completed_with_errors" else 0
    if args.command == "doctor-bucoliche":
        try:
            config = load_bucoliche_config(args.config)
            result = BucolicheDoctor(config,
                config_has_section=has_bucoliche_section(args.config)).run()
        except (BucolicheError, OSError) as exc:
            result = {"status": "BLOCKED", "checks": [], "errors": [str(exc)],
                      "warnings": [], "suggested_next_commands": []}
            print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
            return 2
        print(result.to_json())
        return 0 if result.status in {"READY", "READY_WITH_WARNINGS"} else 1
    if args.command == "pilot-check":
        local_root = Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data"))
        try:
            result = PilotCheck(load_multi_account_config(args.config),
                storage=load_storage_config(args.config),
                bucoliche=load_bucoliche_config(args.config), config_path=args.config,
                paths=LocalDataPaths(local_root)).run()
        except (MultiAccountConfigError, BucolicheError, OSError, ValueError) as exc:
            payload = {"status": "BLOCKED", "checks": [], "errors": [str(exc)],
                       "warnings": [], "suggested_next_commands": []}
            print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
            return 2
        print(result.to_json())
        return 0 if result.status in {"READY", "READY_WITH_WARNINGS"} else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
