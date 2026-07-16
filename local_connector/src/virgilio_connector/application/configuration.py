"""Toolkit-independent structural configuration service."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import tempfile
from typing import Mapping, Protocol

from ..application_paths import ApplicationPaths
from ..multi_account import (
    LocalImapAccount,
    LocalStorageConfig,
    MultiAccountConfigError,
    load_multi_account_config,
    load_storage_config,
)


@dataclass(frozen=True, slots=True)
class UserPreferences:
    """Ordinary user preferences shared by every presentation."""

    interval_seconds: int = 300
    start_with_windows: bool = False
    minimize_on_close: bool = False

    def validate(self) -> None:
        if not 60 <= self.interval_seconds <= 86_400:
            raise MultiAccountConfigError(
                "preferences.interval_seconds must be between 60 and 86400"
            )


@dataclass(frozen=True, slots=True)
class ConfigurationModel:
    """The complete structural configuration used by every consumer."""

    accounts: tuple[LocalImapAccount, ...]
    storage: LocalStorageConfig
    preferences: UserPreferences = field(default_factory=UserPreferences)

    def validate(self) -> None:
        self.preferences.validate()
        if not self.accounts:
            raise MultiAccountConfigError("configuration must contain at least one account")
        aliases = [account.account_alias for account in self.accounts]
        if len(set(aliases)) != len(aliases):
            raise MultiAccountConfigError("account_alias values must be unique")
        environment_names = [
            name
            for account in self.accounts
            for name in (account.username_env, account.password_env)
        ]
        if len(set(environment_names)) != len(environment_names):
            raise MultiAccountConfigError(
                "credential environment variable names must be unique"
            )


class ConfigurationStore(Protocol):
    """Persistence port for structural configuration."""

    @property
    def source(self) -> Path: ...

    def load(self) -> ConfigurationModel: ...

    def save(self, model: ConfigurationModel) -> None: ...


class YamlConfigurationStore:
    """Local YAML adapter preserving sections owned by other services."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    @property
    def source(self) -> Path:
        return self.path

    def load(self) -> ConfigurationModel:
        model = ConfigurationModel(
            accounts=load_multi_account_config(self.path),
            storage=load_storage_config(self.path),
            preferences=_load_preferences(self.path),
        )
        model.validate()
        return model

    def save(self, model: ConfigurationModel) -> None:
        model.validate()
        text = _render_yaml(model, _unmanaged_yaml_suffix(self.path))
        _atomic_text_write(self.path, text)


class ConfigurationService:
    """Single entry point for structural configuration use cases."""

    def __init__(self, store: ConfigurationStore) -> None:
        self.store = store

    @classmethod
    def for_file(cls, path: Path) -> "ConfigurationService":
        return cls(YamlConfigurationStore(path))

    @classmethod
    def from_paths(cls, paths: ApplicationPaths) -> "ConfigurationService":
        return cls.for_file(paths.configuration_file)

    def exists(self) -> bool:
        return self.store.source.is_file()

    def load(self) -> ConfigurationModel:
        return self.store.load()

    def validate(self, model: ConfigurationModel) -> None:
        model.validate()

    def save(self, model: ConfigurationModel) -> None:
        model.validate()
        self.store.save(model)

    def field_sources(self) -> Mapping[str, Path]:
        """Document the authoritative source for every structural field group."""

        return {
            "accounts.*": self.store.source,
            "storage.*": self.store.source,
            "preferences.*": self.store.source,
        }


def _render_yaml(model: ConfigurationModel, suffix: str) -> str:
    lines = ["accounts:"]
    for account in model.accounts:
        fields = (
            ("account_alias", account.account_alias),
            ("email", account.email),
            ("provider_hint", account.provider_hint),
            ("imap_host", account.imap_host),
            ("imap_port", account.imap_port),
            ("username_env", account.username_env),
            ("password_env", account.password_env),
            ("input_folder", account.input_folder),
            ("done_folder", account.done_folder),
            ("error_folder", account.error_folder),
            ("enabled", account.enabled),
            ("max_messages", account.max_messages),
            ("ack_enabled", account.ack_enabled),
            ("ack_strategy", account.ack_strategy),
        )
        for index, (key, value) in enumerate(fields):
            prefix = "  - " if index == 0 else "    "
            lines.append(f"{prefix}{key}: {_yaml_scalar(value)}")
    storage = model.storage
    lines.extend((
        "storage:",
        f"  adapter: {_yaml_scalar(storage.adapter)}",
        f"  staging_dir: {_yaml_scalar(str(storage.staging_dir))}",
        f"  use_account_subfolders: {_yaml_scalar(storage.use_account_subfolders)}",
        f"  copy_manifest: {_yaml_scalar(storage.copy_manifest)}",
        f"  overwrite: {_yaml_scalar(storage.overwrite)}",
        f"  create_staging_dir: {_yaml_scalar(storage.create_staging_dir)}",
        "preferences:",
        f"  interval_seconds: {_yaml_scalar(model.preferences.interval_seconds)}",
        f"  start_with_windows: {_yaml_scalar(model.preferences.start_with_windows)}",
        f"  minimize_on_close: {_yaml_scalar(model.preferences.minimize_on_close)}",
    ))
    return "\n".join(lines) + "\n" + suffix


def _unmanaged_yaml_suffix(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"(?m)^(?!accounts:|storage:|preferences:)[A-Za-z][A-Za-z0-9_-]*:\s*$",
        text,
    )
    return text[match.start():] if match else ""


def _load_preferences(path: Path) -> UserPreferences:
    values: dict[str, object] = {}
    in_preferences = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line[:1].isspace() and line.strip().endswith(":"):
            in_preferences = line.strip() == "preferences:"
            continue
        if not in_preferences:
            continue
        text = line.strip()
        if ":" not in text:
            raise MultiAccountConfigError("invalid preferences entry")
        key, raw_value = (part.strip() for part in text.split(":", 1))
        if key == "interval_seconds":
            try:
                values[key] = int(raw_value)
            except ValueError as exc:
                raise MultiAccountConfigError(
                    "preferences.interval_seconds must be an integer"
                ) from exc
        elif key in {"start_with_windows", "minimize_on_close"}:
            if raw_value.lower() not in {"true", "false"}:
                raise MultiAccountConfigError(f"preferences.{key} must be true or false")
            values[key] = raw_value.lower() == "true"
    preferences = UserPreferences(**values)
    preferences.validate()
    return preferences


def _atomic_text_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        temporary.write_text(text, encoding="utf-8", newline="\n")
        temporary.replace(path)
    except Exception as exc:
        raise MultiAccountConfigError(
            "configuration save failed; previous file preserved"
        ) from exc
    finally:
        temporary.unlink(missing_ok=True)


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    import json
    return json.dumps(str(value), ensure_ascii=False)
