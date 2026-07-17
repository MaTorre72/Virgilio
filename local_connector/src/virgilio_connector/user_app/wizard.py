"""First-run wizard views and local navigation for Caronte."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from ..application.account_connection import BackgroundAccountConnectionCheck
from ..application.account_management import AccountManagementService
from .text_controls import bind_text_interactions


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
        initial_folder: str = "",
        choose_folder: Callable[[], str] | None = None,
        menu_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.frame = ttk_module.Frame(parent, padding=32)
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
        self.folder_entry = ttk_module.Entry(self.frame)
        self.folder_entry.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        self.folder_entry.insert(0, initial_folder)
        bind_text_interactions(self.folder_entry, menu_factory=menu_factory)
        self._choose_folder = choose_folder or self._open_folder_dialog
        ttk_module.Button(
            self.frame, text="Scegli cartella...", command=self.select_folder
        ).grid(row=2, column=1, sticky="w", pady=(16, 0))
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
        on_add: Callable[[], None],
        on_update: Callable[[], None],
        on_remove: Callable[[], None],
        on_select: Callable[[], None],
        menu_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._ttk = ttk_module
        self._menu_factory = menu_factory
        self._enabled = True
        self.advanced_visible = False
        self.frame = ttk_module.Frame(parent, padding=32)
        ttk_module.Label(self.frame, text="Configura le caselle").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        self.table = ttk_module.Treeview(
            self.frame,
            columns=("name", "email", "provider", "status"),
            show="headings",
        )
        for column, heading in (
            ("name", "Nome casella"),
            ("email", "Email"),
            ("provider", "Provider"),
            ("status", "Stato"),
        ):
            self.table.heading(column, text=heading)
        self.table.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 16))
        self.name_entry = self._field(2, "Nome casella")
        self.name_entry.insert(0, "Principale")
        self.email_entry = self._field(3, "Email")
        self.password_entry = self._field(4, "Password", show="*")
        self.enabled_control = ttk_module.Checkbutton(
            self.frame, text="Casella attiva", command=self.toggle_enabled
        )
        self.enabled_control.state(("selected",))
        self.enabled_control.grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.advanced_button = ttk_module.Button(
            self.frame,
            text="Mostra impostazioni avanzate",
            command=self.toggle_advanced,
        )
        self.advanced_button.grid(row=6, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.advanced_frame = ttk_module.Frame(self.frame)
        self.advanced_frame.grid(row=7, column=0, columnspan=2, sticky="ew")
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
        self.advanced_frame.grid_remove()
        self.message = ttk_module.Label(self.frame, text="")
        self.message.grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 0))
        actions = ttk_module.Frame(self.frame)
        actions.grid(row=9, column=0, columnspan=2, sticky="w", pady=(12, 0))
        ttk_module.Button(actions, text="Aggiungi", command=on_add).grid(row=0, column=0)
        ttk_module.Button(actions, text="Modifica", command=on_update).grid(row=0, column=1)
        ttk_module.Button(actions, text="Rimuovi", command=on_remove).grid(row=0, column=2)
        ttk_module.Button(
            self.frame, text="Verifica collegamento", command=on_test
        ).grid(row=10, column=0, sticky="w", pady=(24, 0))
        ttk_module.Button(self.frame, text="Indietro", command=on_back).grid(
            row=11, column=0, sticky="w", pady=(24, 0)
        )
        ttk_module.Button(self.frame, text="Termina configurazione", command=on_continue).grid(
            row=11, column=1, sticky="e", pady=(24, 0)
        )
        self.table.bind("<<TreeviewSelect>>", lambda _event: on_select())

    def _field(self, row: int, label: str, **entry_options: Any) -> Any:
        self._ttk.Label(self.frame, text=label).grid(row=row, column=0, sticky="w")
        entry = self._ttk.Entry(self.frame, **entry_options)
        bind_text_interactions(entry, menu_factory=self._menu_factory)
        entry.grid(row=row, column=1, sticky="ew")
        return entry

    def visible_fields(self) -> tuple[str, ...]:
        return self.ORDINARY_FIELDS

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
        ):
            entry.delete(0, "end")
            entry.insert(0, value)
        self._enabled = account.enabled
        self.enabled_control.state(("selected" if account.enabled else "!selected",))

    def toggle_advanced(self) -> None:
        self.advanced_visible = not self.advanced_visible
        if self.advanced_visible:
            self.advanced_frame.grid(row=7, column=0, columnspan=2, sticky="ew")
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


class FirstRunController:
    """Replace wizard frames while keeping validation local to each step."""

    def __init__(
        self,
        parent: Any,
        *,
        ttk_module: Any,
        readonly_test: Callable[[AccountForm], str] | None = None,
        account_service: AccountManagementService | None = None,
        on_complete: Callable[[], None] | None = None,
        open_existing: bool = False,
        choose_folder: Callable[[], str] | None = None,
        menu_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.parent = parent
        self._ttk = ttk_module
        self.step = WizardStep.WELCOME
        self.current_view: WelcomeView | LimboView | AccountView | None = None
        self._welcome_validator = WelcomeValidator()
        self._limbo_validator = LimboValidator()
        self._account_validator = AccountValidator()
        self._readonly_test = readonly_test
        self._connection_check = (
            BackgroundAccountConnectionCheck(readonly_test)
            if readonly_test is not None
            else None
        )
        self._account_service = account_service
        self._on_complete = on_complete
        self._choose_folder = choose_folder
        self._menu_factory = menu_factory
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
            result = self._limbo_validator.validate(self.current_view.folder_value())
            self.current_view.show_validation(result)
            if result.is_valid:
                self._limbo_folder = self.current_view.folder_value()
                self._show_account()
            return result

        assert isinstance(self.current_view, AccountView)
        if self._account_service is not None:
            if not self._account_service.list_accounts():
                result = ValidationResult(False, "Aggiungi almeno una casella.")
                self.current_view.show_validation(result)
                return result
            result = ValidationResult(True, "Configurazione completata.")
            self.current_view.show_validation(result)
            if self._on_complete is not None:
                self._on_complete()
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

    def _save_account(self, *, update: bool) -> ValidationResult:
        assert isinstance(self.current_view, AccountView)
        form = self.current_view.form_value()
        result = self._account_validator.validate(form)
        alias = self.current_view.selected_alias() if update else None
        if result.is_valid and self._account_service is None:
            result = ValidationResult(False, "Salvataggio non disponibile.")
        elif result.is_valid and update and alias is None:
            result = ValidationResult(False, "Seleziona una casella da modificare.")
        elif result.is_valid and self._account_service is not None:
            if update:
                self._account_service.update(
                    alias, email=form.email, password=form.password, host=form.host,
                    port=form.port, enabled=form.enabled,
                )
                message = "Casella modificata."
            else:
                self._account_service.add(
                    name=form.name, email=form.email, password=form.password,
                    host=form.host, port=form.port, enabled=form.enabled,
                    limbo=Path(self._limbo_folder),
                )
                message = "Casella aggiunta."
            self.current_view.render_accounts(self._account_service.list_accounts())
            result = ValidationResult(True, message)
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
            if self._connection_check is None:
                result = ValidationResult(False, "Verifica non disponibile.")
            elif not self._connection_check.start(form):
                result = ValidationResult(False, "Verifica gia` in corso. Attendi il risultato.")
            else:
                result = ValidationResult(True, "Verifica avviata per la casella selezionata.")
                self._schedule_connection_poll()
        self.current_view.show_validation(result)
        return result

    def poll_account_connection(self) -> ValidationResult | None:
        if self._connection_check is None:
            return None
        feedback = self._connection_check.poll()
        if feedback is None:
            return None
        result = ValidationResult(feedback.ok, feedback.message)
        if isinstance(self.current_view, AccountView):
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
            initial_folder=self._limbo_folder,
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
            on_test=self.test_account_connection,
            on_add=self.add_account,
            on_update=self.update_account,
            on_remove=self.remove_account,
            on_select=self.load_selected_account,
            menu_factory=self._menu_factory,
        )
        if self._account_service is not None:
            view.render_accounts(self._account_service.list_accounts())
        self._replace(view, WizardStep.ACCOUNT)
