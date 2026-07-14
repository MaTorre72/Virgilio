from datetime import datetime

from virgilio_connector.gui_home import HomeSnapshot, ROME, format_home_time
from virgilio_connector.gui_runner import RunnerEvent


NOW = datetime(2026, 7, 14, 17, 30, tzinfo=ROME)


def test_home_without_configuration_and_active_accounts():
    empty = HomeSnapshot()
    assert empty.state == "Configurazione da completare"
    assert "configurazione" in empty.problem
    ready = empty.with_accounts(2)
    assert (ready.state, ready.active_accounts, ready.problem) == ("Pronto", 2, "")


def test_home_transitions_and_counters_for_success():
    home = HomeSnapshot().with_accounts(2)
    running = home.apply(RunnerEvent("started", "running"), now=NOW)
    done = running.apply(RunnerEvent("completed", "stopped", returncode=0),
                         now=NOW, interval_seconds=300)
    assert running.state == "Controllo in corso"
    assert (done.state, done.checks, done.completed, done.problems) == ("Pronto", 1, 1, 0)
    assert format_home_time(done.last_check) == "14/07/2026 17:30"
    assert format_home_time(done.next_check) == "14/07/2026 17:35"


def test_home_error_is_actionable_and_has_no_next_check():
    failed = HomeSnapshot().with_accounts(1).apply(
        RunnerEvent("completed", "error", "password=<redacted>", 2), now=NOW)
    assert (failed.state, failed.checks, failed.problems) == ("Richiede attenzione", 1, 1)
    assert failed.next_check is None
    assert failed.problem == "Il controllo non e` riuscito. Apri il report."
