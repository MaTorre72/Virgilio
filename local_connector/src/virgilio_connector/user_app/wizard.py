"""First-run wizard views and local navigation for Caronte."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import PureWindowsPath
from typing import Any, Callable


class WizardStep(str, Enum):
    WELCOME = "welcome"
    LIMBO = "limbo"


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    message: str = ""


class WelcomeValidator:
    """The welcome step has no user data to validate."""

    def validate(self) -> ValidationResult:
        return ValidationResult(is_valid=True)


class LimboValidator:
    """Validate only the folder value entered in the Limbo step."""

    def validate(self, folder: str) -> ValidationResult:
        value = folder.strip()
        if not value:
            return ValidationResult(False, "Scegli la cartella Limbo.")
        if not PureWindowsPath(value).is_absolute():
            return ValidationResult(False, "Scegli un percorso completo.")
        return ValidationResult(True)


class WelcomeView:
    def __init__(
        self,
        parent: Any,
        *,
        ttk_module: Any,
        on_continue: Callable[[], None],
    ) -> None:
        self.frame = ttk_module.Frame(parent, padding=32)
        ttk_module.Label(self.frame, text="Benvenuto in Caronte").grid(
            row=0, column=0, sticky="w"
        )
        ttk_module.Label(
            self.frame,
            text="Ti accompagniamo nella configurazione iniziale.",
        ).grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk_module.Button(
            self.frame,
            text="Continua",
            command=on_continue,
        ).grid(row=2, column=0, sticky="e", pady=(24, 0))


class LimboView:
    def __init__(
        self,
        parent: Any,
        *,
        ttk_module: Any,
        on_back: Callable[[], None],
        on_continue: Callable[[], None],
    ) -> None:
        self.frame = ttk_module.Frame(parent, padding=32)
        ttk_module.Label(self.frame, text="Scegli la cartella Limbo").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk_module.Label(
            self.frame,
            text="Qui Caronte prepara i documenti da controllare.",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.folder_entry = ttk_module.Entry(self.frame)
        self.folder_entry.grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0)
        )
        self.message = ttk_module.Label(self.frame, text="")
        self.message.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk_module.Button(self.frame, text="Indietro", command=on_back).grid(
            row=4, column=0, sticky="w", pady=(24, 0)
        )
        ttk_module.Button(self.frame, text="Continua", command=on_continue).grid(
            row=4, column=1, sticky="e", pady=(24, 0)
        )

    def folder_value(self) -> str:
        return self.folder_entry.get()

    def show_validation(self, result: ValidationResult) -> None:
        self.message.configure(text=result.message)


class FirstRunController:
    """Replace wizard frames while keeping validation local to each step."""

    def __init__(self, parent: Any, *, ttk_module: Any) -> None:
        self.parent = parent
        self._ttk = ttk_module
        self.step = WizardStep.WELCOME
        self.current_view: WelcomeView | LimboView | None = None
        self._welcome_validator = WelcomeValidator()
        self._limbo_validator = LimboValidator()
        self._show_welcome()

    def continue_forward(self) -> ValidationResult:
        if self.step is WizardStep.WELCOME:
            result = self._welcome_validator.validate()
            if result.is_valid:
                self._show_limbo()
            return result

        assert isinstance(self.current_view, LimboView)
        result = self._limbo_validator.validate(self.current_view.folder_value())
        self.current_view.show_validation(result)
        return result

    def go_back(self) -> None:
        if self.step is WizardStep.LIMBO:
            self._show_welcome()

    def _replace(self, view: WelcomeView | LimboView, step: WizardStep) -> None:
        previous = self.current_view
        if previous is not None:
            previous.frame.destroy()
        self.current_view = view
        self.step = step
        view.frame.grid(row=0, column=0, sticky="nsew")

    def _show_welcome(self) -> None:
        view = WelcomeView(
            self.parent,
            ttk_module=self._ttk,
            on_continue=self.continue_forward,
        )
        self._replace(view, WizardStep.WELCOME)

    def _show_limbo(self) -> None:
        view = LimboView(
            self.parent,
            ttk_module=self._ttk,
            on_back=self.go_back,
            on_continue=self.continue_forward,
        )
        self._replace(view, WizardStep.LIMBO)
