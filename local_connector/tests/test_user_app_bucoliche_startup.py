from pathlib import Path
from tkinter import Tk

from virgilio_connector.bucoliche import BucolicheError
from virgilio_connector.application.bucoliche_startup import (
    BucolicheStartupService,
    GuidedStatus,
)
from virgilio_connector.application.configuration import ConfigurationService
from virgilio_connector.application.credentials import FakeCredentialStore
from virgilio_connector.application.operational_connection import OperationalConnectionService
from virgilio_connector.application.registry_configuration import RegistryConfigurationService
from virgilio_connector.multi_account import scaffold_local_config
from virgilio_connector.user_app.app import UserAppShell
from virgilio_connector.user_app.navigation import UserRoute

from test_user_app import FakeButton, FakeLabel, FakeRoot, FakeTtk


class FakeBucolicheGateway:
    def __init__(self, connect=GuidedStatus(True, "Collegamento Google completato."),
                 verify=GuidedStatus(True, "Registro verificato e pronto.")):
        self.connect_result = connect
        self.verify_result = verify
        self.calls = []

    def connect_google(self):
        self.calls.append("connect")
        return self.connect_result

    def verify_register(self):
        self.calls.append("verify")
        return self.verify_result


class FailingBucolicheGateway:
    def connect_google(self):
        raise BucolicheError("internal connection detail")

    def verify_register(self):
        raise OSError("internal read detail")


class FakeAutomaticControl:
    def __init__(self, installed=False):
        self.installed = installed
        self.calls = []

    def is_installed(self):
        self.calls.append("status")
        return self.installed

    def install(self):
        self.calls.append("install")
        self.installed = True

    def remove(self):
        self.calls.append("remove")
        self.installed = False


