"""Multi-account IMAP read-only configuration and scan runner."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Callable, Mapping, Sequence

from .files import sanitize_filename
from .imap_readonly import ImapReadonlyConfig, ImapReadonlyMailbox
from .local_paths import LocalDataPaths
from .policy import AttachmentPolicy, PolicyDecision
from .ports import MessageReference
from .readonly_state import ReadonlyStateStore, ensure_state_db
from .scanner import LocalScanner, ScanVerdict, UnconfiguredScanner
from .traceability import RuleSet, audit_entry, global_fingerprint, load_machine_id


class MultiAccountConfigError(ValueError):
    """Raised when the local multi-account configuration is unsafe or invalid."""


_ALIAS_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,62}$")
_ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_PROVIDER_DEFAULTS = {
    "gmail_workspace": {
        "imap_host": "imap.gmail.com",
        "input_folder": "Virgilio/da-traghettare",
        "done_folder": "Virgilio/traghettate",
        "error_folder": "Virgilio/errore",
    },
    "generic_imap": {
        "imap_host": "imap.example.invalid",
        "input_folder": "INBOX",
        "done_folder": "done",
        "error_folder": "error",
    },
}


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
    ack_enabled: bool = False
    ack_strategy: str = "no_ack_manual"

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
        if self.ack_strategy not in {"no_ack_manual", "add_done_label_only"}:
            raise MultiAccountConfigError(f"unsupported ack_strategy: {self.ack_strategy}")

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

    def operational_email(self, environ: Mapping[str, str] | None = None) -> str:
        env = os.environ if environ is None else environ
        username = env.get(self.username_env, "").strip()
        if "@" in username:
            return username
        return self.email


@dataclass(frozen=True, slots=True)
class LocalStorageConfig:
    adapter: str
    staging_dir: Path | None
    use_account_subfolders: bool = True
    copy_manifest: bool = True
    overwrite: bool = False
    create_staging_dir: bool = False

    def __post_init__(self) -> None:
        if self.adapter != "local_filesystem":
            raise MultiAccountConfigError(f"unsupported storage adapter: {self.adapter}")
        if self.staging_dir is None or not str(self.staging_dir).strip():
            raise MultiAccountConfigError("storage.staging_dir is required")
        if self.overwrite:
            raise MultiAccountConfigError("storage overwrite must remain false in this phase")
        if not self.copy_manifest:
            raise MultiAccountConfigError("storage copy_manifest must remain true in this phase")


@dataclass(frozen=True, slots=True)
class MultiAccountScanResult:
    account_alias: str
    email: str
    provider_hint: str
    enabled: bool
    status: str
    messages_seen: int
    error: str | None = None


@dataclass(frozen=True, slots=True)
class MultiAccountAttachmentResult:
    account_alias: str
    source_email: str
    message_uid: str
    message_id: str
    subject: str
    attachment_id: str
    original_filename: str | None
    sanitized_filename: str | None
    sha256: str
    size_bytes: int
    mime_type: str
    scan_engine: str | None
    scan_result: str | None
    quarantine_status: str
    saved: bool
    manifest_path: str | None = None
    error: str | None = None
    fingerprint: str | None = None
    included: bool = True
    rule_name: str | None = None
    reason: str | None = None


def scaffold_local_config(*, email: str, staging_dir: Path, account_alias: str | None = None,
                          provider_hint: str = "gmail_workspace", imap_host: str | None = None,
                          imap_port: int = 993, input_folder: str | None = None,
                          done_folder: str | None = None, error_folder: str | None = None,
                          bucoliche_enabled: bool = False,
                          credentials_mode: str = "user_oauth_local") -> str:
    if provider_hint not in _PROVIDER_DEFAULTS:
        raise MultiAccountConfigError(f"unsupported provider_hint: {provider_hint}")
    alias = account_alias or _alias_from_email(email)
    if not _ALIAS_RE.fullmatch(alias):
        raise MultiAccountConfigError("account_alias must be lowercase, stable and filesystem-safe")
    if "@" not in email or not email.strip():
        raise MultiAccountConfigError("email is required")
    if not 1 <= int(imap_port) <= 65535:
        raise MultiAccountConfigError("imap_port must be between 1 and 65535")
    defaults = _PROVIDER_DEFAULTS[provider_hint]
    username_env = _env_name(alias, "USERNAME")
    password_env = _env_name(alias, "PASSWORD")
    lines = [
        "accounts:",
        f"  - account_alias: {alias}",
        f"    email: {email}",
        f"    provider_hint: {provider_hint}",
        f"    imap_host: {imap_host or defaults['imap_host']}",
        f"    imap_port: {int(imap_port)}",
        f"    username_env: {username_env}",
        f"    password_env: {password_env}",
        f"    input_folder: {_quoted(input_folder or defaults['input_folder'])}",
        f"    done_folder: {_quoted(done_folder or defaults['done_folder'])}",
        f"    error_folder: {_quoted(error_folder or defaults['error_folder'])}",
        "    enabled: true",
        "    max_messages: 25",
        "    ack_enabled: false",
        "    ack_strategy: no_ack_manual",
        "storage:",
        "  adapter: local_filesystem",
        f"  staging_dir: {_quoted(str(staging_dir))}",
        "  use_account_subfolders: true",
        "  copy_manifest: true",
        "  overwrite: false",
        "  create_staging_dir: false",
        "bucoliche:",
        f"  enabled: {_bool_text(bucoliche_enabled)}",
        "  adapter: google_sheets_append_only",
        f"  credentials_mode: {credentials_mode}",
        "  spreadsheet_id_env: VIRGILIO_BUCOLICHE_SPREADSHEET_ID",
        "  oauth_client_secrets_path_env: VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH",
        "  oauth_token_path_env: VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH",
        "rules:",
        "  default_action: include",
        "",
        "# Inserire i valori reali solo in .env o nelle variabili d'ambiente locali:",
        f"# {username_env}=utente@example.com",
        f"# {password_env}=password-app-o-token",
        "# VIRGILIO_BUCOLICHE_SPREADSHEET_ID=sheet-id-di-test",
        "# VIRGILIO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH=C:\\path\\client_secret.json",
        "# VIRGILIO_GOOGLE_OAUTH_TOKEN_PATH=C:\\path\\google-token.json",
        "",
    ]
    return "\n".join(lines)


def load_multi_account_config(path: str | Path) -> tuple[LocalImapAccount, ...]:
    """Load a small, repository-free YAML subset for local account config.

    Supported shape:

    accounts:
      - account_alias: marco_sigmapiu
        email: marco@example.invalid
        ...
    """
    raw_accounts, _ = _parse_config_yaml(Path(path))
    accounts = tuple(_account_from_mapping(item) for item in raw_accounts)
    if not accounts:
        raise MultiAccountConfigError("configuration must contain at least one account")
    aliases = [item.account_alias for item in accounts]
    if len(set(aliases)) != len(aliases):
        raise MultiAccountConfigError("account_alias values must be unique")
    return accounts


def load_storage_config(path: str | Path,
                        environ: Mapping[str, str] | None = None) -> LocalStorageConfig:
    _, raw_storage = _parse_config_yaml(Path(path))
    if raw_storage is None:
        raise MultiAccountConfigError("storage section is required in accounts.local.yaml")
    staging_dir = str(raw_storage.get("staging_dir", "")).strip()
    return LocalStorageConfig(
        adapter=str(raw_storage.get("adapter", "local_filesystem")),
        staging_dir=Path(staging_dir) if staging_dir else None,
        use_account_subfolders=_to_bool(raw_storage.get("use_account_subfolders", True)),
        copy_manifest=_to_bool(raw_storage.get("copy_manifest", True)),
        overwrite=_to_bool(raw_storage.get("overwrite", False)),
        create_staging_dir=_to_bool(raw_storage.get("create_staging_dir", False)),
    )


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
        ensure_state_db(self.paths.root)
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
                        store.add_audit_event(machine_id=load_machine_id(self.paths.root),
                            account_alias=account.account_alias, entity_type="message",
                            entity_id=message.message_id or message.message_uid,
                            fingerprint=None, action="message_scanned", status="detected")
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


class MultiAccountImapProcessor:
    """Downloads allowed attachments into per-account local quarantine only."""

    def __init__(self, accounts: Sequence[LocalImapAccount], *,
                 paths: LocalDataPaths | None = None,
                 environ: Mapping[str, str] | None = None,
                 mailbox_factory: Callable[[ImapReadonlyConfig, Path], object] | None = None,
                 policy: AttachmentPolicy | None = None,
                 scanner: LocalScanner | None = None,
                 rules: RuleSet | None = None,
                 max_attachment_bytes: int = 25 * 1024 * 1024) -> None:
        if max_attachment_bytes <= 0:
            raise ValueError("max_attachment_bytes must be positive")
        self.accounts = tuple(accounts)
        self.paths = paths or LocalDataPaths()
        self.environ = os.environ if environ is None else environ
        self.mailbox_factory = mailbox_factory or (
            lambda config, root: ImapReadonlyMailbox(config, root)
        )
        self.policy = policy or AttachmentPolicy()
        self.scanner = scanner or UnconfiguredScanner()
        self.rules = rules or RuleSet()
        self.max_attachment_bytes = max_attachment_bytes

    def process(self, *, dry_run: bool) -> tuple[MultiAccountAttachmentResult, ...]:
        ensure_state_db(self.paths.root)
        if not dry_run:
            self.paths.root.mkdir(parents=True, exist_ok=True)
            store = ReadonlyStateStore(self.paths.state_db)
            store.initialize()
        else:
            store = None
        results: list[MultiAccountAttachmentResult] = []
        for account in self.accounts:
            if not account.enabled:
                continue
            try:
                imap_config = account.to_imap_config(self.environ)
                account_root = self.paths.root / "accounts" / account.account_alias
                mailbox = self.mailbox_factory(imap_config, account_root / "quarantine")
                messages = tuple(mailbox.list_pending())
                run_id = store.start_run(account_alias=account.account_alias) if store else None
                attachments_seen = 0
                try:
                    for message in messages:
                        message_row_id = (store.add_message(run_id, message,
                                          account_alias=account.account_alias)
                                          if store and run_id is not None else None)
                        for attachment in mailbox.detect_attachments(message):
                            attachments_seen += 1
                            results.append(self._handle_attachment(
                                account, account_root, store, message_row_id,
                                message, attachment, dry_run=dry_run,
                            ))
                    if store and run_id is not None:
                        store.complete_run(run_id, messages_seen=len(messages),
                                           attachments_seen=attachments_seen)
                except Exception:
                    if store and run_id is not None:
                        store.complete_run(run_id, messages_seen=len(messages),
                                           attachments_seen=attachments_seen, status="error")
                    raise
            except Exception as exc:
                results.append(MultiAccountAttachmentResult(
                    account.account_alias, account.email, "", "", "", "", None, None,
                    "", 0, "", None, None, "error", False, error=str(exc),
                ))
        return tuple(results)

    def _handle_attachment(self, account: LocalImapAccount, account_root: Path,
                           store: ReadonlyStateStore | None, message_row_id: int | None,
                           message: MessageReference, attachment, *, dry_run: bool
                           ) -> MultiAccountAttachmentResult:
        payload = attachment.payload
        digest = hashlib.sha256(payload).hexdigest()
        sanitized = (sanitize_filename(attachment.original_filename)
                     if attachment.original_filename else None)
        attachment_id = _attachment_id(account.account_alias, message, attachment.ordinal)
        fingerprint = global_fingerprint(account.account_alias, message.message_id,
                                         message.message_uid, attachment_id, digest)
        included, rule_name, rule_reason = self.rules.decide(
            subject=message.subject, sender=message.sender,
            filename=attachment.original_filename, size_bytes=len(payload))
        status, reason = self._decision(attachment.original_filename, len(payload))
        if not included:
            status, reason = "rejected_by_extension", rule_reason
        scan_engine = None
        scan_result = None
        saved = False
        source_email = account.operational_email(self.environ)
        relative_path = None
        manifest_relative = None
        if dry_run:
            return self._result(account, message, attachment, attachment_id, sanitized,
                                digest, status, scan_engine, scan_result, False, None,
                                source_email=source_email,
                                fingerprint=fingerprint, included=included,
                                rule_name=rule_name, reason=reason)
        if store is None or message_row_id is None:
            raise RuntimeError("state store is required outside dry-run")
        existing = store.find_by_attachment_id(attachment_id)
        if existing:
            if str(existing["sha256"]) != digest:
                return self._result(account, message, attachment, attachment_id, sanitized,
                    digest, "error", None, None, False, None,
                    source_email=source_email,
                    error="attachment_id already exists with different sha256",
                    fingerprint=fingerprint)
            return self._result(account, message, attachment, attachment_id, sanitized,
                digest, str(existing["status"]), None, None, False,
                str(existing["manifest_path"]) if existing["manifest_path"] else None,
                source_email=source_email,
                fingerprint=fingerprint, rule_name=rule_name,
                reason="duplicate_seen")
        if status == "quarantined_unverified" and sanitized:
            quarantine = account_root / "quarantine"
            incoming = quarantine / "incoming" / sanitize_filename(message.message_uid)
            ready = quarantine / "ready" / sanitize_filename(message.message_uid)
            rejected = quarantine / "rejected" / sanitize_filename(message.message_uid)
            manifests = account_root / "manifests"
            incoming.mkdir(parents=True, exist_ok=True)
            manifests.mkdir(parents=True, exist_ok=True)
            target = incoming / f"{attachment.ordinal:03d}-{sanitized}"
            temporary = target.with_suffix(target.suffix + ".attachment.tmp")
            temporary.write_bytes(payload)
            temporary.replace(target)
            saved = True
            scan_path = target
            try:
                scan = self.scanner.scan(scan_path)
            except Exception as exc:
                scan = None
                scan_engine = type(self.scanner).__name__
                scan_result = "failed"
                status = "scan_failed"
                reason = f"scanner failed: {exc}"
            if scan and scan.verdict is ScanVerdict.CLEAN:
                scan_engine = scan.engine
                scan_result = scan.verdict.value
                reason = scan.detail
                status = "ready_for_caronte"
                ready.mkdir(parents=True, exist_ok=True)
                destination = ready / target.name
                scan_path.replace(destination)
                scan_path = destination
            elif scan and scan.verdict is ScanVerdict.INFECTED:
                scan_engine = scan.engine
                scan_result = scan.verdict.value
                reason = scan.detail
                status = "rejected_malware"
                rejected.mkdir(parents=True, exist_ok=True)
                destination = rejected / target.name
                scan_path.replace(destination)
                scan_path = destination
            elif scan and scan.verdict is ScanVerdict.UNVERIFIED:
                scan_engine = scan.engine
                scan_result = scan.verdict.value
                reason = scan.detail
                status = "quarantined_unverified"
            relative_path = scan_path.relative_to(self.paths.root).as_posix()
            manifest_path = manifests / f"{attachment_id}.manifest.json"
            manifest = self._manifest(account, message, attachment, attachment_id,
                sanitized, digest, status, scan_engine, scan_result, source_email,
                fingerprint, load_machine_id(self.paths.root), included, rule_name, reason)
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
            manifest_relative = manifest_path.relative_to(self.paths.root).as_posix()
        attachment_row_id = store.add_attachment(message_row_id, ordinal=attachment.ordinal,
            original_filename=attachment.original_filename, sanitized_filename=sanitized,
            declared_mime_type=attachment.declared_mime_type, size_bytes=len(payload),
            sha256=digest, status=status, relative_path=relative_path,
            duplicate_of_id=None, reason=reason, scanner_engine=scan_engine,
            scan_result=scan_result, account_alias=account.account_alias,
            attachment_id=attachment_id, source_email=source_email,
            manifest_path=manifest_relative)
        store.set_fingerprint(attachment_row_id, fingerprint)
        machine_id = load_machine_id(self.paths.root)
        action = "skipped" if not included else "attachment_quarantined"
        store.add_audit_event(machine_id=machine_id, account_alias=account.account_alias,
            entity_type="attachment", entity_id=attachment_id, fingerprint=fingerprint,
            action=action, status=status,
            details={"rule_name": rule_name, "reason": reason})
        return self._result(account, message, attachment, attachment_id, sanitized,
                            digest, status, scan_engine, scan_result, saved,
                            manifest_relative, source_email=source_email,
                            fingerprint=fingerprint, included=included,
                            rule_name=rule_name, reason=reason)

    def _decision(self, filename: str | None, size_bytes: int) -> tuple[str, str]:
        if size_bytes > self.max_attachment_bytes:
            return "rejected_by_size", "attachment exceeds configured size limit"
        if not filename:
            return "rejected_by_extension", "attachment has no filename"
        result = self.policy.evaluate_filename(filename)
        if result.decision is not PolicyDecision.ALLOW:
            return "rejected_by_extension", result.reason
        return "quarantined_unverified", "extension allowed; scanner evidence required"

    @staticmethod
    def _manifest(account: LocalImapAccount, message: MessageReference, attachment,
                  attachment_id: str, sanitized: str | None, digest: str,
                  status: str, scan_engine: str | None, scan_result: str | None,
                  source_email: str, fingerprint: str, machine_id: str,
                  included: bool, rule_name: str | None, reason: str
                  ) -> dict[str, object]:
        original_filename = attachment.original_filename or ""
        file_extension = Path(original_filename).suffix.casefold() if original_filename else ""
        return {
            "schema_version": "1.0",
            "connector_type": "local_imap",
            "account_alias": account.account_alias,
            "source_email": source_email,
            "source_sender": message.sender,
            "source_mailbox": message.mailbox,
            "source_message_uid": message.message_uid,
            "source_message_id": message.message_id,
            "source_message_date": message.date,
            "source_thread_id": message.thread_id,
            "subject": message.subject,
            "attachment_id": attachment_id,
            "original_filename": attachment.original_filename,
            "sanitized_filename": sanitized,
            "file_extension": file_extension,
            "sha256": digest,
            "size_bytes": len(attachment.payload),
            "mime_type": attachment.declared_mime_type,
            "scan_engine": scan_engine,
            "scan_result": scan_result,
            "quarantine_status": status,
            "policy_included": included,
            "policy_rule": rule_name,
            "status_reason": reason,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "fingerprint": fingerprint,
            "audit_trail": [
                audit_entry(machine_id, "attachment_quarantined", status,
                            account.account_alias, "attachment", attachment_id),
                audit_entry(machine_id, "attachment_scanned", scan_result or "unverified",
                            account.account_alias, "attachment", attachment_id),
                audit_entry(machine_id, "manifest_created", "created",
                            account.account_alias, "attachment", attachment_id),
            ],
        }

    @staticmethod
    def _result(account: LocalImapAccount, message: MessageReference, attachment,
                attachment_id: str, sanitized: str | None, digest: str, status: str,
                scan_engine: str | None, scan_result: str | None, saved: bool,
                manifest_path: str | None, source_email: str | None = None,
                error: str | None = None
                , fingerprint: str | None = None, included: bool = True,
                rule_name: str | None = None, reason: str | None = None
                ) -> MultiAccountAttachmentResult:
        return MultiAccountAttachmentResult(
            account.account_alias, source_email or account.email, message.message_uid,
            message.message_id, message.subject, attachment_id,
            attachment.original_filename, sanitized, digest, len(attachment.payload),
            attachment.declared_mime_type, scan_engine, scan_result, status, saved,
            manifest_path, error, fingerprint, included, rule_name, reason,
        )


def _attachment_id(account_alias: str, message: MessageReference, ordinal: int) -> str:
    uidvalidity = sanitize_filename(message.uidvalidity or "unknown")
    uid = sanitize_filename(message.message_uid)
    return f"{account_alias}-{uidvalidity}-{uid}-{ordinal}"


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
        ack_enabled=_to_bool(raw.get("ack_enabled", False)),
        ack_strategy=str(raw.get("ack_strategy", "no_ack_manual")),
    )


def _parse_config_yaml(path: Path) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    if not path.is_file():
        raise MultiAccountConfigError(f"configuration file not found: {path}")
    accounts: list[dict[str, object]] = []
    storage: dict[str, object] | None = None
    current: dict[str, object] | None = None
    section: str | None = None
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        is_top_level_section = not line[:1].isspace() and stripped.endswith(":")
        if is_top_level_section and stripped == "accounts:":
            if current is not None:
                accounts.append(current)
                current = None
            section = "accounts"
            continue
        if is_top_level_section and stripped == "storage:":
            if current is not None:
                accounts.append(current)
                current = None
            section = "storage"
            storage = {}
            continue
        if is_top_level_section:
            if current is not None:
                accounts.append(current)
                current = None
            section = "ignored"
            continue
        if section is None:
            raise MultiAccountConfigError(f"unsupported content before a section at line {line_number}")
        if section == "ignored":
            continue
        if section == "accounts" and stripped.startswith("- "):
            if current is not None:
                accounts.append(current)
            current = {}
            stripped = stripped[2:].strip()
            if stripped:
                key, value = _split_key_value(stripped, line_number)
                current[key] = _parse_scalar(value)
            continue
        if section == "storage":
            if storage is None:
                storage = {}
            key, value = _split_key_value(stripped, line_number)
            storage[key] = _parse_scalar(value)
            continue
        if current is None:
            raise MultiAccountConfigError(f"account item expected at line {line_number}")
        key, value = _split_key_value(stripped, line_number)
        current[key] = _parse_scalar(value)
    if current is not None:
        accounts.append(current)
    return accounts, storage


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


def _alias_from_email(email: str) -> str:
    local_part = email.split("@", 1)[0].strip().lower()
    alias = re.sub(r"[^a-z0-9]+", "_", local_part).strip("_")
    if len(alias) < 2:
        alias = "mailbox_locale"
    if not alias[0].isalnum():
        alias = f"a{alias}"
    return alias[:63]


def _env_name(alias: str, suffix: str) -> str:
    token = re.sub(r"[^A-Z0-9]+", "_", alias.upper()).strip("_")
    return f"VIRGILIO_IMAP_{token}_{suffix}"


def _quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _bool_text(value: bool) -> str:
    return "true" if value else "false"
