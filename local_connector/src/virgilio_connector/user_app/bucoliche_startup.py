"""Guided Bucoliche and automatic-control user view."""

from __future__ import annotations

from typing import Any, Callable

from ..application.bucoliche_startup import BucolicheStartupService, GuidedStatus


class BucolicheStartupView:
    def __init__(
        self,
        parent: Any,
        service: BucolicheStartupService,
        *,
        ttk_module: Any,
        go_home: Callable[[], None],
    ) -> None:
        self.service = service
        self.frame = ttk_module.Frame(parent)
        self.frame.grid(row=0, column=0, sticky="nsew")
        snapshot = service.load()
        ttk_module.Label(self.frame, text="Registro delle attivita`").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        ttk_module.Label(
            self.frame, text="Il Registro e` sempre attivo per le attivita` di Caronte."
        ).grid(
            row=1, column=0, columnspan=2, sticky="w"
        )
        self.registry_status = ttk_module.Label(
            self.frame, text=snapshot.register_message
        )
        self.registry_status.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.registry_action = None
        if snapshot.register_configured:
            ttk_module.Label(
                self.frame, text="Collega il tuo account Google per aggiornare il Registro"
            ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(12, 0))
            self.registry_action = ttk_module.Button(
                self.frame, text="Collega Google", command=self.connect_google
            )
            self.registry_action.grid(row=4, column=0, sticky="w")
        else:
            ttk_module.Label(
                self.frame,
                text="Azione da fare: chiedi all'amministratore di configurare il Registro.",
            ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(12, 0))

        ttk_module.Label(self.frame, text="Collegamento a Virgilio").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(16, 0)
        )
        self.connection_message = ttk_module.Label(
            self.frame, text=snapshot.connection_message
        )
        self.connection_message.grid(row=6, column=0, columnspan=2, sticky="w")
        ttk_module.Label(self.frame, text="Indirizzo di collegamento").grid(
            row=7, column=0, sticky="w"
        )
        self.connection_endpoint = ttk_module.Entry(self.frame, width=48)
        self.connection_endpoint.grid(row=8, column=0, columnspan=2, sticky="ew")
        if snapshot.connection_endpoint:
            self.connection_endpoint.insert(0, snapshot.connection_endpoint)
        ttk_module.Label(self.frame, text="Codice di collegamento").grid(
            row=9, column=0, sticky="w"
        )
        self.connection_code = ttk_module.Entry(self.frame, show="*")
        self.connection_code.grid(row=10, column=0, sticky="ew")
        self.connection_action = ttk_module.Button(
            self.frame, text="Salva collegamento", command=self.save_connection
        )
        self.connection_action.grid(row=10, column=1, sticky="w")

        ttk_module.Label(self.frame, text="Controllo automatico all'accesso a Windows").grid(
            row=11, column=0, columnspan=2, sticky="w", pady=(16, 0)
        )
        self.automatic_message = ttk_module.Label(
            self.frame, text=snapshot.automatic_control_message
        )
        self.automatic_message.grid(row=12, column=0, columnspan=2, sticky="w")
        self.automatic_action = ttk_module.Button(
            self.frame,
            text=("Disattiva controllo automatico" if snapshot.automatic_control_installed
                  else "Attiva controllo automatico"),
            command=self.toggle_automatic_control,
        )
        self.automatic_action.grid(row=13, column=0, sticky="w")
        ttk_module.Button(self.frame, text="Torna alla Home", command=go_home).grid(
            row=14, column=0, sticky="w", pady=(16, 0)
        )

    def connect_google(self) -> GuidedStatus:
        result = self.service.connect_google()
        self.registry_status.configure(text=result.message)
        return result

    def verify_register(self) -> GuidedStatus:
        result = self.service.verify_register()
        self.registry_status.configure(text=result.message)
        return result

    def save_connection(self) -> GuidedStatus:
        result = self.service.configure_operational_connection(
            self.connection_endpoint.get(), self.connection_code.get()
        )
        self.connection_message.configure(text=result.message)
        if result.ok:
            self.connection_code.delete(0, "end")
        return result

    def toggle_automatic_control(self) -> GuidedStatus:
        if self.service.load().automatic_control_installed:
            return self.remove()
        return self.install()

    def install(self) -> GuidedStatus:
        result = self.service.install_automatic_control()
        self.automatic_message.configure(text=result.message)
        if result.ok:
            self.automatic_action.configure(text="Disattiva controllo automatico")
        return result

    def remove(self) -> GuidedStatus:
        result = self.service.remove_automatic_control()
        self.automatic_message.configure(text=result.message)
        if result.ok:
            self.automatic_action.configure(text="Attiva controllo automatico")
        return result
