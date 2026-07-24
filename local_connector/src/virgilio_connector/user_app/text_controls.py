"""Common Windows-style interactions for user-facing text controls."""

from __future__ import annotations

from typing import Any, Callable


FOLDER_ENTRY_WIDTH = 48


def bind_text_interactions(
    control: Any,
    *,
    menu_factory: Callable[..., Any] | None = None,
) -> None:
    """Enable selection, clipboard shortcuts and a right-click context menu."""

    def select_all(_event: Any = None) -> str:
        control.selection_range(0, "end")
        control.icursor("end")
        return "break"

    def virtual_event(name: str) -> Callable[[Any], str]:
        def dispatch(_event: Any = None) -> str:
            control.event_generate(name)
            return "break"

        return dispatch

    actions = (
        ("<Control-a>", select_all),
        ("<Control-A>", select_all),
        ("<Control-x>", virtual_event("<<Cut>>")),
        ("<Control-X>", virtual_event("<<Cut>>")),
        ("<Control-c>", virtual_event("<<Copy>>")),
        ("<Control-C>", virtual_event("<<Copy>>")),
        ("<Control-v>", virtual_event("<<Paste>>")),
        ("<Control-V>", virtual_event("<<Paste>>")),
    )
    for sequence, callback in actions:
        control.bind(sequence, callback)

    if menu_factory is None:
        if not hasattr(control, "tk"):
            return
        from tkinter import Menu

        menu_factory = Menu

    menu = menu_factory(control, tearoff=False)
    menu.add_command(label="Taglia", command=lambda: control.event_generate("<<Cut>>"))
    menu.add_command(label="Copia", command=lambda: control.event_generate("<<Copy>>"))
    menu.add_command(label="Incolla", command=lambda: control.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label="Seleziona tutto", command=select_all)

    def show_menu(event: Any) -> str:
        control.focus_set()
        menu.tk_popup(event.x_root, event.y_root)
        return "break"

    control.bind("<Button-3>", show_menu)
    control._caronte_context_menu = menu
