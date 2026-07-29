"""Small, user-facing build identity window for Caronte."""

from __future__ import annotations

from tkinter import Toplevel, ttk
from typing import Any, Callable

from ..build_info import BuildInfo, load_build_info


ABOUT_TITLE = "Informazioni su Caronte"


def visible_build_information(info: BuildInfo) -> tuple[tuple[str, str], ...]:
    return (
        ("Versione", info.version),
        ("Commit", info.git_short_commit),
        ("Data della build", info.build_utc),
        ("Build ID", info.build_id),
    )


def show_about_dialog(
    parent: Any,
    *,
    info: BuildInfo | None = None,
    ttk_module: Any = ttk,
    toplevel_factory: Callable[[Any], Any] = Toplevel,
) -> Any:
    build = info or load_build_info()
    window = toplevel_factory(parent)
    window.title(ABOUT_TITLE)
    window.resizable(False, False)
    frame = ttk_module.Frame(window, padding=24)
    frame.grid(row=0, column=0, sticky="nsew")
    ttk_module.Label(frame, text=ABOUT_TITLE).grid(row=0, column=0, columnspan=2, sticky="w")
    for row, (label, value) in enumerate(visible_build_information(build), start=1):
        ttk_module.Label(frame, text=label).grid(row=row, column=0, padx=(0, 16), pady=4, sticky="w")
        ttk_module.Label(frame, text=value).grid(row=row, column=1, pady=4, sticky="w")
    ttk_module.Button(frame, text="Chiudi", command=window.destroy).grid(
        row=6, column=1, pady=(16, 0), sticky="e"
    )
    return window
