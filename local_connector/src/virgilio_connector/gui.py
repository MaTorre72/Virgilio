"""Local tkinter wrapper around the existing Virgilio CLI."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime

from .gui_config import GuiConfigService, GuiRuntimeSettings
from .gui_accounts import AccountDraft, AccountManager
from .gui_wizard import FirstRunWizard, WizardAccount
from .gui_runner import ManagedCliRunner
from .gui_home import HomeSnapshot, format_home_time, ROME
from .gui_activity import ActivityFilters, filter_activities, load_activities, parse_day


SENSITIVE_RE = re.compile(
    r"(?i)(password|token|secret|authorization|api[_-]?key)(['\"]?\s*[:=]\s*['\"]?)([^'\"\s,;]+)"
)


@dataclass(frozen=True)
class GuiCommandSpec:
    command: str
    config_path: Path | None = None
    dry_run: bool = False
    human: bool = False
    output_path: Path | None = None
    email: str = ""
    staging_dir: Path | None = None
    provider: str = "gmail_workspace"
    account_alias: str = ""
    imap_host: str = ""
    imap_port: int = 993
    input_folder: str = ""
    done_folder: str = ""
    error_folder: str = ""
    enable_bucoliche: bool = False
    force: bool = False
    interval_seconds: int = 300
    max_cycles: int = 0
    format_name: str = "jsonl"
    python_exe: Path | None = None
    task_name: str = "Virgilio Local Watch"
    backup: bool = False
    confirm: bool = False


@dataclass(frozen=True)
class GuiAction:
    key: str
    label: str
    tab: str
    summary: str
    command: str | None
    needs_config: bool = True
    dry_run: bool = False
    allow_dry_run_toggle: bool = False
    human: bool = False
    destructive: bool = False
    unavailable_reason: str = ""

    @property
    def available(self) -> bool:
        return self.command is not None and not self.unavailable_reason


def _config_args(spec: GuiCommandSpec) -> list[str]:
    if spec.config_path is None:
        raise ValueError("Seleziona prima il file di configurazione.")
    return ["--config", str(spec.config_path)]


def _add_common_runtime_flags(args: list[str], spec: GuiCommandSpec, *,
                              dry_run: bool = False, human: bool = False) -> list[str]:
    if dry_run or spec.dry_run:
        args.append("--dry-run")
    if human or spec.human:
        args.append("--human")
    return args


def build_cli_args(spec: GuiCommandSpec) -> list[str]:
    """Translate a GUI action into existing CLI arguments."""

    config_commands = {
        "doctor", "pilot", "pilot-run", "run-local-pipeline", "watch",
        "doctor-bucoliche", "pilot-preview", "pilot-check", "pilot-run-safe",
        "check-local-conflicts", "export-to-bucoliche", "refresh-bucoliche-state",
        "scan-imap-accounts", "process-imap-accounts", "stage-ready-attachments",
        "complete-staged-messages", "ack-completed-messages",
    }
    if spec.command in config_commands:
        args = [spec.command, *_config_args(spec)]
        if spec.command in {
            "pilot", "pilot-run", "run-local-pipeline", "watch",
            "doctor", "doctor-bucoliche", "pilot-preview", "pilot-run-safe",
        }:
            _add_common_runtime_flags(args, spec)
        elif spec.command in {
            "export-to-bucoliche", "refresh-bucoliche-state", "scan-imap-accounts",
            "process-imap-accounts", "stage-ready-attachments",
            "complete-staged-messages", "ack-completed-messages",
        } and spec.dry_run:
            args.append("--dry-run")
        if spec.command == "watch":
            args.extend(["--interval-seconds", str(spec.interval_seconds)])
            if spec.max_cycles:
                args.extend(["--max-cycles", str(spec.max_cycles)])
        return args

    if spec.command in {"export-central-events", "export-registro-events"}:
        if spec.format_name not in {"jsonl", "csv"}:
            raise ValueError("Formato export non valido.")
        return [spec.command, *_config_args(spec), "--format", spec.format_name]

    if spec.command == "init-config":
        if spec.output_path is None:
            raise ValueError("Scegli dove salvare il file di configurazione.")
        if not spec.email.strip():
            raise ValueError("Inserisci l'email dell'account.")
        if spec.staging_dir is None:
            raise ValueError("Seleziona la Cartella Limbo.")
        args = [
            "init-config",
            "--output", str(spec.output_path),
            "--email", spec.email.strip(),
            "--staging-dir", str(spec.staging_dir),
            "--provider", spec.provider,
            "--imap-port", str(spec.imap_port),
        ]
        optional_pairs = (
            ("--account-alias", spec.account_alias),
            ("--imap-host", spec.imap_host),
            ("--input-folder", spec.input_folder),
            ("--done-folder", spec.done_folder),
            ("--error-folder", spec.error_folder),
        )
        for flag, value in optional_pairs:
            if value.strip():
                args.extend([flag, value.strip()])
        if spec.enable_bucoliche:
            args.append("--enable-bucoliche")
        if spec.dry_run:
            args.append("--dry-run")
        if spec.force:
            args.append("--force")
        return args

    if spec.command == "install-windows-task":
        args = [spec.command, *_config_args(spec)]
        if spec.python_exe is not None:
            args.extend(["--python-exe", str(spec.python_exe)])
        if spec.task_name.strip():
            args.extend(["--task-name", spec.task_name.strip()])
        args.extend(["--interval-seconds", str(spec.interval_seconds)])
        if spec.dry_run:
            args.append("--dry-run")
        if spec.force:
            args.append("--force")
        if spec.human:
            args.append("--human")
        return args

    if spec.command in {"status-windows-task", "uninstall-windows-task"}:
        args = [spec.command]
        if spec.task_name.strip():
            args.extend(["--task-name", spec.task_name.strip()])
        if spec.command == "uninstall-windows-task" and spec.confirm:
            args.append("--confirm")
        if spec.human:
            args.append("--human")
        return args

    if spec.command == "reset-local-state":
        args = ["reset-local-state"]
        if spec.backup:
            args.append("--backup")
        if spec.confirm:
            args.append("--confirm")
        if spec.human:
            args.append("--human")
        return args

    raise ValueError(f"Azione GUI non supportata: {spec.command}")


def run_cli_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "virgilio_connector", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def sanitize_output(text: str) -> str:
    """Keep GUI output readable without exposing obvious secret values."""

    return SENSITIVE_RE.sub(r"\1\2<redacted>", text)


def gui_tabs() -> tuple[str, ...]:
    return (
        "Stato",
        "Setup iniziale",
        "Account mail",
        "Bucoliche",
        "Avvio",
        "Monitoraggio",
        "Manutenzione",
        "Automazione Win11",
        "Diagnostica avanzata",
    )


def gui_actions() -> tuple[GuiAction, ...]:
    return (
        GuiAction("status-doctor", "Controlla stato locale", "Stato",
                  "Verifica configurazione, account, storage, scanner e DB locale.", "doctor",
                  human=True),
        GuiAction("status-preview", "Mostra preview operativa", "Stato",
                  "Mostra stato sintetico del pilota e prossime azioni.", "pilot-preview",
                  human=True),
        GuiAction("status-task", "Stato attivita Win11", "Stato",
                  "Mostra stato e ultimo esito dell'avvio automatico Windows.",
                  "status-windows-task", needs_config=False, human=True),
        GuiAction("setup-init", "Crea configurazione", "Setup iniziale",
                  "Genera o simula un file config senza segreti in chiaro.", "init-config",
                  needs_config=False, allow_dry_run_toggle=True),
        GuiAction("setup-doctor", "Test configurazione", "Setup iniziale",
                  "Esegue il doctor generale sul file selezionato.", "doctor", human=True),
        GuiAction("setup-limbo", "Verifica Limbo e cartelle", "Setup iniziale",
                  "Controlla la Cartella Limbo e le cartelle locali necessarie.", "doctor",
                  human=True),
        GuiAction("mail-list", "Visualizza account", "Account mail",
                  "Il doctor riepiloga account configurati e variabili richieste.", "doctor",
                  human=True),
        GuiAction("mail-test", "Test IMAP", "Account mail",
                  "Il doctor valida host, porta, username e accesso IMAP senza stampare password.",
                  "doctor", human=True),
        GuiAction("bucoliche-doctor", "Verifica Bucoliche", "Bucoliche",
                  "Controlla configurazione e tab Bucoliche consolidate.", "doctor-bucoliche",
                  human=True),
        GuiAction("bucoliche-state", "Verifica stato Bucoliche", "Bucoliche",
                  "Simula il refresh di Bucoliche_Stato senza dati reali.", "refresh-bucoliche-state",
                  dry_run=True),
        GuiAction("bucoliche-export", "Test export Bucoliche", "Bucoliche",
                  "Simula l'append verso Bucoliche_Eventi.", "export-to-bucoliche",
                  dry_run=True),
        GuiAction("start-once", "Scansione manuale", "Avvio",
                  "Esegue un ciclo controllato della pipeline locale.", "run-local-pipeline",
                  human=True, allow_dry_run_toggle=True),
        GuiAction("start-watch-once", "Prova monitoraggio", "Avvio",
                  "Esegue watch per un solo ciclo, utile come prova non bloccante.", "watch",
                  human=True, allow_dry_run_toggle=True),
        GuiAction("start-watch", "Avvia monitoraggio continuo", "Avvio",
                  "Avvia watch continuo tramite CLI esistente.", "watch", human=True,
                  allow_dry_run_toggle=True),
        GuiAction("stop-watch", "Ferma monitoraggio continuo", "Avvio",
                  "Ferma in modo controllato il processo watch posseduto dalla GUI.", "watch"),
        GuiAction("monitor-pilot", "Report ultimo ciclo", "Monitoraggio",
                  "Esegue il pilot completo in dry-run e mostra messaggi utente.", "pilot-run",
                  dry_run=True, human=True),
        GuiAction("monitor-conflicts", "Controlla conflitti", "Monitoraggio",
                  "Legge lo stato locale e segnala conflitti recenti.", "check-local-conflicts"),
        GuiAction("monitor-export", "Export diagnostico Registro", "Monitoraggio",
                  "Esporta eventi Registro locali in formato jsonl.", "export-registro-events"),
        GuiAction("maintenance-reset", "Reset locale con backup", "Manutenzione",
                  "Esegue reset locale solo con backup e conferma esplicita.", "reset-local-state",
                  needs_config=False, destructive=True),
        GuiAction("maintenance-backup", "Backup stato locale", "Manutenzione",
                  "Manca una CLI backup-only separata dal reset sicuro.",
                  None, needs_config=False, unavailable_reason="CLI mancante: backup-local-state"),
        GuiAction("maintenance-config-export", "Export config senza segreti", "Manutenzione",
                  "Manca una CLI stabile di export configurazione.",
                  None, unavailable_reason="CLI mancante: export-config"),
        GuiAction("maintenance-config-import", "Import configurazione", "Manutenzione",
                  "Manca una CLI stabile di import configurazione.",
                  None, unavailable_reason="CLI mancante: import-config"),
        GuiAction("maintenance-db", "Verifica integrita DB", "Manutenzione",
                  "Manca una CLI dedicata per PRAGMA integrity_check sul DB locale.",
                  None, unavailable_reason="CLI mancante: check-state-db"),
        GuiAction("maintenance-quarantine", "Pulizia Quarantena locale", "Manutenzione",
                  "Manca una CLI stabile per pulizia controllata della Quarantena.",
                  None, unavailable_reason="CLI mancante: clean-local-quarantine"),
        GuiAction("win11-plan", "Verifica piano task", "Automazione Win11",
                  "Simula la registrazione del task Win11 senza crearla.", "install-windows-task",
                  dry_run=True, human=True),
        GuiAction("win11-install", "Installa task Win11", "Automazione Win11",
                  "Registra l'avvio automatico via Utilita di Pianificazione.", "install-windows-task",
                  destructive=True, human=True),
        GuiAction("win11-remove", "Rimuovi task Win11", "Automazione Win11",
                  "Rimuove l'avvio automatico solo dopo conferma esplicita.",
                  "uninstall-windows-task", needs_config=False, human=True, destructive=True),
        GuiAction("win11-status", "Leggi stato task Win11", "Automazione Win11",
                  "Mostra installazione, stato, ultima esecuzione e ultimo esito.",
                  "status-windows-task", needs_config=False, human=True),
        GuiAction("diag-doctor", "Doctor avanzato", "Diagnostica avanzata",
                  "Esegue doctor in formato umano.", "doctor", human=True),
        GuiAction("diag-pilot-safe", "Smoke pilota mirato", "Diagnostica avanzata",
                  "Esegue i gate pilot-check, pipeline dry-run ed export Bucoliche dry-run.",
                  "pilot-run-safe", human=True),
        GuiAction("diag-central", "Export eventi centrali", "Diagnostica avanzata",
                  "Esporta eventi locali senza segreti.", "export-central-events"),
    )


def gui_actions_by_tab() -> dict[str, tuple[GuiAction, ...]]:
    actions = gui_actions()
    return {tab: tuple(action for action in actions if action.tab == tab) for tab in gui_tabs()}


def gui_context_fields() -> dict[str, tuple[str, ...]]:
    """Declare which settings may be visible in each GUI area."""

    return {
        "Stato": (),
        "Setup iniziale": ("profile", "init_output", "init_email", "local_data", "limbo", "scanner"),
        "Account mail": (),
        "Bucoliche": ("shared_register",),
        "Avvio": ("interval", "safe_test"),
        "Monitoraggio": (),
        "Manutenzione": ("confirm_reset",),
        "Automazione Win11": ("interval", "task_name"),
        "Diagnostica avanzata": ("python", "format", "max_cycles"),
    }


class VirgilioGuiApp:
    """Operator GUI that delegates execution to the CLI entrypoint."""

    def __init__(self, root, *, command_runner=run_cli_command,
                 managed_runner: ManagedCliRunner | None = None,
                 initial_config: Path | None = None):
        import tkinter as tk
        from tkinter import ttk

        self._tk = tk
        self._ttk = ttk
        self.root = root
        self.command_runner = command_runner
        self.managed_runner = managed_runner or ManagedCliRunner()

        root.title("Virgilio Caronte locale")
        root.minsize(980, 680)

        self.config_var = tk.StringVar(value=str(initial_config) if initial_config else "")
        self.output_var = tk.StringVar(value="")
        self.email_var = tk.StringVar(value="")
        self.staging_var = tk.StringVar(value="")
        self.local_data_var = tk.StringVar(value="")
        self.scanner_var = tk.StringVar(value="auto")
        self.provider_var = tk.StringVar(value="gmail_workspace")
        self.alias_var = tk.StringVar(value="")
        self.imap_host_var = tk.StringVar(value="")
        self.imap_port_var = tk.IntVar(value=993)
        self.input_folder_var = tk.StringVar(value="")
        self.done_folder_var = tk.StringVar(value="")
        self.error_folder_var = tk.StringVar(value="")
        self.enable_bucoliche_var = tk.BooleanVar(value=False)
        self.dry_run_var = tk.BooleanVar(value=True)
        self.force_var = tk.BooleanVar(value=False)
        self.interval_var = tk.IntVar(value=300)
        self.max_cycles_var = tk.IntVar(value=1)
        self.format_var = tk.StringVar(value="jsonl")
        self.python_var = tk.StringVar(value=sys.executable)
        self.task_name_var = tk.StringVar(value="Virgilio Local Watch")
        self.confirm_reset_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Pronto")
        self.home = HomeSnapshot()
        self.home_vars = {key: tk.StringVar(value="") for key in (
            "state", "accounts", "checks", "completed", "problems", "last", "next", "problem")}
        self.activity_rows = ()
        self.activity_account_var = tk.StringVar(value="Tutte")
        self.activity_outcome_var = tk.StringVar(value="Tutti")
        self.activity_day_var = tk.StringVar(value="")
        self.activity_error_var = tk.StringVar(value="Tutti")
        self.activity_count_var = tk.StringVar(value="Nessuna attivita locale")

        self._build_layout()
        root.protocol("WM_DELETE_WINDOW", self._close)
        root.after(100, self._poll_runner)

    def _build_layout(self) -> None:
        from tkinter import filedialog

        self._filedialog = filedialog
        root = self.root
        ttk = self._ttk

        shell = ttk.Frame(root, padding=12)
        shell.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)

        notebook = ttk.Notebook(shell)
        notebook.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        for tab, actions in gui_actions_by_tab().items():
            frame = ttk.Frame(notebook, padding=10)
            notebook.add(frame, text=tab)
            self._build_context_panel(frame, tab)
            if tab == "Stato":
                self._build_home(frame)
            elif tab == "Monitoraggio":
                self._build_activity(frame, actions)
            else:
                self._build_tab(frame, actions, row_offset=(1 if gui_context_fields()[tab] else 0))

        self._refresh_home_config()
        self._render_home()

        output_frame = ttk.Frame(shell)
        output_frame.grid(row=1, column=0, sticky="nsew")
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(1, weight=1)
        ttk.Label(output_frame, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        ttk.Button(output_frame, text="Copia report", command=self._copy_output).grid(
            row=0, column=1, sticky="e"
        )
        self.output_text = self._tk.Text(output_frame, wrap="word", height=12)
        self.output_text.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(4, 0))

    def _build_context_panel(self, parent, tab: str) -> None:
        ttk = self._ttk
        fields = gui_context_fields()[tab]
        if not fields:
            return
        panel = ttk.LabelFrame(parent, text="Impostazioni di questa area", padding=10)
        panel.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        panel.columnconfigure(1, weight=1)
        row = 0

        def entry(label, variable, browse=None):
            nonlocal row
            ttk.Label(panel, text=label).grid(row=row, column=0, sticky="w", pady=3)
            ttk.Entry(panel, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=8, pady=3)
            if browse:
                ttk.Button(panel, text="Sfoglia...", command=browse).grid(row=row, column=2, pady=3)
            row += 1

        if "profile" in fields:
            entry("Profilo locale", self.config_var, self._browse_config)
        if "init_output" in fields:
            entry("Nuovo profilo", self.output_var, self._browse_output)
        if "init_email" in fields:
            entry("Email prima casella", self.email_var)
        if "local_data" in fields:
            entry("Cartella dati locali", self.local_data_var, self._browse_local_data)
        if "limbo" in fields:
            entry("Cartella Limbo", self.staging_var, self._browse_staging)
        if "scanner" in fields:
            ttk.Label(panel, text="Controllo antivirus").grid(row=row, column=0, sticky="w", pady=3)
            ttk.Combobox(panel, textvariable=self.scanner_var,
                         values=("auto", "defender", "disabled"), state="readonly").grid(
                             row=row, column=1, sticky="w", padx=8, pady=3)
            row += 1
        if "shared_register" in fields:
            ttk.Checkbutton(panel, text="Usa il Registro condiviso Bucoliche",
                            variable=self.enable_bucoliche_var).grid(
                                row=row, column=0, columnspan=2, sticky="w")
            row += 1
        if "interval" in fields:
            ttk.Label(panel, text="Controlla ogni (secondi)").grid(row=row, column=0, sticky="w", pady=3)
            ttk.Spinbox(panel, from_=1, to=86400, textvariable=self.interval_var, width=8).grid(
                row=row, column=1, sticky="w", padx=8, pady=3)
            row += 1
        if "safe_test" in fields:
            ttk.Checkbutton(panel, text="Prova senza modifiche", variable=self.dry_run_var).grid(
                row=row, column=0, columnspan=2, sticky="w")
            row += 1
        if "confirm_reset" in fields:
            ttk.Checkbutton(panel, text="Ho compreso: crea backup e azzera lo stato locale",
                            variable=self.confirm_reset_var).grid(
                                row=row, column=0, columnspan=2, sticky="w")
            row += 1
        if "task_name" in fields:
            entry("Nome avvio automatico", self.task_name_var)
        if "python" in fields:
            entry("Eseguibile Python", self.python_var, self._browse_python)
        if "format" in fields:
            ttk.Label(panel, text="Formato export tecnico").grid(row=row, column=0, sticky="w", pady=3)
            ttk.Combobox(panel, textvariable=self.format_var, values=("jsonl", "csv"),
                         state="readonly").grid(row=row, column=1, sticky="w", padx=8, pady=3)
            row += 1
        if "max_cycles" in fields:
            ttk.Label(panel, text="Cicli massimi di prova").grid(row=row, column=0, sticky="w", pady=3)
            ttk.Spinbox(panel, from_=0, to=999, textvariable=self.max_cycles_var, width=8).grid(
                row=row, column=1, sticky="w", padx=8, pady=3)
            row += 1
        if tab in {"Setup iniziale", "Bucoliche", "Avvio", "Automazione Win11"}:
            ttk.Button(panel, text="Salva impostazioni",
                       command=lambda area=tab: self._save_context_settings(area)).grid(
                           row=row, column=1, sticky="e", padx=8, pady=(6, 0))

    def _build_tab(self, frame, actions: tuple[GuiAction, ...], *, row_offset: int = 0) -> None:
        ttk = self._ttk
        frame.columnconfigure(1, weight=1)
        if actions and actions[0].tab == "Setup iniziale":
            ttk.Button(frame, text="Apri procedura guidata", command=self._open_first_run_wizard,
                       width=28).grid(row=row_offset, column=0, sticky="ew", pady=3)
            ttk.Label(frame, text="Guida Cartelle, Caselle, Registro condiviso e verifica finale.",
                      wraplength=620, justify="left").grid(
                          row=row_offset, column=1, sticky="w", padx=(10, 0), pady=3)
            row_offset += 1
        elif actions and actions[0].tab == "Account mail":
            ttk.Button(frame, text="Gestisci caselle", command=self._open_account_manager,
                       width=28).grid(row=row_offset, column=0, sticky="ew", pady=3)
            ttk.Label(frame, text="Gestione completa delle caselle senza modificare file manualmente.",
                      wraplength=620, justify="left").grid(
                          row=row_offset, column=1, sticky="w", padx=(10, 0))
            row_offset += 1
        for row, action in enumerate(actions):
            ttk.Button(
                frame,
                text=action.label,
                command=lambda item=action: self.run_action(item),
                state=("normal" if action.available else "disabled"),
                width=28,
            ).grid(row=row + row_offset, column=0, sticky="ew", pady=3)
            text = action.summary
            if not action.available:
                text = f"{text} ({action.unavailable_reason})"
            ttk.Label(frame, text=text, wraplength=620, justify="left").grid(
                row=row + row_offset, column=1, sticky="w", padx=(10, 0), pady=3
            )

    def _build_home(self, frame) -> None:
        ttk = self._ttk
        frame.columnconfigure((0, 1, 2, 3), weight=1)
        ttk.Label(frame, textvariable=self.home_vars["state"],
                  font=("TkDefaultFont", 16, "bold")).grid(
                      row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))
        cards = (("Caselle attive", "accounts"), ("Controlli", "checks"),
                 ("Completati", "completed"), ("Problemi", "problems"))
        for index, (label, key) in enumerate(cards):
            box = ttk.LabelFrame(frame, text=label, padding=10)
            box.grid(row=1, column=index, sticky="nsew", padx=4, pady=4)
            ttk.Label(box, textvariable=self.home_vars[key],
                      font=("TkDefaultFont", 14, "bold")).grid()
        ttk.Label(frame, textvariable=self.home_vars["last"]).grid(row=3, column=0, sticky="w", pady=6)
        ttk.Label(frame, textvariable=self.home_vars["next"]).grid(row=3, column=1, sticky="w", pady=6)
        ttk.Label(frame, textvariable=self.home_vars["problem"], wraplength=760).grid(
            row=4, column=0, columnspan=4, sticky="w", pady=6)
        primary = {action.key: action for action in gui_actions()}
        for column, key in enumerate(("start-once", "start-watch", "stop-watch")):
            action = primary[key]
            ttk.Button(frame, text=action.label, command=lambda item=action: self.run_action(item),
                       width=28).grid(row=5, column=column, sticky="ew", padx=4, pady=(12, 0))

    def _build_activity(self, frame, actions: tuple[GuiAction, ...]) -> None:
        ttk = self._ttk
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        filters = ttk.LabelFrame(frame, text="Filtra attivita", padding=8)
        filters.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        labels = (("Casella", self.activity_account_var), ("Esito", self.activity_outcome_var),
                  ("Data (gg/mm/aaaa)", self.activity_day_var),
                  ("Errori", self.activity_error_var))
        for column, (label, variable) in enumerate(labels):
            ttk.Label(filters, text=label).grid(row=0, column=column * 2, sticky="w", padx=(0, 4))
            if column == 0:
                self.activity_account_combo = ttk.Combobox(
                    filters, textvariable=variable, values=("Tutte",), state="readonly", width=16)
                widget = self.activity_account_combo
            elif column == 1:
                widget = ttk.Combobox(filters, textvariable=variable,
                                      values=("Tutti", "Riuscito", "Completato", "In attesa",
                                              "Ignorato", "Problema"), state="readonly", width=14)
            elif column == 3:
                widget = ttk.Combobox(filters, textvariable=variable,
                                      values=("Tutti", "Solo errori", "Senza errori"),
                                      state="readonly", width=14)
            else:
                widget = ttk.Entry(filters, textvariable=variable, width=14)
            widget.grid(row=0, column=column * 2 + 1, sticky="w", padx=(0, 10))
            if column != 2:
                widget.bind("<<ComboboxSelected>>", lambda _event: self._render_activity())
        ttk.Button(filters, text="Applica data", command=self._render_activity).grid(row=0, column=8, padx=3)
        ttk.Button(filters, text="Aggiorna", command=self._refresh_activity).grid(row=0, column=9, padx=3)

        columns = ("data", "casella", "messaggio", "allegato", "azione", "esito", "problema")
        table = ttk.Frame(frame)
        table.grid(row=1, column=0, sticky="nsew")
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        self.activity_tree = ttk.Treeview(table, columns=columns, show="headings", height=11)
        headings = ("Data e ora", "Casella", "Messaggio", "Allegato", "Azione", "Esito", "Problema")
        widths = (135, 100, 180, 130, 145, 90, 240)
        for key, heading, width in zip(columns, headings, widths):
            self.activity_tree.heading(key, text=heading)
            self.activity_tree.column(
                key, width=width, minwidth=70, stretch=(key in {"messaggio", "problema"}))
        vertical = ttk.Scrollbar(table, orient="vertical", command=self.activity_tree.yview)
        horizontal = ttk.Scrollbar(table, orient="horizontal", command=self.activity_tree.xview)
        self.activity_tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.activity_tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        ttk.Label(frame, textvariable=self.activity_count_var).grid(row=2, column=0, sticky="w", pady=(4, 8))

        actions_frame = ttk.Frame(frame)
        actions_frame.grid(row=3, column=0, sticky="ew")
        for column, action in enumerate(actions):
            ttk.Button(actions_frame, text=action.label,
                       command=lambda item=action: self.run_action(item),
                       state=("normal" if action.available else "disabled")).grid(
                           row=0, column=column, padx=(0, 6), sticky="w")
        self._refresh_activity()

    def _refresh_activity(self) -> None:
        local_root = Path(os.environ.get("VIRGILIO_LOCAL_DATA_DIR", ".local_data"))
        redact = sanitize_output
        config_text = self.config_var.get().strip()
        if config_text:
            service = GuiConfigService(Path(config_text), Path(config_text).with_name(".env.local"))
            redact = lambda value: sanitize_output(service.redact(value))
        try:
            self.activity_rows = load_activities(local_root / "state.db", redact=redact)
            accounts = tuple(sorted({row.account for row in self.activity_rows}))
            self.activity_account_combo.configure(values=("Tutte", *accounts))
            if self.activity_account_var.get() not in ("Tutte", *accounts):
                self.activity_account_var.set("Tutte")
            self._render_activity()
        except (OSError, ValueError) as exc:
            self.activity_rows = ()
            self.activity_count_var.set(f"Attivita non disponibili: {sanitize_output(str(exc))}")

    def _render_activity(self) -> None:
        try:
            day = parse_day(self.activity_day_var.get())
        except ValueError:
            self.activity_count_var.set("Data non valida: usa gg/mm/aaaa.")
            return
        error_values = {"Tutti": "all", "Solo errori": "only", "Senza errori": "without"}
        rows = filter_activities(self.activity_rows, ActivityFilters(
            account="" if self.activity_account_var.get() == "Tutte" else self.activity_account_var.get(),
            outcome="" if self.activity_outcome_var.get() == "Tutti" else self.activity_outcome_var.get(),
            day=day, errors=error_values.get(self.activity_error_var.get(), "all"),
        ))
        self.activity_tree.delete(*self.activity_tree.get_children())
        for index, row in enumerate(rows):
            self.activity_tree.insert("", "end", iid=f"activity-{index}", values=(
                row.occurred_text, row.account, row.message, row.attachment,
                row.action, row.outcome, row.problem or "-"))
        self.activity_count_var.set(
            f"{len(rows)} attivita mostrate" if rows else "Nessuna attivita per i filtri selezionati")

    def _refresh_home_config(self) -> None:
        config_text = self.config_var.get().strip()
        if not config_text:
            self.home = HomeSnapshot()
            return
        try:
            service = GuiConfigService(Path(config_text), Path(config_text).with_name(".env.local"))
            model = service.load()
            self.home = self.home.with_accounts(sum(account.enabled for account in model.accounts))
            if not self.staging_var.get().strip():
                self.staging_var.set(str(model.storage.staging_dir))
            settings = service.load_runtime_settings()
            if settings.local_data_dir is not None:
                self.local_data_var.set(str(settings.local_data_dir))
                os.environ["VIRGILIO_LOCAL_DATA_DIR"] = str(settings.local_data_dir)
            self.scanner_var.set(settings.scanner)
            self.interval_var.set(settings.interval_seconds)
            self.task_name_var.set(settings.task_name)
            self.enable_bucoliche_var.set(FirstRunWizard(service).draft.bucoliche_enabled)
            os.environ["VIRGILIO_SCANNER"] = settings.scanner
        except (OSError, ValueError) as exc:
            self.home = HomeSnapshot(problem=f"Configurazione non pronta: {sanitize_output(str(exc))}")

    def _render_home(self) -> None:
        values = {
            "state": self.home.state, "accounts": str(self.home.active_accounts),
            "checks": str(self.home.checks), "completed": str(self.home.completed),
            "problems": str(self.home.problems),
            "last": f"Ultima verifica: {format_home_time(self.home.last_check)}",
            "next": f"Prossima verifica: {format_home_time(self.home.next_check)}",
            "problem": self.home.problem or "Nessun problema rilevato.",
        }
        for key, value in values.items():
            self.home_vars[key].set(value)

    def _open_account_manager(self) -> None:
        config_text = self.config_var.get().strip()
        if not config_text:
            self._set_output("Seleziona prima il file di configurazione.")
            return
        manager = AccountManager(GuiConfigService(
            Path(config_text), Path(config_text).with_name(".env.local")
        ))
        window = self._tk.Toplevel(self.root)
        window.title("Caselle mail")
        frame = self._ttk.Frame(window, padding=12)
        frame.grid(sticky="nsew")
        tree = self._ttk.Treeview(frame, columns=("email", "server", "stato"), show="tree headings", height=7)
        tree.heading("#0", text="Nome")
        for key, title in (("email", "Email"), ("server", "Server"), ("stato", "Stato")):
            tree.heading(key, text=title)
        tree.grid(row=0, column=0, columnspan=5, sticky="nsew")
        fields = {name: self._tk.StringVar() for name in (
            "alias", "email", "username", "password", "provider", "host", "port",
            "input", "done", "error")}
        enabled = self._tk.BooleanVar(value=True)
        current_alias = self._tk.StringVar(value="")
        labels = (("Nome", "alias"), ("Email", "email"), ("Utente", "username"),
                  ("Password", "password"), ("Provider", "provider"), ("Server IMAP", "host"),
                  ("Porta", "port"), ("Cartella in ingresso", "input"),
                  ("Cartella completate", "done"), ("Cartella errori", "error"))
        password_entry = None
        for index, (label, key) in enumerate(labels):
            row, pair = divmod(index, 2)
            column = pair * 2
            self._ttk.Label(frame, text=label).grid(row=row + 1, column=column, sticky="w", pady=3)
            entry = self._ttk.Entry(frame, textvariable=fields[key],
                                    show=("*" if key == "password" else ""))
            entry.grid(row=row + 1, column=column + 1, sticky="ew", padx=6, pady=3)
            if key == "password":
                password_entry = entry
        self._ttk.Checkbutton(frame, text="Casella attiva", variable=enabled).grid(row=6, column=0, sticky="w")
        password_visible = self._tk.BooleanVar(value=False)

        def toggle_password_visibility() -> None:
            password_entry.configure(show="" if password_visible.get() else "*")

        self._ttk.Checkbutton(
            frame, text="Mostra password", variable=password_visible,
            command=toggle_password_visibility,
        ).grid(row=6, column=1, sticky="w")

        def refresh() -> None:
            tree.delete(*tree.get_children())
            for item in manager.list_accounts():
                tree.insert("", "end", iid=item.account_alias, text=item.account_alias,
                            values=(item.email, f"{item.imap_host}:{item.imap_port}",
                                    "Attiva" if item.enabled else "Disattivata"))

        def load_selected(_event=None) -> None:
            selection = tree.selection()
            if not selection:
                return
            draft = manager.get(selection[0])
            current_alias.set(draft.alias)
            values = (draft.alias, draft.email, draft.username, draft.password, draft.provider,
                      draft.imap_host, str(draft.imap_port), draft.input_folder,
                      draft.done_folder, draft.error_folder)
            for key, value in zip(fields, values):
                fields[key].set(value)
            enabled.set(draft.enabled)

        def save() -> None:
            try:
                draft = AccountDraft(fields["alias"].get(), fields["email"].get(),
                    fields["username"].get(), fields["password"].get(), fields["provider"].get(),
                    fields["host"].get(), int(fields["port"].get()), fields["input"].get(),
                    fields["done"].get(), fields["error"].get(), enabled.get())
                manager.save(draft, previous_alias=current_alias.get() or None)
                current_alias.set(draft.alias)
                refresh()
                self.status_var.set("Casella salvata")
            except (ValueError, OSError) as exc:
                self._set_output(manager.service.redact(
                    f"Casella non salvata: {exc}",
                    (fields["username"].get(), fields["password"].get()),
                ))

        def new() -> None:
            current_alias.set("")
            defaults = AccountDraft("", "")
            values = (defaults.alias, defaults.email, defaults.username, defaults.password,
                      defaults.provider, defaults.imap_host, str(defaults.imap_port),
                      defaults.input_folder, defaults.done_folder, defaults.error_folder)
            for key, value in zip(fields, values): fields[key].set(value)
            enabled.set(True)

        def toggle() -> None:
            try:
                if current_alias.get():
                    manager.set_enabled(current_alias.get(), not enabled.get())
                    load_selected()
                    refresh()
            except (ValueError, OSError) as exc:
                self._set_output(manager.service.redact(f"Stato casella non aggiornato: {exc}"))

        def remove() -> None:
            try:
                if current_alias.get() and self._confirm(GuiAction(
                        "remove", "Rimuovi casella", "Account mail", "", "x", destructive=True)):
                    manager.remove(current_alias.get())
                    new()
                    refresh()
            except (ValueError, OSError) as exc:
                self._set_output(manager.service.redact(f"Casella non rimossa: {exc}"))

        def test() -> None:
            if current_alias.get():
                try:
                    self._set_output(manager.test_connection(current_alias.get()).message)
                except (ValueError, OSError) as exc:
                    self._set_output(manager.service.redact(f"Test non riuscito: {exc}"))

        tree.bind("<<TreeviewSelect>>", load_selected)
        for column, (text, command) in enumerate((("Nuova", new), ("Salva", save),
                ("Abilita / disabilita", toggle), ("Prova read-only", test), ("Rimuovi", remove))):
            self._ttk.Button(frame, text=text, command=command).grid(row=7, column=column, padx=3, pady=(8, 0))
        refresh()

    def _open_first_run_wizard(self) -> None:
        config_text = self.config_var.get().strip()
        if not config_text:
            config_text = str(Path.cwd() / "accounts.local.yaml")
            self.config_var.set(config_text)
        service = GuiConfigService(Path(config_text), Path(config_text).with_name(".env.local"))
        wizard = FirstRunWizard(service)
        existing = wizard.draft.accounts
        window = self._tk.Toplevel(self.root)
        window.title("Primo avvio Caronte locale")
        window.transient(self.root)
        fields = self._ttk.Frame(window, padding=14)
        fields.grid(sticky="nsew")
        limbo = self._tk.StringVar(value=str(wizard.draft.staging_dir or self.staging_var.get()))
        alias = self._tk.StringVar(value=existing[0].alias if existing else "account_1")
        email = self._tk.StringVar(value=existing[0].email if existing else self.email_var.get())
        second_email = self._tk.StringVar(value=existing[1].email if len(existing) > 1 else "")
        bucoliche = self._tk.BooleanVar(value=wizard.draft.bucoliche_enabled)
        status = self._tk.StringVar(value="Passo 1 di 4 - Cartelle")
        labels = (("Cartella Limbo", limbo), ("Nome prima casella", alias),
                  ("Email prima casella", email), ("Email seconda casella (facoltativa)", second_email))
        for row, (text, variable) in enumerate(labels):
            self._ttk.Label(fields, text=text).grid(row=row, column=0, sticky="w", pady=4)
            self._ttk.Entry(fields, textvariable=variable, width=54).grid(
                row=row, column=1, sticky="ew", padx=8, pady=4)
        self._ttk.Checkbutton(fields, text="Uso anche il Registro condiviso Bucoliche",
                              variable=bucoliche).grid(row=4, column=0, columnspan=2, sticky="w")
        self._ttk.Label(fields, textvariable=status, wraplength=560).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(10, 4))

        def collect() -> None:
            wizard.set_folders(Path(limbo.get().strip()))
            accounts = [WizardAccount(alias.get().strip(), email.get().strip())]
            if second_email.get().strip():
                accounts.append(WizardAccount("account_2", second_email.get().strip()))
            wizard.set_accounts(tuple(accounts))
            wizard.set_bucoliche(bucoliche.get())

        def go_next() -> None:
            try:
                collect()
                if wizard.step_index == 3:
                    wizard.save()
                    self.staging_var.set(limbo.get().strip())
                    status.set("Configurazione salvata. Puoi riaprire la procedura quando vuoi.")
                    return
                wizard.next()
                status.set(f"Passo {wizard.step_index + 1} di 4 - {wizard.step}")
            except (ValueError, OSError) as exc:
                status.set(f"Da completare: {sanitize_output(str(exc))}")

        def go_back() -> None:
            wizard.back()
            status.set(f"Passo {wizard.step_index + 1} di 4 - {wizard.step}")

        self._ttk.Button(fields, text="Indietro", command=go_back).grid(row=6, column=0, sticky="w")
        self._ttk.Button(fields, text="Avanti / Salva", command=go_next).grid(row=6, column=1, sticky="e")

    def _set_output(self, text: str) -> None:
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", sanitize_output(text).strip() or "(nessun output)")

    def _copy_output(self) -> None:
        text = sanitize_output(self.output_text.get("1.0", "end")).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set("Report copiato negli appunti")

    def _browse_config(self) -> None:
        path = self._filedialog.askopenfilename(
            title="Seleziona accounts.local.yaml",
            filetypes=[("YAML", "*.yaml *.yml"), ("Tutti i file", "*.*")],
        )
        if path:
            self.config_var.set(path)
            self._refresh_home_config()
            self._render_home()
            self._refresh_activity()

    def _browse_output(self) -> None:
        path = self._filedialog.asksaveasfilename(
            title="Scrivi file di configurazione",
            defaultextension=".yaml",
            filetypes=[("YAML", "*.yaml"), ("Tutti i file", "*.*")],
        )
        if path:
            self.output_var.set(path)

    def _browse_staging(self) -> None:
        path = self._filedialog.askdirectory(title="Seleziona Cartella Limbo")
        if path:
            self.staging_var.set(path)

    def _browse_local_data(self) -> None:
        path = self._filedialog.askdirectory(title="Seleziona cartella dati locali")
        if path:
            self.local_data_var.set(path)

    def _browse_python(self) -> None:
        path = self._filedialog.askopenfilename(
            title="Seleziona python.exe",
            filetypes=[("Python", "python.exe"), ("Tutti i file", "*.*")],
        )
        if path:
            self.python_var.set(path)

    def _spec_for_action(self, action: GuiAction) -> GuiCommandSpec:
        config_text = self.config_var.get().strip()
        output_text = self.output_var.get().strip()
        staging_text = self.staging_var.get().strip()
        python_text = self.python_var.get().strip()
        max_cycles = self.max_cycles_var.get()
        if action.key == "start-watch-once":
            max_cycles = 1
        if action.key == "start-watch":
            max_cycles = 0
        dry_run = action.dry_run or (action.allow_dry_run_toggle and self.dry_run_var.get())
        if action.key in {"win11-install", "maintenance-reset"}:
            dry_run = False
        return GuiCommandSpec(
            command=action.command or "",
            config_path=Path(config_text) if config_text else None,
            dry_run=dry_run,
            human=action.human,
            output_path=Path(output_text) if output_text else None,
            email=self.email_var.get(),
            staging_dir=Path(staging_text) if staging_text else None,
            provider=self.provider_var.get(),
            account_alias=self.alias_var.get(),
            imap_host=self.imap_host_var.get(),
            imap_port=self.imap_port_var.get(),
            input_folder=self.input_folder_var.get(),
            done_folder=self.done_folder_var.get(),
            error_folder=self.error_folder_var.get(),
            enable_bucoliche=self.enable_bucoliche_var.get(),
            force=(action.key == "win11-install" or self.force_var.get()),
            interval_seconds=self.interval_var.get(),
            max_cycles=max_cycles,
            format_name=self.format_var.get(),
            python_exe=Path(python_text) if python_text else None,
            task_name=self.task_name_var.get(),
            backup=action.key == "maintenance-reset",
            confirm=(self.confirm_reset_var.get() or action.key == "win11-remove"),
        )

    def run_action(self, action: GuiAction) -> None:
        self._refresh_home_config()
        self._render_home()
        if not action.available:
            self.status_var.set("Azione non disponibile")
            self._set_output(action.unavailable_reason)
            return
        if action.destructive and not self._confirm(action):
            self.status_var.set("Azione annullata")
            return
        if action.key == "stop-watch":
            self.managed_runner.stop()
            self._poll_runner_events()
            return
        try:
            self._persist_runtime_settings()
            args = build_cli_args(self._spec_for_action(action))
        except ValueError as exc:
            self.status_var.set("Input non valido")
            self._set_output(f"Errore: {exc}")
            return

        self.status_var.set(f"Avvio: {action.label}")
        if not self.managed_runner.start(args):
            self._poll_runner_events()

    def _persist_runtime_settings(self) -> None:
        config_text = self.config_var.get().strip()
        local_data_text = self.local_data_var.get().strip()
        settings = GuiRuntimeSettings(
            local_data_dir=Path(local_data_text) if local_data_text else None,
            scanner=self.scanner_var.get(),
            interval_seconds=self.interval_var.get(),
            task_name=self.task_name_var.get(),
        )
        settings.validate()
        if config_text:
            GuiConfigService(
                Path(config_text), Path(config_text).with_name(".env.local")
            ).save_runtime_settings(settings)
        if settings.local_data_dir is not None:
            os.environ["VIRGILIO_LOCAL_DATA_DIR"] = str(settings.local_data_dir)
        os.environ["VIRGILIO_SCANNER"] = settings.scanner

    def _save_context_settings(self, tab: str) -> None:
        try:
            self._persist_runtime_settings()
            config_text = self.config_var.get().strip()
            if tab in {"Setup iniziale", "Bucoliche"} and config_text:
                service = GuiConfigService(
                    Path(config_text), Path(config_text).with_name(".env.local")
                )
                wizard = FirstRunWizard(service)
                limbo_text = self.staging_var.get().strip()
                if limbo_text:
                    wizard.set_folders(Path(limbo_text))
                wizard.set_bucoliche(self.enable_bucoliche_var.get())
                wizard.save()
            self.status_var.set("Impostazioni salvate")
        except (OSError, ValueError) as exc:
            self.status_var.set("Impostazioni non salvate")
            self._set_output(f"Correggi le impostazioni: {exc}")

    def _poll_runner_events(self) -> None:
        for event in self.managed_runner.drain_events():
            if event.message:
                self._set_output(event.message)
            labels = {
                "running": "Caronte attivo", "stopping": "Arresto in corso",
                "stopped": "Caronte fermo", "error": "Errore Caronte",
            }
            self.status_var.set(labels.get(event.state, event.state))
            self.home = self.home.apply(event, now=datetime.now(ROME),
                                        interval_seconds=self.interval_var.get())
            self._render_home()
            if event.kind in {"completed", "stopped", "error"}:
                self._refresh_activity()

    def _poll_runner(self) -> None:
        self._poll_runner_events()
        self.root.after(100, self._poll_runner)

    def _close(self) -> None:
        self.managed_runner.close()
        self.root.destroy()

    def _confirm(self, action: GuiAction) -> bool:
        from tkinter import messagebox

        if action.key == "maintenance-reset" and not self.confirm_reset_var.get():
            self._set_output("Per il reset seleziona prima 'Conferma reset'.")
            return False
        return messagebox.askyesno(
            "Conferma azione",
            f"Eseguire '{action.label}'? L'azione puo modificare lo stato locale.",
        )


def launch_gui(*, config_path: Path | None = None) -> int:
    import tkinter as tk

    if os.environ.get("DISPLAY") == "" and os.name != "nt":
        print("GUI non disponibile: ambiente grafico assente.")
        return 2
    root = tk.Tk()
    VirgilioGuiApp(root, initial_config=config_path)
    root.mainloop()
    return 0
