from datetime import datetime
import threading
import time

from virgilio_connector.application.configuration import ConfigurationService
from virgilio_connector.application.home_control import HomeFeedback, HomeRunController
from virgilio_connector.application.operation_runner import RunnerEvent
from virgilio_connector.user_app.app import UserAppShell
from virgilio_connector.user_app.wizard import AccountForm, FirstRunController

from test_user_app import FakeLabel, FakeRoot, FakeTtk


class FakeRunner:
    def __init__(self):
        self.state = "stopped"
        self.events = []
        self.commands = []

    @property
    def running(self):
        return self.state in {"starting", "running", "stopping"}

    def start(self, args):
        if self.running:
            self.events.append(RunnerEvent("rejected", self.state, "raw rejected"))
            return False
        self.commands.append(args)
        self.state = "starting"
        return True

    def stop(self):
        if not self.running:
            self.events.append(RunnerEvent("rejected", self.state, "raw stopped"))
            return False
        self.state = "stopping"
        return True

    def close(self):
        self.state = "stopped"

    def drain_events(self):
        events, self.events = self.events, []
        return events


def _wait_for_connection(controller):
    deadline = time.monotonic() + 1
    while time.monotonic() < deadline:
        result = controller.poll_account_connection()
        if result is not None:
            return result
        time.sleep(0.005)
    raise AssertionError("connection feedback not produced")


def _account_form():
    return AccountForm("Principale", "person@example.invalid", "synthetic-password", True)


def test_connection_check_shows_immediate_progress_then_success_without_blocking(tmp_path):
    release = threading.Event()

    def slow_success(_form):
        release.wait(1)
        return "Collegamento riuscito: 2 messaggi visibili."

    controller = FirstRunController(FakeRoot(), ttk_module=FakeTtk, readonly_test=slow_success)
    controller.continue_forward()
    controller.current_view.folder_entry.set(str(tmp_path))
    controller.continue_forward()
    view = controller.current_view
    view.name_entry.set(_account_form().name)
    view.email_entry.set(_account_form().email)
    view.password_entry.set(_account_form().password)

    started = controller.test_account_connection()

    assert started.message == "Verifica avviata per la casella selezionata."
    assert controller.poll_account_connection() is None
    release.set()
    completed = _wait_for_connection(controller)
    assert completed.is_valid is True
    assert view.message.config["text"] == "Collegamento riuscito: 2 messaggi visibili."


def test_connection_authentication_failure_is_actionable_and_redacted():
    def rejected(_form):
        raise RuntimeError("LOGIN failed password=do-not-show C:\\private\\config.yaml")

    controller = FirstRunController(FakeRoot(), ttk_module=FakeTtk, readonly_test=rejected)
    controller._connection_check.start(_account_form())
    result = _wait_for_connection(controller)

    assert result.is_valid is False
    assert result.message == "Accesso rifiutato. Controlla le credenziali della casella e riprova."
    assert "do-not-show" not in result.message and "C:\\" not in result.message


def test_check_now_reports_acceptance_and_final_result():
    runner = FakeRunner()
    controller = HomeRunController("config.yaml", runner)

    assert controller.check_now() is True
    accepted = controller.drain_feedback()
    assert accepted == [HomeFeedback("Controllo in corso", "Controllo richiesto. Attendi il risultato.")]

    runner.state = "stopped"
    runner.events.append(RunnerEvent("completed", "stopped", "password=do-not-show", 0))
    completed = controller.drain_feedback()[0]
    assert completed.state == "Pronto"
    assert completed.refresh_activity is True
    assert completed.last_check is not None
    assert completed.message.startswith("Controllo completato.")
    assert "do-not-show" not in completed.message


def test_start_double_start_and_pause_have_visible_coherent_feedback():
    runner = FakeRunner()
    controller = HomeRunController("config.yaml", runner)

    assert controller.start() is True
    assert controller.drain_feedback()[0].message.startswith("Avvio richiesto")
    runner.state = "running"
    assert controller.start() is False
    rejected = controller.drain_feedback()[0]
    assert rejected.state == "Controllo in corso"
    assert "gia` in corso" in rejected.message

    assert controller.pause() is True
    pause_requested = controller.drain_feedback()[0]
    assert pause_requested.state == "In pausa"
    runner.state = "stopped"
    runner.events.append(RunnerEvent("stopped", "stopped", "", -15))
    assert controller.drain_feedback()[0].message == "Caronte e` in pausa."


class QueuedHomeControl:
    def __init__(self, feedback):
        self.feedback = list(feedback)

    def check_now(self): return True
    def start(self): return True
    def pause(self): return True
    def close(self): return None
    def set_interval_seconds(self, value): return None

    def drain_feedback(self):
        items, self.feedback = self.feedback, []
        return items


class ActivityRows:
    def list_activities(self):
        return (object(), object(), object())


class ScheduledRoot(FakeRoot):
    def __init__(self):
        super().__init__()
        self.scheduled = []

    def after(self, delay, callback):
        self.scheduled.append((delay, callback))


def test_home_poll_updates_state_last_check_and_activity_count(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("present: true\n", encoding="utf-8")
    completed_at = datetime.fromisoformat("2026-07-17T09:30:00+02:00")
    control = QueuedHomeControl((HomeFeedback(
        "Pronto", "Controllo completato.", completed_at, True
    ),))
    shell = UserAppShell(
        FakeRoot(), ConfigurationService.for_file(config), ttk_module=FakeTtk,
        home_control=control, activity_service=ActivityRows(),
    )

    assert shell.poll_home_operations() == 1
    visible = " ".join(label.config.get("text", "") for label in FakeLabel.created)
    assert "Stato generale: Pronto" in visible
    assert "Ultimo controllo: 17/07/2026 09:30" in visible
    assert "Attivita aggiornate: 3" in visible


def test_home_schedules_periodic_non_blocking_event_consumption(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("present: true\n", encoding="utf-8")
    root = ScheduledRoot()
    control = QueuedHomeControl((HomeFeedback("Controllo in corso", "Controllo avviato."),))
    shell = UserAppShell(
        root, ConfigurationService.for_file(config), ttk_module=FakeTtk,
        home_control=control,
    )

    assert root.scheduled[0][0] == 100
    root.scheduled.pop(0)[1]()

    assert shell.home.status.state == "Controllo in corso"
    assert root.scheduled[0][0] == 100


def test_runner_error_never_exposes_installed_runtime_details_or_credentials():
    runner = FakeRunner()
    controller = HomeRunController("C:\\repository\\secret.yaml", runner)
    controller.check_now()
    controller.drain_feedback()
    runner.state = "error"
    runner.events.append(RunnerEvent(
        "error", "error", "python stack trace password=do-not-show C:\\repository", 1
    ))

    feedback = controller.drain_feedback()[0]
    visible = feedback.message.casefold()
    assert feedback.state == "Richiede attenzione"
    assert "riprova" in visible
    assert all(term not in visible for term in (
        "python", "stack trace", "password", "do-not-show", "repository", "yaml"
    ))
