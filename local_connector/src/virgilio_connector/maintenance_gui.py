"""Independent presentation for the Caronte maintenance application."""

from __future__ import annotations

from pathlib import Path
from tkinter import ttk
from typing import Any

from .application.maintenance import MaintenanceService
from .application.credentials import CredentialStoreError
from .application.operational_connection import (
    OperationalConnectionService,
    create_operational_connection_service,
)
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
        operational_connection: OperationalConnectionService | None = None,
    ) -> None:
        self.root = root
        self.service = service
        self._ttk = ttk_module
        self.registry_configuration = registry_configuration
        self.operational_connection = operational_connection
        self.reset_confirmed = False
        root.title(WINDOW_TITLE)
        root.minsize(680, 420)

        frame = ttk_module.Frame(root, padding=28)
        frame.grid(row=0, column=0, sticky="nsew")
        ttk_module.Label(frame, text="Strumenti tecnici di manutenzione").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        row_offset = 0
        if self.registry_configuration is not None and self.operational_connection is not None:
            register = self.registry_configuration.load()
            connection = self.operational_connection.load()
            ttk_module.Label(frame, text="Configurazione dei servizi Virgilio").grid(
                row=1, column=0, columnspan=2, sticky="w", pady=(0, 4)
            )
            ttk_module.Label(
                frame,
                text=(
                    "Questi dati si impostano una sola volta. Sono destinati a chi "
                    "amministra Virgilio, non all'utente di Caronte."
                ),
                wraplength=700,
            ).grid(row=2, column=0, columnspan=2, sticky="w")
            ttk_module.Label(frame, text="Registro delle attivita` (Google Fogli)").grid(
                row=3, column=0, columnspan=2, sticky="w", pady=(10, 0)
            )
            ttk_module.Label(
                frame,
                text=(
                    "Apri il foglio condiviso scelto come Registro e copia qui "
                    "l'indirizzo mostrato dal browser."
                ),
                wraplength=700,
            ).grid(row=4, column=0, columnspan=2, sticky="w")
            self.registry_entry = ttk_module.Entry(frame, width=72)
            self.registry_entry.grid(row=5, column=0, columnspan=2, sticky="we")
            if register.spreadsheet_id:
                self.registry_entry.insert(0, register.spreadsheet_id)
            ttk_module.Label(frame, text="Indirizzo del servizio di consegna").grid(
                row=6, column=0, columnspan=2, sticky="w", pady=(10, 0)
            )
            ttk_module.Label(
                frame,
                text=(
                    "In Apps Script apri Gestisci deployment, seleziona l'App web "
                    "di Virgilio e copia l'indirizzo che termina con /exec."
                ),
                wraplength=700,
            ).grid(row=7, column=0, columnspan=2, sticky="w")
            self.connection_endpoint = ttk_module.Entry(frame, width=72)
            self.connection_endpoint.grid(row=8, column=0, columnspan=2, sticky="we")
            if connection.endpoint_url:
                self.connection_endpoint.insert(0, connection.endpoint_url)
            ttk_module.Label(frame, text="Chiave di accesso del servizio").grid(
                row=9, column=0, columnspan=2, sticky="w", pady=(10, 0)
            )
            ttk_module.Label(
                frame,
                text=(
                    "Usa il valore VIRGILIO_TOKEN salvato nelle proprieta` dello "
                    "script. La chiave viene protetta da Windows; se e` gia` "
                    "configurata, lascia il campo vuoto per mantenerla."
                ),
                wraplength=700,
            ).grid(row=10, column=0, columnspan=2, sticky="w")
            self.connection_code = ttk_module.Entry(frame, width=52, show="*")
            self.connection_code.grid(row=11, column=0, sticky="we")
            ttk_module.Button(
                frame, text="Salva configurazione Virgilio", command=self.save_services
            ).grid(row=11, column=1, sticky="w", padx=(8, 0))
            self.registry_message = ttk_module.Label(frame, text=register.message)
            self.registry_message.grid(row=12, column=0, columnspan=2, sticky="w")
            self.connection_message = ttk_module.Label(frame, text=connection.message)
            self.connection_message.grid(row=13, column=0, columnspan=2, sticky="w")
            row_offset = 13
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

    def save_services(self):
        if self.registry_configuration is None or self.operational_connection is None:
            return None
        register = self.registry_configuration.select_register(self.registry_entry.get())
        self.registry_message.configure(text=register.message)
        if not register.configured:
            return register
        try:
            connection = self.operational_connection.configure(
                self.connection_endpoint.get(), self.connection_code.get()
            )
        except (ValueError, CredentialStoreError, OSError) as exc:
            self.connection_message.configure(text=str(exc))
            return register
        self.connection_message.configure(text=connection.message)
        self.connection_code.delete(0, "end")
        return register

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
        operational_connection=create_operational_connection_service(configuration_file),
    )
    root.mainloop()
    return 0


__all__ = ["MaintenanceApp", "launch_gui"]
