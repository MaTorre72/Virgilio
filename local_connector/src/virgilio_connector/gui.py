"""Minimal local tkinter wrapper around the existing Virgilio CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys


@dataclass(frozen=True)
class GuiCommandSpec:
    command: str
    config_path: Path | None = None
    dry_run: bool = False
    human: bool = False
    output_path: Path | None = None
    email: str = ""
    staging_dir: Path | None = None


def build_cli_args(spec: GuiCommandSpec) -> list[str]:
    """Translate a GUI action into the existing CLI arguments."""

    if spec.command in {"doctor", "pilot"}:
        if spec.config_path is None:
            raise ValueError("config_path is required")
        args = [spec.command, "--config", str(spec.config_path)]
        if spec.command == "pilot" and spec.human:
            args.append("--human")
        return args
    if spec.command == "init-config":
        if spec.output_path is None:
            raise ValueError("output_path is required")
        if not spec.email.strip():
            raise ValueError("email is required")
        if spec.staging_dir is None:
            raise ValueError("staging_dir is required")
        args = [
            "init-config",
            "--output", str(spec.output_path),
            "--email", spec.email.strip(),
            "--staging-dir", str(spec.staging_dir),
        ]
        if spec.dry_run:
            args.append("--dry-run")
        return args
    raise ValueError(f"unsupported GUI command: {spec.command}")


def run_cli_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "virgilio_connector", *args],
        capture_output=True,
        text=True,
        check=False,
    )


class VirgilioGuiApp:
    """Small operator GUI that delegates execution to the CLI entrypoint."""

    def __init__(self, root, *, command_runner=run_cli_command, initial_config: Path | None = None):
        import tkinter as tk
        from tkinter import ttk

        self._tk = tk
        self._ttk = ttk
        self.root = root
        self.command_runner = command_runner

        root.title("Virgilio Local Connector")
        root.minsize(780, 520)

        self.command_var = tk.StringVar(value="doctor")
        self.config_var = tk.StringVar(value=str(initial_config) if initial_config else "")
        self.output_var = tk.StringVar(value="")
        self.email_var = tk.StringVar(value="")
        self.staging_var = tk.StringVar(value="")
        self.dry_run_var = tk.BooleanVar(value=True)
        self.human_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Pronto")

        self._build_layout()
        self._sync_form()

    def _build_layout(self) -> None:
        from tkinter import filedialog

        self._filedialog = filedialog
        root = self.root
        ttk = self._ttk

        frame = ttk.Frame(root, padding=12)
        frame.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(7, weight=1)

        ttk.Label(frame, text="Comando").grid(row=0, column=0, sticky="w", pady=(0, 8))
        command_box = ttk.Combobox(
            frame,
            textvariable=self.command_var,
            values=("doctor", "pilot", "init-config"),
            state="readonly",
        )
        command_box.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=(0, 8))
        command_box.bind("<<ComboboxSelected>>", lambda _event: self._sync_form())

        ttk.Label(frame, text="Config YAML").grid(row=1, column=0, sticky="w", pady=4)
        self.config_entry = ttk.Entry(frame, textvariable=self.config_var)
        self.config_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)
        ttk.Button(frame, text="Sfoglia...", command=self._browse_config).grid(
            row=1, column=2, sticky="ew", padx=(8, 0), pady=4
        )

        ttk.Label(frame, text="Output config").grid(row=2, column=0, sticky="w", pady=4)
        self.output_entry = ttk.Entry(frame, textvariable=self.output_var)
        self.output_entry.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=4)
        ttk.Button(frame, text="Salva come...", command=self._browse_output).grid(
            row=2, column=2, sticky="ew", padx=(8, 0), pady=4
        )

        ttk.Label(frame, text="Email account").grid(row=3, column=0, sticky="w", pady=4)
        self.email_entry = ttk.Entry(frame, textvariable=self.email_var)
        self.email_entry.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=4)

        ttk.Label(frame, text="Cartella staging").grid(row=4, column=0, sticky="w", pady=4)
        self.staging_entry = ttk.Entry(frame, textvariable=self.staging_var)
        self.staging_entry.grid(row=4, column=1, sticky="ew", padx=(8, 0), pady=4)
        ttk.Button(frame, text="Cartella...", command=self._browse_staging).grid(
            row=4, column=2, sticky="ew", padx=(8, 0), pady=4
        )

        self.dry_run_check = ttk.Checkbutton(frame, text="Dry-run", variable=self.dry_run_var)
        self.dry_run_check.grid(row=5, column=0, sticky="w", pady=(8, 4))
        self.human_check = ttk.Checkbutton(frame, text="Output umano", variable=self.human_var)
        self.human_check.grid(row=5, column=1, sticky="w", padx=(8, 0), pady=(8, 4))

        button_row = ttk.Frame(frame)
        button_row.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(8, 8))
        button_row.columnconfigure(0, weight=1)
        ttk.Label(button_row, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        ttk.Button(button_row, text="Esegui", command=self.run_selected_command).grid(
            row=0, column=1, sticky="e"
        )

        self.output_text = self._tk.Text(frame, wrap="word", height=18)
        self.output_text.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(4, 0))

    def _set_output(self, text: str) -> None:
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text.strip() or "(nessun output)")

    def _browse_config(self) -> None:
        path = self._filedialog.askopenfilename(
            title="Seleziona accounts.local.yaml",
            filetypes=[("YAML", "*.yaml *.yml"), ("Tutti i file", "*.*")],
        )
        if path:
            self.config_var.set(path)

    def _browse_output(self) -> None:
        path = self._filedialog.asksaveasfilename(
            title="Scrivi file di configurazione",
            defaultextension=".yaml",
            filetypes=[("YAML", "*.yaml"), ("Tutti i file", "*.*")],
        )
        if path:
            self.output_var.set(path)

    def _browse_staging(self) -> None:
        path = self._filedialog.askdirectory(title="Seleziona cartella staging")
        if path:
            self.staging_var.set(path)

    def _set_state(self, widget, enabled: bool) -> None:
        widget.configure(state=("normal" if enabled else "disabled"))

    def _sync_form(self) -> None:
        init_mode = self.command_var.get() == "init-config"
        runtime_mode = self.command_var.get() in {"doctor", "pilot"}

        self._set_state(self.config_entry, runtime_mode)
        self._set_state(self.output_entry, init_mode)
        self._set_state(self.email_entry, init_mode)
        self._set_state(self.staging_entry, init_mode)
        self._set_state(self.dry_run_check, init_mode)
        self._set_state(self.human_check, self.command_var.get() == "pilot")

    def run_selected_command(self) -> None:
        try:
            spec = GuiCommandSpec(
                command=self.command_var.get(),
                config_path=Path(self.config_var.get()) if self.config_var.get().strip() else None,
                dry_run=self.dry_run_var.get(),
                human=self.human_var.get(),
                output_path=Path(self.output_var.get()) if self.output_var.get().strip() else None,
                email=self.email_var.get(),
                staging_dir=Path(self.staging_var.get()) if self.staging_var.get().strip() else None,
            )
            args = build_cli_args(spec)
        except ValueError as exc:
            self.status_var.set("Input non valido")
            self._set_output(f"Errore: {exc}")
            return

        self.status_var.set(f"Esecuzione: {' '.join(args)}")
        self.root.update_idletasks()
        completed = self.command_runner(args)
        output = completed.stdout.strip()
        error = completed.stderr.strip()
        combined = output if not error else f"{output}\n\n{error}".strip()
        self._set_output(combined)
        self.status_var.set(f"Exit code: {completed.returncode}")


def launch_gui(*, config_path: Path | None = None) -> int:
    import tkinter as tk

    root = tk.Tk()
    VirgilioGuiApp(root, initial_config=config_path)
    root.mainloop()
    return 0
