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
        self._enabled = snapshot.bucoliche_enabled

        ttk_module.Label(self.frame, text="Bucoliche e controllo automatico").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        ttk_module.Label(self.frame, text="1. Scegli se usare il registro condiviso").grid(
            row=1, column=0, columnspan=2, sticky="w"
        )
        self.enabled_control = ttk_module.Checkbutton(
            self.frame, text="Usa Bucoliche", command=self.toggle_bucoliche
        )
        self.enabled_control.grid(row=2, column=0, sticky="w")
        self._sync_enabled()
        ttk_module.Label(self.frame, text="2. Collega il tuo account Google").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        ttk_module.Button(
            self.frame, text="Collega Google", command=self.connect_google
        ).grid(row=4, column=0, sticky="w")
        ttk_module.Label(self.frame, text="3. Controlla che il registro sia pronto").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        ttk_module.Button(
            self.frame, text="Verifica registro", command=self.verify_register
        ).grid(row=6, column=0, sticky="w")
        self.bucoliche_message = ttk_module.Label(self.frame, text="")
        self.bucoliche_message.grid(row=7, column=0, columnspan=2, sticky="w")

        ttk_module.Label(self.frame, text="Controllo automatico all'accesso a Windows").grid(
            row=8, column=0, columnspan=2, sticky="w", pady=(16, 0)
        )
        self.automatic_message = ttk_module.Label(
            self.frame, text=snapshot.automatic_control_message
        )
        self.automatic_message.grid(row=9, column=0, columnspan=2, sticky="w")
        ttk_module.Button(
            self.frame, text="Attiva controllo automatico", command=self.install
        ).grid(row=10, column=0, sticky="w")
        ttk_module.Button(
            self.frame, text="Rimuovi controllo automatico", command=self.remove
        ).grid(row=10, column=1, sticky="w")
        ttk_module.Button(self.frame, text="Torna alla Home", command=go_home).grid(
            row=11, column=0, sticky="w", pady=(16, 0)
        )

    def toggle_bucoliche(self) -> GuidedStatus:
        self._enabled = not self._enabled
        result = self.service.set_bucoliche_enabled(self._enabled)
        self._sync_enabled()
        self.bucoliche_message.configure(text=result.message)
        return result

    def connect_google(self) -> GuidedStatus:
        result = self.service.connect_google()
        self.bucoliche_message.configure(text=result.message)
        return result

    def verify_register(self) -> GuidedStatus:
        result = self.service.verify_register()
        self.bucoliche_message.configure(text=result.message)
        return result

    def install(self) -> GuidedStatus:
        result = self.service.install_automatic_control()
        self.automatic_message.configure(text=result.message)
        return result

    def remove(self) -> GuidedStatus:
        result = self.service.remove_automatic_control()
        self.automatic_message.configure(text=result.message)
        return result

    def _sync_enabled(self) -> None:
        self.enabled_control.state(("selected",) if self._enabled else ("!selected",))
