"""Application service for coordinated local GUI configuration."""

from __future__ import annotations

from dataclasses import dataclass, replace
import os
from pathlib import Path
import re
import tempfile
from typing import Mapping, Sequence

from .multi_account import (
    LocalImapAccount,
    LocalStorageConfig,
    MultiAccountConfigError,
    _env_name,
    load_multi_account_config,
    load_storage_config,
)


@dataclass(frozen=True, slots=True)
class LocalCredentials:
    username: str = ""
    password: str = ""


@dataclass(frozen=True, slots=True)
class GuiConfigModel:
    accounts: tuple[LocalImapAccount, ...]
    storage: LocalStorageConfig
    credentials: Mapping[str, LocalCredentials]

    def validate(self) -> None:
        if not self.accounts:
            raise MultiAccountConfigError("configuration must contain at least one account")
        aliases = [account.account_alias for account in self.accounts]
        if len(set(aliases)) != len(aliases):
            raise MultiAccountConfigError("account_alias values must be unique")
        env_names: list[str] = []
        for account in self.accounts:
            env_names.extend((account.username_env, account.password_env))
        if len(set(env_names)) != len(env_names):
            raise MultiAccountConfigError("credential environment variable names must be unique")

    def create_account(self, account: LocalImapAccount,
                       credentials: LocalCredentials | None = None) -> "GuiConfigModel":
        return self._with_accounts((*self.accounts, account), account.account_alias, credentials)

    def update_account(self, alias: str, account: LocalImapAccount,
                       credentials: LocalCredentials | None = None) -> "GuiConfigModel":
        if alias not in {item.account_alias for item in self.accounts}:
            raise MultiAccountConfigError(f"account not found: {alias}")
        updated = tuple(account if item.account_alias == alias else item for item in self.accounts)
        values = dict(self.credentials)
        previous = values.pop(alias, LocalCredentials())
        values[account.account_alias] = credentials if credentials is not None else previous
        model = replace(self, accounts=updated, credentials=values)
        model.validate()
        return model

    def remove_account(self, alias: str) -> "GuiConfigModel":
        if alias not in {item.account_alias for item in self.accounts}:
            raise MultiAccountConfigError(f"account not found: {alias}")
        values = dict(self.credentials)
        values.pop(alias, None)
        model = replace(self, accounts=tuple(item for item in self.accounts
                                             if item.account_alias != alias), credentials=values)
        model.validate()
        return model

    def _with_accounts(self, accounts: Sequence[LocalImapAccount], alias: str,
                       credentials: LocalCredentials | None) -> "GuiConfigModel":
        values = dict(self.credentials)
        values[alias] = credentials or LocalCredentials()
        model = replace(self, accounts=tuple(accounts), credentials=values)
        model.validate()
        return model


class GuiConfigService:
    """Loads and atomically saves the YAML structure and ignored local values file."""

    def __init__(self, yaml_path: Path, local_values_path: Path) -> None:
        self.yaml_path = Path(yaml_path)
        self.local_values_path = Path(local_values_path)

    def load(self) -> GuiConfigModel:
        accounts = load_multi_account_config(self.yaml_path)
        storage = load_storage_config(self.yaml_path)
        values = _read_local_values(self.local_values_path)
        credentials = {
            account.account_alias: LocalCredentials(
                values.get(account.username_env, ""), values.get(account.password_env, "")
            ) for account in accounts
        }
        model = GuiConfigModel(accounts, storage, credentials)
        model.validate()
        return model

    def save(self, model: GuiConfigModel) -> None:
        model.validate()
        yaml_text = _render_yaml(model, _unmanaged_yaml_suffix(self.yaml_path))
        previous_values = _read_local_values(self.local_values_path)
        managed = {name for account in model.accounts
                   for name in (account.username_env, account.password_env)}
        retained = {key: value for key, value in previous_values.items()
                    if not key.startswith("VIRGILIO_IMAP_") or key in managed}
        for account in model.accounts:
            credential = model.credentials.get(account.account_alias, LocalCredentials())
            retained[account.username_env] = credential.username
            retained[account.password_env] = credential.password
        local_text = "".join(f"{key}={_env_escape(value)}\n" for key, value in sorted(retained.items()))
        _atomic_pair_write(self.yaml_path, yaml_text, self.local_values_path, local_text)

    @staticmethod
    def new_account(*, account_alias: str, email: str, provider_hint: str,
                    imap_host: str, imap_port: int, input_folder: str,
                    done_folder: str, error_folder: str, enabled: bool = True) -> LocalImapAccount:
        return LocalImapAccount(
            account_alias=account_alias, email=email, provider_hint=provider_hint,
            imap_host=imap_host, imap_port=imap_port,
            username_env=_env_name(account_alias, "USERNAME"),
            password_env=_env_name(account_alias, "PASSWORD"),
            input_folder=input_folder, done_folder=done_folder, error_folder=error_folder,
            enabled=enabled,
        )


def _render_yaml(model: GuiConfigModel, suffix: str) -> str:
    lines = ["accounts:"]
    for account in model.accounts:
        fields = (
            ("account_alias", account.account_alias), ("email", account.email),
            ("provider_hint", account.provider_hint), ("imap_host", account.imap_host),
            ("imap_port", account.imap_port), ("username_env", account.username_env),
            ("password_env", account.password_env), ("input_folder", account.input_folder),
            ("done_folder", account.done_folder), ("error_folder", account.error_folder),
            ("enabled", account.enabled), ("max_messages", account.max_messages),
            ("ack_enabled", account.ack_enabled), ("ack_strategy", account.ack_strategy),
        )
        for index, (key, value) in enumerate(fields):
            prefix = "  - " if index == 0 else "    "
            lines.append(f"{prefix}{key}: {_yaml_scalar(value)}")
    storage = model.storage
    lines.extend(("storage:", f"  adapter: {_yaml_scalar(storage.adapter)}",
                  f"  staging_dir: {_yaml_scalar(str(storage.staging_dir))}",
                  f"  use_account_subfolders: {_yaml_scalar(storage.use_account_subfolders)}",
                  f"  copy_manifest: {_yaml_scalar(storage.copy_manifest)}",
                  f"  overwrite: {_yaml_scalar(storage.overwrite)}",
                  f"  create_staging_dir: {_yaml_scalar(storage.create_staging_dir)}"))
    return "\n".join(lines) + "\n" + suffix


def _unmanaged_yaml_suffix(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"(?m)^(?!accounts:|storage:)[A-Za-z][A-Za-z0-9_-]*:\s*$", text)
    return text[match.start():] if match else ""


def _read_local_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = _env_unescape(value.strip())
    return result


def _atomic_pair_write(first: Path, first_text: str, second: Path, second_text: str) -> None:
    originals = {path: path.read_bytes() if path.exists() else None for path in (first, second)}
    temporary: list[Path] = []
    try:
        for path, content in ((first, first_text), (second, second_text)):
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
            os.close(fd)
            temp = Path(name)
            temp.write_text(content, encoding="utf-8")
            temporary.append(temp)
        temporary[0].replace(first)
        temporary[1].replace(second)
    except Exception as exc:
        for path, content in originals.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(content)
        raise MultiAccountConfigError("configuration save failed; previous values restored") from exc
    finally:
        for path in temporary:
            path.unlink(missing_ok=True)


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    import json
    return json.dumps(str(value), ensure_ascii=False)


def _env_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n")


def _env_unescape(value: str) -> str:
    return value.replace("\\n", "\n").replace("\\\\", "\\")
