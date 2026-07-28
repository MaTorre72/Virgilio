"""User-facing activity and problems view."""

from __future__ import annotations

from typing import Any, Callable, Protocol

from ..application.activity import ActivityFilters, ActivityRow, filter_activities, parse_day


class ActivitySource(Protocol):
    def list_activities(self) -> tuple[ActivityRow, ...]: ...


class EmptyActivitySource:
    def list_activities(self) -> tuple[ActivityRow, ...]:
        return ()


class ActivityView:
    """Render activities, essential filters, and opt-in advanced detail."""

    COLUMNS = ("quando", "casella", "documento", "attivita", "esito", "azione")
    HEADINGS = ("Quando", "Casella", "Documento", "Attivita", "Esito", "Azione consigliata")

    def __init__(
        self,
        parent: Any,
        source: ActivitySource,
        *,
        ttk_module: Any,
        go_home: Callable[[], None] = lambda: None,
    ) -> None:
        self._ttk = ttk_module
        self._all_rows = source.list_activities()
        self._shown_rows: tuple[ActivityRow, ...] = ()
        self.technical_panel_open = False
        self.frame = ttk_module.Frame(parent)
        self.frame.grid(row=0, column=0, sticky="nsew")
        ttk_module.Label(self.frame, text="Attivita e problemi").grid(row=0, column=0, sticky="w")
        self.account_filter = self._filter(1, 0, "Filtra per casella")
        self.outcome_filter = self._filter(1, 1, "Filtra per esito")
        self.day_filter = self._filter(1, 2, "Data (gg/mm/aaaa)")
        ttk_module.Button(self.frame, text="Applica filtri", command=self.apply_filters).grid(
            row=2, column=3, sticky="w"
        )
        self.filter_message = ttk_module.Label(self.frame, text="")
        self.filter_message.grid(row=3, column=0, columnspan=4, sticky="w")
        self.table = ttk_module.Treeview(self.frame, columns=self.COLUMNS, show="headings")
        for column, heading in zip(self.COLUMNS, self.HEADINGS):
            self.table.heading(column, text=heading)
        self.table.grid(row=4, column=0, columnspan=4, sticky="nsew")
        self._replace_rows(self._all_rows)
        ttk_module.Button(
            self.frame, text="Mostra dettagli tecnici", command=self.toggle_technical_detail
        ).grid(row=5, column=0, sticky="w", pady=(12, 0))
        self.technical_label = ttk_module.Label(self.frame, text="")
        self.technical_label.grid(row=6, column=0, columnspan=4, sticky="w")
        self.technical_label.grid_remove()
        ttk_module.Button(self.frame, text="Torna alla Home", command=go_home).grid(
            row=7, column=0, sticky="w", pady=(12, 0)
        )

    def _filter(self, row: int, column: int, label: str) -> Any:
        box = self._ttk.Frame(self.frame)
        box.grid(row=row, column=column, sticky="w", padx=(0, 12))
        self._ttk.Label(box, text=label).grid(row=0, column=0, sticky="w")
        entry = self._ttk.Entry(box)
        entry.grid(row=1, column=0, sticky="w")
        return entry

    def apply_filters(self) -> None:
        try:
            day = parse_day(self.day_filter.get())
        except ValueError:
            self.filter_message.configure(text="Inserisci la data nel formato gg/mm/aaaa.")
            return
        self.filter_message.configure(text="")
        self._replace_rows(filter_activities(self._all_rows, ActivityFilters(
            account=self.account_filter.get(),
            outcome=self.outcome_filter.get(),
            day=day,
        )))

    def toggle_technical_detail(self) -> None:
        if self.technical_panel_open:
            self.technical_label.grid_remove()
            self.technical_panel_open = False
            return
        selected = self.table.selection()
        if not selected:
            self.filter_message.configure(text="Seleziona prima una riga.")
            return
        row = self._shown_rows[int(selected[0])]
        self.technical_label.configure(text=row.technical_detail)
        self.technical_label.grid(row=6, column=0, columnspan=4, sticky="w")
        self.technical_panel_open = True

    def _replace_rows(self, rows: tuple[ActivityRow, ...]) -> None:
        for item in self.table.get_children():
            self.table.delete(item)
        self._shown_rows = rows
        for index, row in enumerate(rows):
            self.table.insert("", "end", iid=str(index), values=row.visible_values)
