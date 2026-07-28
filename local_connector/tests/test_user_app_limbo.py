from pathlib import Path
from tkinter import Tk, ttk

from virgilio_connector.application.account_management import AccountManagementService
from virgilio_connector.application.configuration import ConfigurationService
from virgilio_connector.application.credentials import AccountCredentialService, FakeCredentialStore
from virgilio_connector.application.settings import SettingsService
from virgilio_connector.multi_account import scaffold_local_config
from virgilio_connector.user_app.settings import SettingsView
from virgilio_connector.user_app.text_controls import bind_text_interactions
from virgilio_connector.user_app.wizard import (
    AccountView,
    FirstRunController,
    LimboValidator,
    LimboView,
)

from test_user_app import FakeButton, FakeEntry, FakeLabel, FakeRoot, FakeTtk


class FakeStartup:
    def set_enabled(self, _enabled):
        return None


class FakeTextControl:
    def __init__(self):
        self.bindings = {}
        self.events = []
        self.selection = None
        self.cursor = None
        self.focused = False

    def bind(self, sequence, callback):
        self.bindings[sequence] = callback

    def event_generate(self, event):
        self.events.append(event)

    def selection_range(self, start, end):
        self.selection = (start, end)

    def icursor(self, index):
        self.cursor = index

    def focus_set(self):
        self.focused = True


class FakeMenu:
    def __init__(self, _parent, **_kwargs):
        self.commands = {}
        self.popup = None

    def add_command(self, *, label, command):
        self.commands[label] = command

    def add_separator(self):
        return None

    def tk_popup(self, x, y):
        self.popup = (x, y)


class PointerEvent:
    x_root = 10
    y_root = 20


def _configured_service(tmp_path: Path, limbo: Path) -> ConfigurationService:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        scaffold_local_config(
            email="account@example.invalid", staging_dir=limbo.resolve()
        ),
        encoding="utf-8",
    )
    return ConfigurationService.for_file(config_path)


def test_limbo_copy_identifies_the_synced_drive_folder_without_quarantine_fields(tmp_path):
    controller = FirstRunController(FakeRoot(), ttk_module=FakeTtk)
    controller.continue_forward()

    visible = " ".join(
        widget.kwargs.get("text", "")
        for kind in (FakeLabel, FakeButton)
        for widget in kind.created
    ).lower()

    assert "cartella del limbo drive sincronizzato" in visible
    assert "quarantena" not in visible
    assert "url" not in visible
    assert "id drive" not in visible


def test_folder_selector_and_validator_require_an_existing_absolute_directory(tmp_path):
    selected = tmp_path / "Limbo sincronizzato"
    selected.mkdir()
    view = LimboView(
        FakeRoot(),
        ttk_module=FakeTtk,
        on_back=lambda: None,
        on_continue=lambda: None,
        choose_folder=lambda: str(selected.resolve()),
    )

    view.select_folder()

    validator = LimboValidator()
    assert view.folder_value() == str(selected.resolve())
    assert validator.validate(view.folder_value()).is_valid
    assert not validator.validate("cartella-relativa").is_valid
    assert not validator.validate(str(tmp_path / "inesistente")).is_valid


def test_limbo_value_survives_back_navigation_and_reopening_configuration(tmp_path):
    limbo = tmp_path / "Limbo"
    limbo.mkdir()
    controller = FirstRunController(FakeRoot(), ttk_module=FakeTtk)
    controller.continue_forward()
    controller.current_view.folder_entry.set(str(limbo.resolve()))
    assert controller.continue_forward().is_valid
    controller.go_back()
    assert controller.current_view.folder_value() == str(limbo.resolve())

    configuration = _configured_service(tmp_path, limbo)
    accounts = AccountManagementService(
        configuration, AccountCredentialService(FakeCredentialStore())
    )
    reopened = FirstRunController(
        FakeRoot(), ttk_module=FakeTtk, account_service=accounts, open_existing=True
    )
    reopened.go_back()
    assert reopened.current_view.folder_value() == str(limbo.resolve())


def test_settings_folder_selector_persists_and_reloads_the_limbo(tmp_path):
    original = tmp_path / "Limbo iniziale"
    selected = tmp_path / "Limbo scelto"
    original.mkdir()
    selected.mkdir()
    service = SettingsService(_configured_service(tmp_path, original), FakeStartup())
    view = SettingsView(
        FakeRoot(),
        service,
        ttk_module=FakeTtk,
        go_home=lambda: None,
        on_saved=lambda _interval, _minimize: None,
        choose_folder=lambda: str(selected.resolve()),
    )

    view.select_limbo()
    assert view.save().is_valid
    reopened = SettingsView(
        FakeRoot(), service, ttk_module=FakeTtk,
        go_home=lambda: None, on_saved=lambda _interval, _minimize: None,
    )
    assert reopened.limbo_entry.get() == str(selected.resolve())


