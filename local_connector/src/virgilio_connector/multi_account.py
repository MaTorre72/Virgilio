"""Multi-account IMAP read-only configuration and scan runner."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Callable, Mapping, Sequence

from .imap_readonly import ImapReadonlyConfig, ImapReadonlyMailbox
from .local_paths import LocalDataPaths
from .ports import MessageReference
from .readonly_state import ReadonlyStateStore


class MultiAccountConfigError(ValueError):
    """Raised when the local multi-account configuration is unsafe or invalid."""


_ALIAS_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,62}$")
_ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass(frozen=True, slots=True)
class LocalImapAccount:
    account_alias: str
    email: str
    provider_hint: str
    imap_host: str
    imap_port: int
    username_env: str
    password_env: str
    input_folder: str
    done_folder: str
    error_folder: str
    enabled: bool = True
    max_messages: int = 25

    def __post_init__(self) -> None:
        if not _ALIAS_RE.fullmatch(self.account_alias):
            raise MultiAccountConfigError("account_alias must be lowercase, stable and filesystem-safe")
        if "@" not in self.email or not self.email.strip():
            raise MultiAccountConfigError("email is required")
        if not self.provider_hint.strip():
            raise MultiAccountConfigError("provider_hint is required")
        if not self.imap_host.strip():
            raise MultiAccountConfigError("imap_host is required")
        if not 1 <= int(self.imap_port) <= 65535:
            raise MultiAccountConfigError("imap_port must be between 1 and 65535")
        for field_name, value in (("username_env", self.username_env),
                                  ("password_env", self.password_env)):
            if not _ENV_RE.fullmatch(value):
                raise MultiAccountConfigError(f"{field_name} must be an environment variable name")
        for field_name, value in (("input_folder", self.input_folder),
                                  ("done_folder", self.done_folder),
                                  ("error_folder", self.error_folder)):
            if not value.strip():
                raise MultiAccountConfigError(f"{field_name} is required")
        if self.max_messages <= 0:
            raise MultiAccountConfigError("max_messages must be positive")

    def to_imap_config(self, environ: Mapping[str, str] | None = None) -> ImapReadonlyConfig:
        env = os.environ if environ is None else environ
        username = env.get(self.username_env, "").strip()
        password = env.get(self.password_env, "")
        if not username:
            raise MultiAccountConfigError(
                f"missing username environment variable for {self.account_alias}: {self.username_env}"
            )
        if not password:
            raise MultiAccountConfigError(
                f"missing password environment variable for {self.account_alias}: {self.password_env}"
            )
        return ImapReadonlyConfig(
            host=self.imap_host,
            port=self.imap_port,
            username=username,
            password=password,
            mailbox=self.input_folder,
            max_messages=self.max_messages,
        )


@dataclass(frozen=True, slots=True)
class MultiAccountScanResult:
    account_alias: str
    email: str
    provider_hint: str
    enabled: bool
    status: str
    messages_seen: int
    error: str | None = None


def load_multi_account_config(path: str | Path) -> tuple[LocalImapAccount, ...]:
    """Load a small, repository-free YAML subset for local account config.

    Supported shape:

    accounts:
      - account_alias: marco_sigmapiu
        email: marco@example.invalid
        ...
    """
    raw_accounts = _parse_accounts_yaml(Path(path))
    accounts = tuple(_account_from_mapping(item) for item in raw_accounts)
    if not accounts:
        raise MultiAccountConfigError("configuration must contain at least one account")
    aliases = [item.account_alias for item in accounts]
    if len(set(aliases)) != len(aliases):
        raise MultiAccountConfigError("account_alias values must be unique")
    return accounts


class MultiAccountReadonlyScanner:
    """Scans configured IMAP accounts without downloads, ack or remote calls."""

    def __init__(self, accounts: Sequence[LocalImapAccount], *,
                 paths: LocalDataPaths | None = None,
                 environ: Mapping[str, str] | None = None,
                 mailbox_factory: Callable[[ImapReadonlyConfig, Path], object] | None = None) -> None:
        self.accounts = tuple(accounts)
        self.paths = paths or LocalDataPaths()
        self.environ = os.environ if environ is None else environ
        self.mailbox_factory = mailbox_factory or (
            lambda config, root: ImapReadonlyMailbox(config, root)
        )

    def scan(self, *, dry_run: bool) -> tuple[MultiAccountScanResult, ...]:
        if not dry_run:
            self.paths.root.mkdir(parents=True, exist_ok=True)
            store = ReadonlyStateStore(self.paths.state_db)
            store.initialize()
        else:
            store = None
        results: list[MultiAccountScanResult] = []
        for account in self.accounts:
            if not account.enabled:
                results.append(MultiAccountScanResult(
                    account.account_alias, account.email, account.provider_hint,
                    False, "disabled", 0,
                ))
                continue
            try:
                imap_config = account.to_imap_config(self.environ)
                mailbox = self.mailbox_factory(imap_config, self.paths.quarantine / account.account_alias)
                messages = tuple(mailbox.list_pending())
                if store is not None:
                    run_id = store.start_run(account_alias=account.account_alias)
                    for message in messages:
                        store.add_message(run_id, message, account_alias=account.account_alias)
                    store.complete_run(run_id, messages_seen=len(messages), attachments_seen=0)
                results.append(MultiAccountScanResult(
                    account.account_alias, account.email, account.provider_hint,
                    True, "ok", len(messages),
                ))
            except Exception as exc:
                if store is not None:
                    run_id = store.start_run(account_alias=account.account_alias)
                    store.complete_run(run_id, messages_seen=0, attachments_seen=0, status="error")
                results.append(MultiAccountScanResult(
                    account.account_alias, account.email, account.provider_hint,
                    True, "error", 0, str(exc),
                ))
        return tuple(results)


def _account_from_mapping(raw: Mapping[str, object]) -> LocalImapAccount:
    required = {
        "account_alias", "email", "provider_hint", "imap_host", "imap_port",
        "username_env", "password_env", "input_folder", "done_folder",
        "error_folder",
    }
    missing = sorted(required - set(raw))
    if missing:
        raise MultiAccountConfigError(f"account is missing required fields: {', '.join(missing)}")
    return LocalImapAccount(
        account_alias=str(raw["account_alias"]),
        email=str(raw["email"]),
        provider_hint=str(raw["provider_hint"]),
        imap_host=str(raw["imap_host"]),
        imap_port=int(raw["imap_port"]),
        username_env=str(raw["username_env"]),
        password_env=str(raw["password_env"]),
        input_folder=str(raw["input_folder"]),
        done_folder=str(raw["done_folder"]),
        error_folder=str(raw["error_folder"]),
        enabled=_to_bool(raw.get("enabled", True)),
        max_messages=int(raw.get("max_messages", 25)),
    )


def _parse_accounts_yaml(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        raise MultiAccountConfigError(f"configuration file not found: {path}")
    accounts: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    in_accounts = False
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.strip() == "accounts:":
            in_accounts = True
            continue
        if not in_accounts:
            raise MultiAccountConfigError(f"unsupported content before accounts at line {line_number}")
        stripped = line.strip()
        if stripped.startswith("- "):
            if current is not None:
                accounts.append(current)
            current = {}
            stripped = stripped[2:].strip()
            if stripped:
                key, value = _split_key_value(stripped, line_number)
                current[key] = _parse_scalar(value)
            continue
        if current is None:
            raise MultiAccountConfigError(f"account item expected at line {line_number}")
        key, value = _split_key_value(stripped, line_number)
        current[key] = _parse_scalar(value)
    if current is not None:
        accounts.append(current)
    return accounts


def _split_key_value(text: str, line_number: int) -> tuple[str, str]:
    if ":" not in text:
        raise MultiAccountConfigError(f"expected key: value at line {line_number}")
    key, value = text.split(":", 1)
    key = key.strip()
    if not key:
        raise MultiAccountConfigError(f"empty key at line {line_number}")
    return key, value.strip()


def _parse_scalar(value: str) -> object:
    value = value.strip()
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
        return value[1:-1]
    if value.isdigit():
        return int(value)
    return value


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    raise MultiAccountConfigError("enabled must be true or false")
