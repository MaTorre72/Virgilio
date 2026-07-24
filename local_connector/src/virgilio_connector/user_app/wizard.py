"""First-run wizard views and local navigation for Caronte."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from ..application.account_connection import BackgroundAccountConnectionCheck
from ..application.account_management import AccountManagementService
from .demo import DemoState
from .text_controls import bind_text_interactions


class WizardStep(str, Enum):
    WELCOME = "welcome"
    LIMBO = "limbo"
    ACCOUNT = "account"
    SUMMARY = "summary"


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
        path = Path(value).expanduser()
        if not path.is_absolute():
            return ValidationResult(False, "Scegli un percorso completo.")
        if not path.is_dir():
            return ValidationResult(False, "Scegli una cartella esistente.")
        return ValidationResult(True)


@dataclass(frozen=True)
class AccountForm:
    name: str
    email: str
    password: str = field(repr=False)
    enabled: bool
    host: str = "imap.gmail.com"
    port: int = 993
    provider: str = "gmail_workspace"
    input_folder: str = "da-traghettare"
    done_folder: str = "traghettate"
    error_folder: str = "errore"


class AccountValidator:
    """Validate only values belonging to the mailbox step."""

    def validate(
        self, form: AccountForm, *, require_google_access: bool = True
    ) -> ValidationResult:
        if not form.name.strip():
            return ValidationResult(False, "Inserisci un nome per la casella.")
        if "@" not in form.email or not form.email.strip():
            return ValidationResult(False, "Inserisci un indirizzo email valido.")
        google_provider = (
            form.provider == "gmail_workspace"
            or form.host.strip().lower() == "imap.gmail.com"
        )
        if google_provider and require_google_access and not _is_google_authorization(form.password):
            return ValidationResult(False, "Collega con Google per aggiungere la casella.")
        if not google_provider and not form.password:
            return ValidationResult(False, "Inserisci la password della casella.")
        if not form.host.strip() or not 1 <= form.port <= 65535:
            return ValidationResult(False, "Controlla le impostazioni avanzate.")
        if not all((
            form.input_folder.strip(),
            form.done_folder.strip(),
            form.error_folder.strip(),
        )):
            return ValidationResult(False, "Indica le tre cartelle della casella.")
        return ValidationResult(True)


class WelcomeView:
    def __init__(
        self,
        parent: Any,
        *,
        ttk_module: Any,
        on_continue: Callable[[], None],
    ) -> None:
        self.frame = ttk_module.Frame(parent, padding=16)
        ttk_module.Label(self.frame, text="Benvenuto in Caronte").grid(
            row=0, column=0, sticky="w"
        )
        ttk_module.Label(
            self.frame,
            text="Prepariamo Caronte per ricevere i documenti da controllare.",
        ).grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk_module.Label(
            self.frame,
            text="Servono una cartella Limbo e almeno una casella.",
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk_module.Button(
            self.frame,
            text="Inizia la configurazione",
            command=on_continue,
        ).grid(row=3, column=0, sticky="w", pady=(24, 0))


class LimboView:
    def __init__(
        self,
        parent: Any,
        *,
        ttk_module: Any,
        on_back: Callable[[], None],
        on_continue: Callable[[], None],
        initial_folder: str = "",
        choose_folder: Callable[[], str] | None = None,
        menu_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.frame = ttk_module.Frame(parent, padding=16)
        ttk_module.Label(self.frame, text="Scegli la cartella Limbo").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk_module.Label(
            self.frame,
            text=(
                "Scegli sul computer la cartella del Limbo Drive sincronizzato. "
                "Qui Caronte prepara i documenti da controllare."
            ),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(12, 0))
        ttk_module.Label(
            self.frame,
            text="Cartella del Limbo",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(16, 0))
        self.folder_entry = ttk_module.Entry(self.frame)
        self.folder_entry.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        self.folder_entry.insert(0, initial_folder)
        bind_text_interactions(self.folder_entry, menu_factory=menu_factory)
        self._choose_folder = choose_folder or self._open_folder_dialog
        ttk_module.Button(
            self.frame, text="Scegli cartella...", command=self.select_folder
        ).grid(row=3, column=1, sticky="w", pady=(6, 0))
        self.message = ttk_module.Label(self.frame, text="")
        self.message.grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk_module.Button(self.frame, text="Indietro", command=on_back).grid(
            row=5, column=0, sticky="w", pady=(24, 0)
        )
        ttk_module.Button(self.frame, text="Continua", command=on_continue).grid(
            row=5, column=1, sticky="e", pady=(24, 0)
        )

    def folder_value(self) -> str:
        return self.folder_entry.get()

    @staticmethod
    def _open_folder_dialog() -> str:
        from tkinter import filedialog

        return filedialog.askdirectory(mustexist=True)

    def select_folder(self) -> None:
        selected = self._choose_folder()
        if selected:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, selected)

    def show_validation(self, result: ValidationResult) -> None:
        self.message.configure(text=result.message)


def _is_google_authorization(value: str) -> bool:
    try:
        payload = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return False
    return bool(
        isinstance(payload, dict)
        and payload.get("token")
        and payload.get("refresh_token")
    )


class AccountView:
    """Ordinary mailbox fields with optional provider details."""

    GOOGLE_FIELDS = ("Nome casella", "Email", "Casella attiva")
    GENERIC_FIELDS = ("Nome casella", "Email", "Password", "Casella attiva")

    def __init__(
        self,
        parent: Any,
        *,
        ttk_module: Any,
        on_back: Callable[[], None],
        on_continue: Callable[[], None],
        on_test: Callable[[], None],
        on_update: Callable[[], None],
        on_remove: Callable[[], None],
        on_select: Callable[[], None],
        menu_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._ttk = ttk_module
        self._menu_factory = menu_factory
        self._enabled = True
        self.provider = "gmail_workspace"
        self.advanced_visible = False
        self.frame = ttk_module.Frame(parent, padding=16)
        ttk_module.Label(self.frame, text="Configura le caselle").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk_module.Label(
            self.frame,
            text="Aggiungi la prima casella. Puoi aggiungere subito anche una seconda casella.",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.provider_hint = ttk_module.Label(
            self.frame,
            text=(
                "Scegli Google oppure Posta IMAP, inserisci i dati richiesti e collegala. "
                "Caronte la aggiungerà dopo la verifica."
            ),
        )
        self.provider_hint.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.table = ttk_module.Treeview(
            self.frame,
            columns=("name", "email", "provider", "status"),
            show="headings",
            height=5,
        )
        for column, heading in (
            ("name", "Nome casella"),
            ("email", "Email"),
            ("provider", "Provider"),
            ("status", "Stato"),
        ):
            self.table.heading(column, text=heading)
        self.table.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 4))
        self.name_entry = self._field(4, "Nome casella")
        self.name_entry.insert(0, "Principale")
        self.email_entry = self._field(5, "Email")
        self.password_label = ttk_module.Label(self.frame, text="Password")
        self.password_label.grid(row=6, column=0, sticky="w")
        self.password_entry = ttk_module.Entry(self.frame, show="*")
        bind_text_interactions(self.password_entry, menu_factory=menu_factory)
        self.password_entry.grid(row=6, column=1, sticky="ew")
        self.password_label.grid_remove()
        self.password_entry.grid_remove()
        self.enabled_control = ttk_module.Checkbutton(
            self.frame, text="Casella attiva", command=self.toggle_enabled
        )
        self.enabled_control.state(("selected",))
        self.enabled_control.grid(row=7, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.provider_button = ttk_module.Button(
            self.frame,
            text="Scegli Posta IMAP",
            command=self.use_generic_provider,
        )
        self.provider_button.grid(row=8, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.advanced_button = ttk_module.Button(
            self.frame,
            text="Mostra impostazioni avanzate",
            command=self.toggle_advanced,
        )
        self.advanced_button.grid(row=9, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.advanced_frame = ttk_module.Frame(self.frame)
        self.advanced_frame.grid(row=10, column=0, columnspan=2, sticky="ew")
        ttk_module.Label(
            self.advanced_frame, text="Server posta in arrivo"
        ).grid(row=0, column=0, sticky="w")
        self.host_entry = ttk_module.Entry(self.advanced_frame)
        bind_text_interactions(self.host_entry, menu_factory=menu_factory)
        self.host_entry.insert(0, "imap.gmail.com")
        self.host_entry.grid(row=0, column=1, sticky="ew")
        ttk_module.Label(self.advanced_frame, text="Porta").grid(
            row=1, column=0, sticky="w"
        )
        self.port_entry = ttk_module.Entry(self.advanced_frame)
        bind_text_interactions(self.port_entry, menu_factory=menu_factory)
        self.port_entry.insert(0, "993")
        self.port_entry.grid(row=1, column=1, sticky="ew")
        self.input_folder_entry = self._advanced_field(
            2, "Cartella da controllare", "da-traghettare"
        )
        self.done_folder_entry = self._advanced_field(
            3, "Cartella completati", "traghettate"
        )
        self.error_folder_entry = self._advanced_field(
            4, "Cartella problemi", "errore"
        )
        self.advanced_frame.grid_remove()
        self.message = ttk_module.Label(self.frame, text="")
        self.message.grid(row=11, column=0, columnspan=2, sticky="w", pady=(4, 0))
        actions = ttk_module.Frame(self.frame)
        actions.grid(row=12, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk_module.Button(actions, text="Modifica", command=on_update).grid(row=0, column=0)
        ttk_module.Button(actions, text="Rimuovi", command=on_remove).grid(row=0, column=1)
        self.access_button = ttk_module.Button(
            self.frame, text="Collega con Google", command=on_test
        )
        self.access_button.grid(row=13, column=0, sticky="w", pady=(12, 0))
        ttk_module.Button(self.frame, text="Indietro", command=on_back).grid(
            row=14, column=0, sticky="w", pady=(12, 0)
        )
        ttk_module.Button(self.frame, text="Completa configurazione", command=on_continue).grid(
            row=14, column=1, sticky="e", pady=(12, 0)
        )
        self.table.bind("<<TreeviewSelect>>", lambda _event: on_select())

    def _field(self, row: int, label: str, **entry_options: Any) -> Any:
        self._ttk.Label(self.frame, text=label).grid(row=row, column=0, sticky="w")
        entry = self._ttk.Entry(self.frame, **entry_options)
        bind_text_interactions(entry, menu_factory=self._menu_factory)
        entry.grid(row=row, column=1, sticky="ew")
        return entry

    def _advanced_field(self, row: int, label: str, initial: str) -> Any:
        self._ttk.Label(self.advanced_frame, text=label).grid(
            row=row, column=0, sticky="w"
        )
        entry = self._ttk.Entry(self.advanced_frame)
        bind_text_interactions(entry, menu_factory=self._menu_factory)
        entry.insert(0, initial)
        entry.grid(row=row, column=1, sticky="ew")
        return entry

    def visible_fields(self) -> tuple[str, ...]:
        return self.GOOGLE_FIELDS if self.provider == "gmail_workspace" else self.GENERIC_FIELDS

    def use_generic_provider(self) -> None:
        self.provider = "custom_imap"
        if self.host_entry.get().strip().lower() == "imap.gmail.com":
            self.host_entry.delete(0, "end")
        self.password_label.grid(row=6, column=0, sticky="w")
        self.password_entry.grid(row=6, column=1, sticky="ew")
        self.provider_button.configure(
            text="Usa Gmail o Workspace", command=self.use_google_provider
        )
        self.access_button.configure(text="Verifica e aggiungi")
        if not self.advanced_visible:
            self.toggle_advanced()

    def use_google_provider(self) -> None:
        self.provider = "gmail_workspace"
        self.host_entry.delete(0, "end")
        self.host_entry.insert(0, "imap.gmail.com")
        self.port_entry.delete(0, "end")
        self.port_entry.insert(0, "993")
        if not _is_google_authorization(self.password_entry.get()):
            self.password_entry.delete(0, "end")
        self.password_label.grid_remove()
        self.password_entry.grid_remove()
        self.provider_button.configure(
            text="Scegli Posta IMAP", command=self.use_generic_provider
        )
        self.access_button.configure(text="Collega con Google")
        if self.advanced_visible:
            self.toggle_advanced()

    def toggle_enabled(self) -> None:
        self._enabled = not self._enabled

    def populate(self, account: Any, password: str) -> None:
        """Show the persisted values of the selected mailbox for editing."""

        for entry, value in (
            (self.name_entry, account.name),
            (self.email_entry, account.email),
            (self.password_entry, password),
            (self.host_entry, account.host),
            (self.port_entry, str(account.port)),
            (self.input_folder_entry, account.input_folder),
            (self.done_folder_entry, account.done_folder),
            (self.error_folder_entry, account.error_folder),
        ):
            entry.delete(0, "end")
            entry.insert(0, value)
        self._enabled = account.enabled
        self.enabled_control.state(("selected" if account.enabled else "!selected",))
        if account.host == "imap.gmail.com":
            self.use_google_provider()
        else:
            self.use_generic_provider()

    def toggle_advanced(self) -> None:
        self.advanced_visible = not self.advanced_visible
        if self.advanced_visible:
            self.advanced_frame.grid(row=10, column=0, columnspan=2, sticky="ew")
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
            provider=self.provider,
            input_folder=self.input_folder_entry.get(),
            done_folder=self.done_folder_entry.get(),
            error_folder=self.error_folder_entry.get(),
        )

    def show_validation(self, result: ValidationResult) -> None:
        self.message.configure(text=result.message)

    def selected_alias(self) -> str | None:
        selected = self.table.selection()
        return selected[0] if selected else None

    def render_accounts(self, accounts: tuple[Any, ...]) -> None:
        for item in self.table.get_children():
            self.table.delete(item)
        for account in accounts:
            provider = "Gmail / Workspace" if account.host == "imap.gmail.com" else account.host
            self.table.insert(
                "", "end", iid=account.alias,
                values=(account.name, account.email, provider, "Attiva" if account.enabled else "Disattivata"),
            )


class SummaryView:
    """Review persisted setup details before the user opens Home."""

    def __init__(
        self, parent: Any, *, ttk_module: Any,
        on_back: Callable[[], None], on_continue: Callable[[], None],
        demo: DemoState | None = None,
        account_service: AccountManagementService | None = None,
    ) -> None:
        self.frame = ttk_module.Frame(parent, padding=16)
        ttk_module.Label(self.frame, text="Riepilogo").grid(row=0, column=0, sticky="w")
        ttk_module.Label(
            self.frame,
            text="Controlla i dati prima di aprire la Home.",
        ).grid(row=1, column=0, sticky="w", pady=(12, 0))
        if demo is not None:
            limbo_folder = demo.limbo_folder
            accounts = demo.accounts
        else:
            assert account_service is not None
            model = account_service.configuration.load()
            limbo_folder = str(model.storage.staging_dir)
            accounts = account_service.list_accounts()
        active_accounts = tuple(account for account in accounts if account.enabled)
        inactive_accounts = tuple(account for account in accounts if not account.enabled)
        ttk_module.Label(
            self.frame, text=f"Cartella Limbo: {limbo_folder}", wraplength=640
        ).grid(
            row=2, column=0, sticky="w", pady=(12, 0)
        )
        ttk_module.Label(
            self.frame,
            text=f"Caselle configurate: {len(accounts)} ({len(active_accounts)} attive)",
        ).grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk_module.Label(
            self.frame,
            text="Caselle: " + ", ".join(account.name for account in accounts),
            wraplength=640,
        ).grid(row=4, column=0, sticky="w", pady=(8, 0))
        correction = (
            "Caselle da attivare: " + ", ".join(account.name for account in inactive_accounts)
            if inactive_accounts
            else "Configurazione completa: tutte le caselle sono attive."
        )
        ttk_module.Label(self.frame, text=correction, wraplength=640).grid(
            row=5, column=0, sticky="w", pady=(8, 0)
        )
        ttk_module.Label(
            self.frame,
            text="Per cambiare un dato, scegli Indietro e correggilo nella schermata indicata.",
        ).grid(row=6, column=0, sticky="w", pady=(12, 0))
        ttk_module.Button(self.frame, text="Indietro", command=on_back).grid(
            row=7, column=0, sticky="w", pady=(24, 0)
        )
        ttk_module.Button(
            self.frame,
            text="Apri Home" if demo is not None else "Completa configurazione",
            command=on_continue,
        ).grid(
            row=7, column=1, sticky="e", pady=(24, 0)
        )


class FirstRunController:
    """Replace wizard frames while keeping validation local to each step."""

    def __init__(
        self,
        parent: Any,
        *,
        ttk_module: Any,
        readonly_test: Callable[[AccountForm], str] | None = None,
        google_access: Callable[[AccountForm], Any] | None = None,
        account_service: AccountManagementService | None = None,
        on_complete: Callable[[], None] | None = None,
        open_existing: bool = False,
        choose_folder: Callable[[], str] | None = None,
        menu_factory: Callable[..., Any] | None = None,
        demo: DemoState | None = None,
    ) -> None:
        self.parent = parent
        self._ttk = ttk_module
        self.step = WizardStep.WELCOME
        self.current_view: WelcomeView | LimboView | AccountView | SummaryView | None = None
        self._welcome_validator = WelcomeValidator()
        self._limbo_validator = LimboValidator()
        self._account_validator = AccountValidator()
        self._readonly_test = readonly_test
        self._google_access = google_access
        self._pending_google_credentials = ""
        self._save_after_connection = False
        self._connection_check = (
            BackgroundAccountConnectionCheck(self._check_connection)
            if readonly_test is not None
            else None
        )
        self._account_service = account_service
        self._on_complete = on_complete
        self._choose_folder = choose_folder
        self._menu_factory = menu_factory
        self._demo = demo
        self._limbo_folder = ""
        if open_existing and account_service is not None:
            self._limbo_folder = str(
                account_service.configuration.load().storage.staging_dir
            )
            self._show_account()
        else:
            self._show_welcome()

    def continue_forward(self) -> ValidationResult:
        if self.step is WizardStep.WELCOME:
            result = self._welcome_validator.validate()
            if result.is_valid:
                self._show_limbo()
            return result

        if self.step is WizardStep.LIMBO:
            assert isinstance(self.current_view, LimboView)
            if self._demo is not None:
                self._limbo_folder = self._demo.limbo_folder
                self._show_account()
                return ValidationResult(True)
            result = self._limbo_validator.validate(self.current_view.folder_value())
            self.current_view.show_validation(result)
            if result.is_valid:
                self._limbo_folder = self.current_view.folder_value()
                self._show_account()
            return result

        if self.step is WizardStep.SUMMARY:
            if self._on_complete is not None:
                self._on_complete()
            return ValidationResult(True, "Percorso dimostrativo completato.")

        assert isinstance(self.current_view, AccountView)
        if self._demo is not None:
            self._show_summary()
            return ValidationResult(True)
        if self._account_service is not None:
            if not self._account_service.list_accounts():
                result = ValidationResult(False, "Aggiungi almeno una casella.")
                self.current_view.show_validation(result)
                return result
            result = ValidationResult(True, "Configurazione pronta per il riepilogo.")
            self.current_view.show_validation(result)
            self._show_summary()
            return result
        result = self._account_validator.validate(self.current_view.form_value())
        self.current_view.show_validation(result)
        return result

    def add_account(self) -> ValidationResult:
        return self._save_account(update=False)

    def update_account(self) -> ValidationResult:
        return self._save_account(update=True)

    def remove_account(self) -> ValidationResult:
        assert isinstance(self.current_view, AccountView)
        alias = self.current_view.selected_alias()
        if self._account_service is None or alias is None:
            result = ValidationResult(False, "Seleziona una casella da rimuovere.")
        else:
            self._account_service.remove(alias)
            self.current_view.render_accounts(self._account_service.list_accounts())
            result = ValidationResult(True, "Casella rimossa.")
        self.current_view.show_validation(result)
        return result

    def _save_account(
        self, *, update: bool, success_message: str | None = None
    ) -> ValidationResult:
        assert isinstance(self.current_view, AccountView)
        form = self.current_view.form_value()
        result = self._account_validator.validate(form)
        alias = self.current_view.selected_alias() if update else None
        if result.is_valid and self._account_service is None:
            result = ValidationResult(False, "Salvataggio non disponibile.")
        elif result.is_valid and update and alias is None:
            result = ValidationResult(False, "Seleziona una casella da modificare.")
        elif result.is_valid and self._account_service is not None:
            try:
                if update:
                    self._account_service.update(
                        alias, email=form.email, password=form.password, host=form.host,
                        port=form.port, enabled=form.enabled,
                        input_folder=form.input_folder, done_folder=form.done_folder,
                        error_folder=form.error_folder,
                    )
                    message = success_message or "Casella modificata."
                else:
                    self._account_service.add(
                        name=form.name, email=form.email, password=form.password,
                        host=form.host, port=form.port, enabled=form.enabled,
                        limbo=Path(self._limbo_folder),
                        input_folder=form.input_folder, done_folder=form.done_folder,
                        error_folder=form.error_folder,
                    )
                    message = success_message or "Casella aggiunta."
                self.current_view.render_accounts(self._account_service.list_accounts())
                result = ValidationResult(True, message)
            except Exception:
                result = ValidationResult(
                    False,
                    "Casella non salvata. Riprova; se il problema continua, "
                    "chiudi e riapri Caronte.",
                )
        self.current_view.show_validation(result)
        return result

    def go_back(self) -> None:
        if self.step is WizardStep.LIMBO:
            self._show_welcome()
        elif self.step is WizardStep.ACCOUNT:
            self._show_limbo()
        elif self.step is WizardStep.SUMMARY:
            self._show_account()

    def test_account_connection(self) -> ValidationResult:
        return self._start_account_connection(save_after_success=False)

    def connect_and_add_account(self) -> ValidationResult:
        return self._start_account_connection(save_after_success=True)

    def _start_account_connection(
        self, *, save_after_success: bool
    ) -> ValidationResult:
        assert isinstance(self.current_view, AccountView)
        form = self.current_view.form_value()
        result = self._account_validator.validate(form, require_google_access=False)
        if result.is_valid:
            if self._connection_check is None:
                result = ValidationResult(False, "Verifica non disponibile.")
            elif not self._connection_check.start(form):
                result = ValidationResult(False, "Verifica già in corso. Attendi il risultato.")
            else:
                self._save_after_connection = save_after_success
                result = ValidationResult(
                    True,
                    "Collegamento e salvataggio in corso..."
                    if save_after_success
                    else "Verifica avviata per la casella selezionata.",
                )
                self._schedule_connection_poll()
        self.current_view.show_validation(result)
        return result

    def _check_connection(self, form: AccountForm) -> str:
        if self._readonly_test is None:
            raise RuntimeError("connection check unavailable")
        if form.provider != "gmail_workspace":
            return self._readonly_test(form)
        if self._google_access is None:
            return self._readonly_test(form)
        authorization = self._google_access(form)
        self._pending_google_credentials = authorization.credentials_json
        return self._readonly_test(replace(form, password=authorization.access_token))

    def poll_account_connection(self) -> ValidationResult | None:
        if self._connection_check is None:
            return None
        feedback = self._connection_check.poll()
        if feedback is None:
            return None
        result = ValidationResult(feedback.ok, feedback.message)
        if isinstance(self.current_view, AccountView):
            if feedback.ok and self._pending_google_credentials:
                self.current_view.password_entry.delete(0, "end")
                self.current_view.password_entry.insert(0, self._pending_google_credentials)
                self._pending_google_credentials = ""
            if feedback.ok and self._save_after_connection:
                message = (
                    "Casella collegata e aggiunta."
                    if self.current_view.provider == "gmail_workspace"
                    else "Casella verificata e aggiunta."
                )
                self._save_after_connection = False
                result = self._save_account(
                    update=False, success_message=message
                )
            elif not feedback.ok:
                self._save_after_connection = False
                self._pending_google_credentials = ""
            self.current_view.show_validation(result)
        return result

    def _schedule_connection_poll(self) -> None:
        after = getattr(self.parent, "after", None)
        if after is None:
            return

        def poll() -> None:
            if self.poll_account_connection() is None and self._connection_check.running:
                after(100, poll)

        after(100, poll)

    def load_selected_account(self) -> None:
        assert isinstance(self.current_view, AccountView)
        alias = self.current_view.selected_alias()
        if self._account_service is None or alias is None:
            return
        account, credentials = self._account_service.get_account(alias)
        self.current_view.populate(account, credentials.password)

    def _replace(
        self, view: WelcomeView | LimboView | AccountView | SummaryView, step: WizardStep
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
            initial_folder=(
                self._demo.limbo_folder if self._demo is not None else self._limbo_folder
            ),
            choose_folder=self._choose_folder,
            menu_factory=self._menu_factory,
        )
        self._replace(view, WizardStep.LIMBO)

    def _show_account(self) -> None:
        view = AccountView(
            self.parent,
            ttk_module=self._ttk,
            on_back=self.go_back,
            on_continue=self.continue_forward,
            on_test=self.connect_and_add_account,
            on_update=self.update_account,
            on_remove=self.remove_account,
            on_select=self.load_selected_account,
            menu_factory=self._menu_factory,
        )
        if self._demo is not None:
            view.render_accounts(self._demo.accounts)
        elif self._account_service is not None:
            view.render_accounts(self._account_service.list_accounts())
        self._replace(view, WizardStep.ACCOUNT)

    def _show_summary(self) -> None:
        self._replace(
            SummaryView(
                self.parent,
                ttk_module=self._ttk,
                demo=self._demo,
                account_service=self._account_service,
                on_back=self.go_back,
                on_continue=self.continue_forward,
            ), WizardStep.SUMMARY,
        )