def test_text_controls_offer_keyboard_and_windows_context_menu_actions():
    control = FakeTextControl()
    bind_text_interactions(control, menu_factory=FakeMenu)

    assert {"<Control-a>", "<Control-x>", "<Control-c>", "<Control-v>", "<Button-3>"} <= set(control.bindings)
    assert control.bindings["<Control-a>"]() == "break"
    assert control.selection == (0, "end")
    menu = control._caronte_context_menu
    menu.commands["Copia"]()
    menu.commands["Incolla"]()
    assert control.events == ["<<Copy>>", "<<Paste>>"]
    assert control.bindings["<Button-3>"](PointerEvent()) == "break"
    assert control.focused and menu.popup == (10, 20)


def test_folder_fields_request_readable_width_and_use_expanding_columns(tmp_path):
    controller = FirstRunController(FakeRoot(), ttk_module=FakeTtk)
    controller.continue_forward()
    limbo = controller.current_view

    assert limbo.folder_entry.kwargs["width"] >= 48
    assert limbo.frame.column_options[0]["weight"] == 1

    controller.current_view.folder_entry.set(str(tmp_path.resolve()))
    controller.continue_forward()
    accounts = controller.current_view
    assert all(
        entry.kwargs["width"] >= 48
        for entry in (accounts.input_folder_entry, accounts.error_folder_entry)
    )
    assert accounts.advanced_frame.column_options[1]["weight"] == 1

    limbo_dir = tmp_path / "limbo"
    limbo_dir.mkdir()
    settings = SettingsView(
        FakeRoot(),
        SettingsService(_configured_service(tmp_path, limbo_dir), FakeStartup()),
        ttk_module=FakeTtk,
        go_home=lambda: None,
        on_saved=lambda _interval, _minimize: None,
    )
    assert settings.limbo_entry.kwargs["width"] >= 48
    assert settings.frame.column_options[1]["weight"] == 1


def test_real_folder_fields_fit_and_scroll_at_supported_scales(tmp_path):
    root = Tk()
    root.withdraw()
    root.geometry("960x640")
    original_scale = float(root.tk.call("tk", "scaling"))
    root.tk.call("tk", "scaling", 1.0)
    container = ttk.Frame(root)
    container.pack(fill="both", expand=True)
    try:
        views = [
            LimboView(
                container,
                ttk_module=ttk,
                on_back=lambda: None,
                on_continue=lambda: None,
            ),
            AccountView(
                container,
                ttk_module=ttk,
                on_back=lambda: None,
                on_continue=lambda: None,
                on_test=lambda: None,
                on_update=lambda: None,
                on_remove=lambda: None,
                on_select=lambda: None,
            ),
        ]
        limbo_dir = tmp_path / "limbo-real"
        limbo_dir.mkdir()
        views.append(
            SettingsView(
                container,
                SettingsService(
                    _configured_service(tmp_path, limbo_dir), FakeStartup()
                ),
                ttk_module=ttk,
                go_home=lambda: None,
                on_saved=lambda _interval, _minimize: None,
            )
        )

        for view in views:
            view.frame.grid(row=0, column=0, sticky="nsew")
            entries = (
                (view.input_folder_entry, view.error_folder_entry)
                if isinstance(view, AccountView)
                else (
                    view.folder_entry
                    if isinstance(view, LimboView)
                    else view.limbo_entry,
                )
            )
            for scale in (1.0, 1.25):
                root.tk.call("tk", "scaling", scale)
                root.update_idletasks()
                assert all(int(entry.cget("width")) >= 48 for entry in entries)
                assert root.winfo_reqwidth() <= 960
                assert root.winfo_reqheight() <= 640
            long_value = "C:\\" + "\\".join(["cartella-molto-lunga"] * 12)
            entry = entries[0]
            entry.delete(0, "end")
            entry.insert(0, long_value)
            entry.icursor("end")
            entry.xview_moveto(1.0)
            root.update_idletasks()
            assert entry.xview()[0] > 0
            view.frame.grid_remove()
    finally:
        root.tk.call("tk", "scaling", original_scale)
        root.destroy()
