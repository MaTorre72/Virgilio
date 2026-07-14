"""First-run wizard services shared by the local GUI."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from .gui_config import GuiConfigService, LocalCredentials
from .multi_account import MultiAccountConfigError, scaffold_local_config


WIZARD_STEPS = ("Cartelle", "Caselle", "Registro condiviso", "Verifica finale")


@dataclass(frozen=True, slots=True)
class WizardAccount:
    alias: str
    email: str
    username: str = ""
    password: str = ""
    provider: str = "gmail_workspace"
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    input_folder: str = "Virgilio/da-traghettare"
    done_folder: str = "Virgilio/traghettate"
    error_folder: str = "Virgilio/errore"


@dataclass(frozen=True, slots=True)
class WizardDraft:
    staging_dir: Path | None = None
    accounts: tuple[WizardAccount, ...] = ()
    bucoliche_enabled: bool = False


class FirstRunWizard:
    """Navigation and persistence for a reopenable, network-free setup wizard."""

    def __init__(self, service: GuiConfigService, *, draft: WizardDraft | None = None,
                 verifier: Callable[[WizardDraft], tuple[str, ...]] | None = None) -> None:
        self.service = service
        self.draft = draft or self._load_existing()
        self.step_index = 0
        self.verifier = verifier or self._verify_local

    @property
    def step(self) -> str:
        return WIZARD_STEPS[self.step_index]

    @property
    def first_run(self) -> bool:
        return not self.service.yaml_path.exists()

    def set_folders(self, staging_dir: Path) -> None:
        path = Path(staging_dir)
        if not path.is_absolute():
            raise MultiAccountConfigError("Scegli una cartella completa sul computer.")
        self.draft = replace(self.draft, staging_dir=path)

    def set_accounts(self, accounts: tuple[WizardAccount, ...]) -> None:
        if not accounts:
            raise MultiAccountConfigError("Inserisci almeno una casella mail.")
        aliases = [item.alias for item in accounts]
        if len(set(aliases)) != len(aliases):
            raise MultiAccountConfigError("Ogni casella deve avere un nome diverso.")
        self.draft = replace(self.draft, accounts=accounts)

    def set_bucoliche(self, enabled: bool) -> None:
        self.draft = replace(self.draft, bucoliche_enabled=bool(enabled))

    def next(self) -> str:
        self._validate_step(self.step_index)
        self.step_index = min(self.step_index + 1, len(WIZARD_STEPS) - 1)
        return self.step

    def back(self) -> str:
        self.step_index = max(self.step_index - 1, 0)
        return self.step

    def problems(self) -> tuple[str, ...]:
        problems: list[str] = []
        for index in range(3):
            try:
                self._validate_step(index)
            except MultiAccountConfigError as exc:
                problems.append(str(exc))
        problems.extend(self.verifier(self.draft))
        return tuple(dict.fromkeys(problems))

    def save(self) -> None:
        problems = self.problems()
        if problems:
            raise MultiAccountConfigError("; ".join(problems))
        assert self.draft.staging_dir is not None
        first = self.draft.accounts[0]
        text = scaffold_local_config(
            email=first.email, staging_dir=self.draft.staging_dir,
            account_alias=first.alias, provider_hint=first.provider,
            imap_host=first.imap_host, imap_port=first.imap_port,
            input_folder=first.input_folder, done_folder=first.done_folder,
            error_folder=first.error_folder, bucoliche_enabled=self.draft.bucoliche_enabled,
        )
        self.service.yaml_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.service.yaml_path.with_suffix(".wizard.tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(self.service.yaml_path)
        model = self.service.load()
        model = model.update_account(first.alias, model.accounts[0],
                                     LocalCredentials(first.username, first.password))
        for item in self.draft.accounts[1:]:
            account = self.service.new_account(
                account_alias=item.alias, email=item.email, provider_hint=item.provider,
                imap_host=item.imap_host, imap_port=item.imap_port,
                input_folder=item.input_folder, done_folder=item.done_folder,
                error_folder=item.error_folder,
            )
            model = model.create_account(account, LocalCredentials(item.username, item.password))
        self.service.save(model)

    def _validate_step(self, index: int) -> None:
        if index == 0:
            if self.draft.staging_dir is None:
                raise MultiAccountConfigError("Scegli la cartella Limbo.")
            if not self.draft.staging_dir.is_absolute():
                raise MultiAccountConfigError("La cartella Limbo deve avere un percorso completo.")
        elif index == 1:
            if not self.draft.accounts:
                raise MultiAccountConfigError("Inserisci almeno una casella mail.")
            for item in self.draft.accounts:
                self.service.new_account(
                    account_alias=item.alias, email=item.email, provider_hint=item.provider,
                    imap_host=item.imap_host, imap_port=item.imap_port,
                    input_folder=item.input_folder, done_folder=item.done_folder,
                    error_folder=item.error_folder,
                )

    def _load_existing(self) -> WizardDraft:
        if not self.service.yaml_path.exists():
            return WizardDraft()
        model = self.service.load()
        accounts = tuple(WizardAccount(
            alias=item.account_alias, email=item.email,
            username=model.credentials[item.account_alias].username,
            password=model.credentials[item.account_alias].password,
            provider=item.provider_hint, imap_host=item.imap_host, imap_port=item.imap_port,
            input_folder=item.input_folder, done_folder=item.done_folder,
            error_folder=item.error_folder,
        ) for item in model.accounts)
        text = self.service.yaml_path.read_text(encoding="utf-8")
        bucoliche_enabled = "bucoliche:\n  enabled: true" in text
        return WizardDraft(model.storage.staging_dir, accounts, bucoliche_enabled)

    @staticmethod
    def _verify_local(draft: WizardDraft) -> tuple[str, ...]:
        if draft.staging_dir is not None and draft.staging_dir.exists() \
                and not draft.staging_dir.is_dir():
            return ("La cartella Limbo scelta non e una cartella.",)
        return ()
