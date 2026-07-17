from pathlib import Path

import pytest

from virgilio_connector.application.configuration import ConfigurationService
from virgilio_connector.application.settings import SettingsService, SettingsValidationError
from virgilio_connector.application.windows_startup import WindowsStartupAdapter
from virgilio_connector.multi_account import scaffold_local_config
from virgilio_connector.user_app.app import UserAppShell
from virgilio_connector.user_app.navigation import UserRoute

from test_user_app import FakeButton, FakeEntry, FakeLabel, FakeRoot, FakeTtk


class FakeStartupAdapter:
    def __init__(self):
        self.values = []

    def set_enabled(self, enabled):
        self.values.append(enabled)


class FakeRegistryKey:
    def __enter__(self): return self
    def __exit__(self, *args): return None


class FakeRegistry:
    HKEY_CURRENT_USER = object()
    KEY_SET_VALUE = 1
    REG_SZ = 1

    def __init__(self):
        self.saved = {}

    def CreateKeyEx(self, *args): return FakeRegistryKey()
    def SetValueEx(self, key, name, reserved, kind, value): self.saved[name] = value
    def DeleteValue(self, key, name):
        if name not in self.saved: raise FileNotFoundError
        del self.saved[name]


class FakeHomeControl:
    def __init__(self):
        self.interval_seconds = None
        self.closed = False

    def check_now(self): return True
    def start(self): return True
    def pause(self): return True
    def set_interval_seconds(self, value): self.interval_seconds = value
    def close(self): self.closed = True


def _configuration(tmp_path: Path) -> ConfigurationService:
    path = tmp_path / "config.yaml"
    path.write_text(
        scaffold_local_config(
            email="account@example.invalid", staging_dir=(tmp_path / "old-limbo").resolve()
        ),
        encoding="utf-8",
    )
    return ConfigurationService.for_file(path)


def test_limbo_interval_and_preferences_round_trip_through_shared_model(tmp_path):
    configuration = _configuration(tmp_path)
    startup = FakeStartupAdapter()
    service = SettingsService(configuration, startup)
    new_limbo = (tmp_path / "nuovo limbo").resolve()
    new_limbo.mkdir()

    saved = service.save(
        limbo=str(new_limbo),
        interval_minutes="12",
        start_with_windows=True,
        minimize_on_close=True,
    )

    loaded = configuration.load()
    assert saved.limbo == new_limbo
    assert loaded.storage.staging_dir == new_limbo
    assert (
        loaded.preferences.interval_seconds,
        loaded.preferences.start_with_windows,
        loaded.preferences.minimize_on_close,
    ) == (720, True, True)
    assert service.load() == saved
    assert startup.values == [True]


def test_windows_startup_adapter_uses_injected_registry_without_real_access(tmp_path):
    registry = FakeRegistry()
    adapter = WindowsStartupAdapter(tmp_path / "config.yaml", registry=registry)

    adapter.set_enabled(True)
    assert "Caronte" in registry.saved
    assert "user-gui" in registry.saved["Caronte"]
    adapter.set_enabled(False)
    assert registry.saved == {}


@pytest.mark.parametrize("value", ("", "zero", "0", "1441"))
def test_interval_validation_rejects_values_outside_allowed_range(tmp_path, value):
    service = SettingsService(_configuration(tmp_path), FakeStartupAdapter())

    with pytest.raises(SettingsValidationError):
        service.save(
            limbo=str((tmp_path / "limbo").resolve()),
            interval_minutes=value,
            start_with_windows=False,
            minimize_on_close=False,
        )


def test_settings_view_saves_preferences_and_updates_close_behavior(tmp_path):
    configuration = _configuration(tmp_path)
    startup = FakeStartupAdapter()
    control = FakeHomeControl()
    root = FakeRoot()
    shell = UserAppShell(
        root,
        configuration,
        ttk_module=FakeTtk,
        home_control=control,
        settings_service=SettingsService(configuration, startup),
    )

    shell.show_settings()
    assert shell.route is UserRoute.SETTINGS
    selected_limbo = (tmp_path / "limbo scelto").resolve()
    selected_limbo.mkdir()
    shell.settings.limbo_entry.set(str(selected_limbo))
    shell.settings.interval_entry.set("7")
    shell.settings.toggle_start_with_windows()
    shell.settings.toggle_minimize_on_close()
    assert shell.settings.save().is_valid
    assert control.interval_seconds == 420

    root.protocols["WM_DELETE_WINDOW"]()
    assert root.iconified is True
    assert root.destroyed is False
    shell.close()
    assert control.closed is True
    assert root.destroyed is True


def test_default_settings_view_hides_technical_parameters(tmp_path):
    shell = UserAppShell(
        FakeRoot(),
        _configuration(tmp_path),
        ttk_module=FakeTtk,
        settings_service=SettingsService(_configuration(tmp_path), FakeStartupAdapter()),
    )
    shell.show_settings()
    visible = " ".join(
        widget.kwargs.get("text", "")
        for kind in (FakeLabel, FakeButton)
        for widget in kind.created
    ).lower()
    forbidden = {
        "python", "venv", "cli", "yaml", ".env", "doctor", "pilot", "dry-run",
        "watch", "staging", "ack", "manifest", "sqlite", "exit code",
        "account_alias", "username_env", "password_env", "stack trace",
        "percorso del repository",
    }
    assert all(term not in visible for term in forbidden)
