"""Toolkit-independent structural configuration service."""

from __future__ import annotations

from dataclasses import dataclass
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
class ConfigurationModel:
    """The complete structural configuration used by every consumer."""

    accounts: tuple[LocalImapAccount, ...]
    storage: LocalStorageConfig

    def validate(self) -> None:
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

        return {"accounts.*": self.store.source, "storage.*": self.store.source}


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
    ))
    return "\n".join(lines) + "\n" + suffix


def _unmanaged_yaml_suffix(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"(?m)^(?!accounts:|storage:)[A-Za-z][A-Za-z0-9_-]*:\s*$", text)
    return text[match.start():] if match else ""


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
