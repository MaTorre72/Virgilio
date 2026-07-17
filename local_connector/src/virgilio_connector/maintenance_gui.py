"""Independent presentation for the Caronte maintenance application."""

from __future__ import annotations

from pathlib import Path
from tkinter import ttk
from typing import Any

from .application.maintenance import MaintenanceService
from .application.registry_configuration import RegistryConfigurationService
from .application_paths import default_application_paths


WINDOW_TITLE = "Caronte Manutenzione"
MAINTENANCE_OPERATIONS = (
    "Registro condiviso", "Backup locale", "Verifica integrita`", "Report diagnostico",
    "Reset protetto",
)


class MaintenanceApp:
    """Present only the supported technical maintenance operations."""

    def __init__(
        self,
        root: Any,
        service: MaintenanceService,
        *,
        ttk_module: Any = ttk,
        registry_configuration: RegistryConfigurationService | None = None,
    ) -> None:
        self.root = root
        self.service = service
        self._ttk = ttk_module
        self.registry_configuration = registry_configuration
        self.reset_confirmed = False
        root.title(WINDOW_TITLE)
        root.minsize(680, 420)

        frame = ttk_module.Frame(root, padding=28)
        frame.grid(row=0, column=0, sticky="nsew")
        ttk_module.Label(frame, text="Strumenti tecnici di manutenzione").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        row_offset = 0
        if self.registry_configuration is not None:
            status = self.registry_configuration.load()
            ttk_module.Label(frame, text="Registro condiviso").grid(
                row=1, column=0, columnspan=2, sticky="w", pady=(0, 4)
            )
            ttk_module.Label(
                frame, text="Incolla l'indirizzo del foglio scelto per questa installazione."
            ).grid(row=2, column=0, columnspan=2, sticky="w")
            self.registry_entry = ttk_module.Entry(frame, width=64)
            self.registry_entry.grid(row=3, column=0, sticky="we", pady=(4, 4))
            if status.spreadsheet_id:
                self.registry_entry.insert(0, status.spreadsheet_id)
            ttk_module.Button(
                frame, text="Salva Registro", command=self.save_register
            ).grid(row=3, column=1, sticky="w", padx=(8, 0))
            self.registry_message = ttk_module.Label(frame, text=status.message)
            self.registry_message.grid(row=4, column=0, columnspan=2, sticky="w")
            row_offset = 4
        ttk_module.Button(frame, text="Crea backup", command=self.create_backup).grid(
            row=1 + row_offset, column=0, sticky="w", pady=4
        )
        ttk_module.Button(
            frame, text="Verifica integrita`", command=self.verify_integrity
        ).grid(row=2 + row_offset, column=0, sticky="w", pady=4)
        ttk_module.Button(
            frame, text="Crea report diagnostico", command=self.create_diagnostic_report
        ).grid(row=3 + row_offset, column=0, sticky="w", pady=4)
        self.confirm_control = ttk_module.Checkbutton(
            frame,
            text="Confermo il reset con backup automatico",
            command=self.toggle_reset_confirmation,
        )
        self.confirm_control.grid(row=4 + row_offset, column=0, sticky="w", pady=(16, 4))
        ttk_module.Button(frame, text="Esegui reset", command=self.reset).grid(
            row=5 + row_offset, column=0, sticky="w", pady=4
        )
        self.message = ttk_module.Label(frame, text="")
        self.message.grid(row=6 + row_offset, column=0, columnspan=2, sticky="w", pady=(16, 0))

    def save_register(self):
        if self.registry_configuration is None:
            return None
        result = self.registry_configuration.select_register(self.registry_entry.get())
        self.registry_message.configure(text=result.message)
        return result

    def create_backup(self):
        result = self.service.create_backup()
        self.message.configure(text=result.message)
        return result

    def verify_integrity(self):
        result = self.service.verify_integrity()
        self.message.configure(text=result.message)
        return result

    def create_diagnostic_report(self):
        result = self.service.create_diagnostic_report()
        self.message.configure(text=result.message)
        return result

    def toggle_reset_confirmation(self) -> None:
        self.reset_confirmed = not self.reset_confirmed
        self.confirm_control.state(("selected",) if self.reset_confirmed else ("!selected",))

    def reset(self):
        result = self.service.reset(confirmed=self.reset_confirmed)
        self.message.configure(text=result.message)
        if result.status != "cancelled":
            self.reset_confirmed = False
            self.confirm_control.state(("!selected",))
        return result


def launch_gui(*, config_path: Path | None = None) -> int:
    """Create and run the independent maintenance window."""

    from tkinter import Tk

    paths = default_application_paths()
    configuration_file = config_path or paths.configuration_file
    root = Tk()
    MaintenanceApp(
        root,
        MaintenanceService(paths.data_dir),
        registry_configuration=RegistryConfigurationService(configuration_file),
    )
    root.mainloop()
    return 0


__all__ = ["MaintenanceApp", "launch_gui"]