def _configuration(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text(
        scaffold_local_config(
            email="utente@example.invalid",
            staging_dir=(tmp_path / "limbo").resolve(),
            bucoliche_enabled=False,
        ),
        encoding="utf-8",
    )
    return ConfigurationService.for_file(path)


def _service(tmp_path, *, installed=False, bucoliche=None, configured=True):
    configuration = _configuration(tmp_path)
    if configured:
        RegistryConfigurationService(configuration.store.source).select_register(
            "abcDEFGhijklmNOPQRST_uvwx"
        )
    google = bucoliche or FakeBucolicheGateway()
    automatic = FakeAutomaticControl(installed)
    connection = OperationalConnectionService(
        configuration.store.source, FakeCredentialStore()
    )
    return (
        configuration,
        BucolicheStartupService(configuration, google, automatic, connection),
        google,
        automatic,
    )


def test_register_is_always_present_and_reports_administrative_configuration(tmp_path):
    configuration, service, google, automatic = _service(tmp_path, configured=False)

    snapshot = service.load()

    assert snapshot.register_configured is False
    assert snapshot.register_message == "Registro non ancora configurato dall'amministratore."
    assert snapshot.automatic_control_message == "Controllo automatico non attivo."
    assert service.install_automatic_control() == GuidedStatus(
        True, "Controllo automatico attivato."
    )
    assert automatic.installed is True
    assert service.connect_google() == GuidedStatus(
        False, "Registro non ancora configurato dall'amministratore. Chiedi di configurarlo."
    )
    assert google.calls == []

    shell = UserAppShell(
        FakeRoot(), configuration, ttk_module=FakeTtk,
        bucoliche_startup_service=service,
    )
    shell.show_bucoliche_startup()
    visible = " ".join(widget.kwargs.get("text", "") for widget in FakeLabel.created)
    assert "Apri Caronte Manutenzione" in visible
    assert "configurazione iniziale" in visible
    assert shell.bucoliche_startup.registry_action is None


def test_google_connection_is_a_guided_step_using_only_the_injected_adapter(tmp_path):
    _, service, google, _ = _service(tmp_path)

    result = service.connect_google()

    assert result == GuidedStatus(True, "Collegamento Google completato.")
    assert google.calls == ["connect"]


def test_register_verification_is_read_only_through_the_injected_adapter(tmp_path):
    _, service, google, _ = _service(tmp_path)
    before = service.configuration.store.source.read_bytes()

    result = service.verify_register()

    assert result == GuidedStatus(True, "Registro verificato e pronto.")
    assert google.calls == ["verify"]
    assert service.configuration.store.source.read_bytes() == before


def test_known_connection_errors_are_translated_without_internal_details(tmp_path):
    _, service, _, _ = _service(tmp_path, bucoliche=FailingBucolicheGateway())

    connection = service.connect_google()
    register = service.verify_register()

    assert connection == GuidedStatus(False, "Collegamento Google non completato. Riprova.")
    assert register == GuidedStatus(
        False, "Registro non pronto. Completa prima il collegamento Google."
    )


def test_google_configuration_problem_has_a_guided_message(tmp_path):
    unavailable = FakeBucolicheGateway(
        connect=GuidedStatus(
            False,
            "Collegamento Google non disponibile. Chiedi all'amministratore di completare la configurazione di Caronte.",
        )
    )
    _, service, _, _ = _service(tmp_path, bucoliche=unavailable)

    result = service.connect_google()

    assert result.ok is False
    assert "amministratore" in result.message
    assert all(term not in result.message.lower() for term in ("file", "oauth", "path", "json"))


def test_automatic_control_install_remove_and_status_use_fake_scheduler(tmp_path):
    _, service, _, automatic = _service(tmp_path)

    assert service.load().automatic_control_message == "Controllo automatico non attivo."
    assert service.install_automatic_control() == GuidedStatus(
        True, "Controllo automatico attivato."
    )
    assert service.load().automatic_control_installed is True
    assert service.remove_automatic_control() == GuidedStatus(
        True, "Controllo automatico rimosso."
    )
    assert automatic.calls == ["status", "install", "status", "remove"]


def test_guided_view_offers_one_automatic_control_action_at_a_time(tmp_path):
    configuration, service, _, automatic = _service(tmp_path)
    shell = UserAppShell(
        FakeRoot(), configuration, ttk_module=FakeTtk,
        bucoliche_startup_service=service,
    )
    shell.show_bucoliche_startup()
    view = shell.bucoliche_startup

    assert view.automatic_message.config["text"] == "Controllo automatico non attivo."
    assert view.automatic_action.config["text"] == "Attiva controllo automatico"
    assert view.toggle_automatic_control().ok is True
    assert automatic.installed is True
    assert view.automatic_action.config["text"] == "Disattiva controllo automatico"
    assert view.toggle_automatic_control().ok is True
    assert automatic.installed is False


def test_guided_view_shows_clear_steps_and_known_error_messages(tmp_path):
    failed = FakeBucolicheGateway(
        connect=GuidedStatus(False, "Collegamento non completato. Controlla il file Google scelto."),
        verify=GuidedStatus(False, "Registro non pronto. Completa prima il collegamento Google."),
    )
    configuration, service, _, automatic = _service(tmp_path, bucoliche=failed)
    shell = UserAppShell(
        FakeRoot(), configuration, ttk_module=FakeTtk,
        bucoliche_startup_service=service,
    )

    shell.show_bucoliche_startup()
    assert shell.route is UserRoute.BUCOLICHE_STARTUP
    view = shell.bucoliche_startup
    assert view.connect_google().ok is False
    assert "Riprova" in view.registry_status.config["text"]
    assert view.verify_register().ok is False
    assert "Completa prima" in view.registry_status.config["text"]
    assert view.install().ok and automatic.installed
    assert view.remove().ok and not automatic.installed

    visible = " ".join(
        widget.kwargs.get("text", "")
        for kind in (FakeLabel, FakeButton)
        for widget in kind.created
    ).lower()
    assert "registro delle attivita" in visible
    assert "collega il tuo account google per aggiornare il registro" in visible
    forbidden = {
        "python", "venv", "cli", "yaml", ".env", "doctor", "pilot", "dry-run",
        "watch", "staging", "ack", "manifest", "sqlite", "exit code",
        "account_alias", "username_env", "password_env", "stack trace",
        "percorso del repository",
    }
    assert all(term not in visible for term in forbidden)
    assert "bucoliche" not in visible


def test_guided_view_hides_administrative_fields_and_opens_maintenance(tmp_path):
    configuration, service, _, _ = _service(tmp_path, configured=False)
    calls = []
    shell = UserAppShell(
        FakeRoot(), configuration, ttk_module=FakeTtk,
        bucoliche_startup_service=service,
        open_maintenance=lambda: calls.append("opened") or True,
    )
    shell.show_bucoliche_startup()
    view = shell.bucoliche_startup

    assert view.maintenance_action.config["text"] == "Apri Caronte Manutenzione"
    assert view.open_maintenance() is True
    assert calls == ["opened"]

    visible = " ".join(
        widget.kwargs.get("text", "")
        for kind in (FakeLabel, FakeButton)
        for widget in kind.created
    ).lower()
    assert "indirizzo di collegamento" not in visible
    assert "codice di collegamento" not in visible
    assert "salva collegamento" not in visible
    assert "chiedi all'amministratore" not in visible
    assert "configurazione iniziale" in visible


def test_guided_view_reports_when_maintenance_cannot_be_opened(tmp_path):
    configuration, service, _, _ = _service(tmp_path, configured=False)
    shell = UserAppShell(
        FakeRoot(), configuration, ttk_module=FakeTtk,
        bucoliche_startup_service=service,
        open_maintenance=lambda: False,
    )
    shell.show_bucoliche_startup()

    assert shell.bucoliche_startup.open_maintenance() is False
    assert "Non e` stato possibile" in shell.bucoliche_startup.connection_message.config["text"]


def test_registry_and_connection_view_fits_real_tk_at_supported_scales(tmp_path):
    configuration, service, _, _ = _service(tmp_path)
    root = Tk()
    root.withdraw()
    try:
        root.geometry("960x640")
        shell = UserAppShell(
            root, configuration, bucoliche_startup_service=service,
        )
        shell.show_bucoliche_startup()
        for scale in (1.0, 1.25):
            root.tk.call("tk", "scaling", scale)
            root.update_idletasks()
            assert root.winfo_reqwidth() <= 960
            assert root.winfo_reqheight() <= 640
            assert shell.bucoliche_startup.maintenance_action.winfo_viewable() in {0, 1}
    finally:
        root.destroy()
