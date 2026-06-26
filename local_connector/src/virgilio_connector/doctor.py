"""Environment doctor for local Caronte pilot readiness."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path
import tempfile
from typing import Callable, Mapping, Sequence

from .imap_readonly import ImapReadonlyConfig, ImapReadonlyMailbox
from .local_paths import LocalDataPaths
from .multi_account import LocalImapAccount, LocalStorageConfig
from .readonly_state import ReadonlyStateStore
from .scanner import LocalScanner


@dataclass(frozen=True, slots=True)
class DoctorResult:
    status: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    accounts: tuple[dict[str, object], ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))


class LocalDoctor:
    def __init__(self, accounts: Sequence[LocalImapAccount], *,
                 storage: LocalStorageConfig,
                 paths: LocalDataPaths,
                 scanner: LocalScanner,
                 environ: Mapping[str, str] | None = None,
                 mailbox_factory: Callable[[ImapReadonlyConfig], object] | None = None) -> None:
        self.accounts = tuple(accounts)
        self.storage = storage
        self.paths = paths
        self.scanner = scanner
        self.environ = os.environ if environ is None else environ
        self.mailbox_factory = mailbox_factory or (lambda config: ImapReadonlyMailbox(config, paths.root))

    def run(self) -> DoctorResult:
        errors: list[str] = []
        warnings: list[str] = []
        account_rows: list[dict[str, object]] = []
        enabled = [item for item in self.accounts if item.enabled]
        if not enabled:
            errors.append("no enabled account configured")
        aliases = [item.account_alias for item in self.accounts]
        if len(set(aliases)) != len(aliases):
            errors.append("account_alias values are not unique")
        for account in enabled:
            account_rows.append(self._check_account(account, errors))
        self._check_local_data(errors, warnings)
        self._check_storage(errors)
        if not self.scanner.available:
            warnings.append("scanner unavailable; attachments may remain quarantined_unverified")
        status = "BLOCKED" if errors else "READY_WITH_WARNINGS" if warnings else "READY"
        return DoctorResult(status, tuple(errors), tuple(warnings), tuple(account_rows))

    def _check_account(self, account: LocalImapAccount, errors: list[str]) -> dict[str, object]:
        row: dict[str, object] = {
            "account_alias": account.account_alias,
            "email": account.email,
            "username_env": "OK" if self.environ.get(account.username_env) else "MISSING",
            "password_env": "OK" if self.environ.get(account.password_env) else "MISSING",
            "imap": "NOT_CHECKED",
        }
        if not account.input_folder:
            errors.append(f"{account.account_alias}: input_folder missing")
        if account.ack_enabled and not account.done_folder:
            errors.append(f"{account.account_alias}: done_folder missing with ack_enabled")
        if row["username_env"] == "MISSING":
            errors.append(f"{account.account_alias}: username_env missing")
        if row["password_env"] == "MISSING":
            errors.append(f"{account.account_alias}: password_env missing")
        if row["username_env"] == "OK" and row["password_env"] == "OK":
            try:
                config = account.to_imap_config(self.environ)
                self.mailbox_factory(config).list_pending()
                row["imap"] = "OK_READONLY"
            except Exception as exc:
                row["imap"] = "ERROR"
                errors.append(f"{account.account_alias}: IMAP read-only check failed: {type(exc).__name__}")
        return row

    def _check_local_data(self, errors: list[str], warnings: list[str]) -> None:
        try:
            self.paths.root.mkdir(parents=True, exist_ok=True)
            ReadonlyStateStore(self.paths.state_db).initialize()
        except Exception as exc:
            errors.append(f"local data not writable or SQLite not migrable: {type(exc).__name__}")
        if not self.paths.root.exists():
            warnings.append("local data directory does not exist yet")

    def _check_storage(self, errors: list[str]) -> None:
        staging = self.storage.staging_dir
        if staging is None:
            errors.append("storage staging_dir missing")
            return
        if not staging.exists():
            if self.storage.create_staging_dir:
                return
            errors.append("storage staging_dir does not exist")
            return
        if not staging.is_dir():
            errors.append("storage staging_dir is not a directory")
            return
        try:
            with tempfile.NamedTemporaryFile(prefix=".virgilio-doctor-", dir=staging, delete=False) as handle:
                handle.write(b"ok")
                temp = Path(handle.name)
            temp.unlink()
        except Exception as exc:
            errors.append(f"storage staging_dir not writable: {type(exc).__name__}")
