from pathlib import Path

from virgilio_connector.bucoliche import BucolicheError
from virgilio_connector.application.bucoliche_startup import (
    BucolicheStartupService,
    GuidedStatus,
)
from virgilio_connector.application.configuration import ConfigurationService
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
    return configuration, BucolicheStartupService(configuration, google, automatic), google, automatic


def test_register_is_always_present_and_reports_administrative_configuration(tmp_path):
    _, service, _, _ = _service(tmp_path, configured=False)

    snapshot = service.load()

    assert snapshot.register_configured is False
    assert snapshot.register_message == "Registro non ancora configurato dall'amministratore."


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
    assert "Riprova" in view.bucoliche_message.config["text"]
    assert view.verify_register().ok is False
    assert "Completa prima" in view.bucoliche_message.config["text"]
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
