"""First-run wizard views and local navigation for Caronte."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import PureWindowsPath
from typing import Any, Callable


class WizardStep(str, Enum):
    WELCOME = "welcome"
    LIMBO = "limbo"
    ACCOUNT = "account"


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


@dataclass(frozen=True)
class AccountForm:
    name: str
    email: str
    password: str
    enabled: bool
    host: str = "imap.gmail.com"
    port: int = 993


class AccountValidator:
    """Validate only values belonging to the mailbox step."""

    def validate(self, form: AccountForm) -> ValidationResult:
        if not form.name.strip():
            return ValidationResult(False, "Inserisci un nome per la casella.")
        if "@" not in form.email or not form.email.strip():
            return ValidationResult(False, "Inserisci un indirizzo email valido.")
        if not form.password:
            return ValidationResult(False, "Inserisci la password della casella.")
        if not form.host.strip() or not 1 <= form.port <= 65535:
            return ValidationResult(False, "Controlla le impostazioni avanzate.")
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


class AccountView:
    """Ordinary mailbox fields with optional provider details."""

    ORDINARY_FIELDS = ("Nome casella", "Email", "Password", "Casella attiva")

    def __init__(
        self,
        parent: Any,
        *,
        ttk_module: Any,
        on_back: Callable[[], None],
        on_continue: Callable[[], None],
        on_test: Callable[[], None],
    ) -> None:
        self._ttk = ttk_module
        self._enabled = True
        self.advanced_visible = False
        self.frame = ttk_module.Frame(parent, padding=32)
        ttk_module.Label(self.frame, text="Configura la casella").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        self.name_entry = self._field(1, "Nome casella")
        self.name_entry.insert(0, "Principale")
        self.email_entry = self._field(2, "Email")
        self.password_entry = self._field(3, "Password", show="*")
        self.enabled_control = ttk_module.Checkbutton(
            self.frame, text="Casella attiva", command=self.toggle_enabled
        )
        self.enabled_control.grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.advanced_button = ttk_module.Button(
            self.frame,
            text="Mostra impostazioni avanzate",
            command=self.toggle_advanced,
        )
        self.advanced_button.grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.advanced_frame = ttk_module.Frame(self.frame)
        self.advanced_frame.grid(row=6, column=0, columnspan=2, sticky="ew")
        ttk_module.Label(
            self.advanced_frame, text="Server posta in arrivo"
        ).grid(row=0, column=0, sticky="w")
        self.host_entry = ttk_module.Entry(self.advanced_frame)
        self.host_entry.insert(0, "imap.gmail.com")
        self.host_entry.grid(row=0, column=1, sticky="ew")
        ttk_module.Label(self.advanced_frame, text="Porta").grid(
            row=1, column=0, sticky="w"
        )
        self.port_entry = ttk_module.Entry(self.advanced_frame)
        self.port_entry.insert(0, "993")
        self.port_entry.grid(row=1, column=1, sticky="ew")
        self.advanced_frame.grid_remove()
        self.message = ttk_module.Label(self.frame, text="")
        self.message.grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk_module.Button(
            self.frame, text="Verifica collegamento", command=on_test
        ).grid(row=8, column=0, sticky="w", pady=(24, 0))
        ttk_module.Button(self.frame, text="Indietro", command=on_back).grid(
            row=9, column=0, sticky="w", pady=(24, 0)
        )
        ttk_module.Button(self.frame, text="Continua", command=on_continue).grid(
            row=9, column=1, sticky="e", pady=(24, 0)
        )

    def _field(self, row: int, label: str, **entry_options: Any) -> Any:
        self._ttk.Label(self.frame, text=label).grid(row=row, column=0, sticky="w")
        entry = self._ttk.Entry(self.frame, **entry_options)
        entry.grid(row=row, column=1, sticky="ew")
        return entry

    def visible_fields(self) -> tuple[str, ...]:
        return self.ORDINARY_FIELDS

    def toggle_enabled(self) -> None:
        self._enabled = not self._enabled

    def toggle_advanced(self) -> None:
        self.advanced_visible = not self.advanced_visible
        if self.advanced_visible:
            self.advanced_frame.grid(row=6, column=0, columnspan=2, sticky="ew")
            self.advanced_button.configure(text="Nascondi impostazioni avanzate")
        else:
            self.advanced_frame.grid_remove()
            self.advanced_button.configure(text="Mostra impostazioni avanzate")

    def form_value(self) -> AccountForm:
        try:
            port = int(self.port_entry.get())
        except (TypeError, ValueError):
            port = 0
        return AccountForm(
            name=self.name_entry.get(),
            email=self.email_entry.get(),
            password=self.password_entry.get(),
            enabled=self._enabled,
            host=self.host_entry.get(),
            port=port,
        )

    def show_validation(self, result: ValidationResult) -> None:
        self.message.configure(text=result.message)


class FirstRunController:
    """Replace wizard frames while keeping validation local to each step."""

    def __init__(
        self,
        parent: Any,
        *,
        ttk_module: Any,
        readonly_test: Callable[[AccountForm], str] | None = None,
    ) -> None:
        self.parent = parent
        self._ttk = ttk_module
        self.step = WizardStep.WELCOME
        self.current_view: WelcomeView | LimboView | AccountView | None = None
        self._welcome_validator = WelcomeValidator()
        self._limbo_validator = LimboValidator()
        self._account_validator = AccountValidator()
        self._readonly_test = readonly_test
        self._show_welcome()

    def continue_forward(self) -> ValidationResult:
        if self.step is WizardStep.WELCOME:
            result = self._welcome_validator.validate()
            if result.is_valid:
                self._show_limbo()
            return result

        if self.step is WizardStep.LIMBO:
            assert isinstance(self.current_view, LimboView)
            result = self._limbo_validator.validate(self.current_view.folder_value())
            self.current_view.show_validation(result)
            if result.is_valid:
                self._show_account()
            return result

        assert isinstance(self.current_view, AccountView)
        result = self._account_validator.validate(self.current_view.form_value())
        self.current_view.show_validation(result)
        return result

    def go_back(self) -> None:
        if self.step is WizardStep.LIMBO:
            self._show_welcome()
        elif self.step is WizardStep.ACCOUNT:
            self._show_limbo()

    def test_account_connection(self) -> ValidationResult:
        assert isinstance(self.current_view, AccountView)
        form = self.current_view.form_value()
        result = self._account_validator.validate(form)
        if result.is_valid:
            if self._readonly_test is None:
                result = ValidationResult(False, "Verifica non disponibile.")
            else:
                result = ValidationResult(True, self._readonly_test(form))
        self.current_view.show_validation(result)
        return result

    def _replace(
        self, view: WelcomeView | LimboView | AccountView, step: WizardStep
    ) -> None:
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

    def _show_account(self) -> None:
        view = AccountView(
            self.parent,
            ttk_module=self._ttk,
            on_back=self.go_back,
            on_continue=self.continue_forward,
            on_test=self.test_account_connection,
        )
        self._replace(view, WizardStep.ACCOUNT)
