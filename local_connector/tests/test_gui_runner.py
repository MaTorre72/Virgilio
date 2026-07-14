import subprocess
import threading
import time

from virgilio_connector.gui_runner import ManagedCliRunner


class FakeProcess:
    def __init__(self, *, output="ok", returncode=0, slow=False, ignore_terminate=False):
        self.output = output
        self.returncode = None
        self.final_returncode = returncode
        self.slow = slow
        self.ignore_terminate = ignore_terminate
        self.released = threading.Event()
        self.terminated = False
        self.killed = False

    def communicate(self):
        if self.slow:
            self.released.wait(2)
        if self.returncode is None:
            self.returncode = self.final_returncode
        return self.output, ""

    def terminate(self):
        self.terminated = True
        if not self.ignore_terminate:
            self.returncode = -15
            self.released.set()

    def kill(self):
        self.killed = True
        self.returncode = -9
        self.released.set()

    def wait(self, timeout=None):
        if not self.released.wait(timeout):
            raise subprocess.TimeoutExpired("fake", timeout)
        return self.returncode


def wait_for(runner, state):
    deadline = time.monotonic() + 2
    while runner.state != state and time.monotonic() < deadline:
        time.sleep(.005)
    assert runner.state == state


def test_start_complete_and_restart_without_blocking():
    processes = [FakeProcess(), FakeProcess()]
    runner = ManagedCliRunner(process_factory=lambda *a, **k: processes.pop(0))
    assert runner.start(["watch", "--max-cycles", "1"])
    wait_for(runner, "stopped")
    assert runner.start(["watch", "--max-cycles", "1"])
    wait_for(runner, "stopped")
    assert [event.kind for event in runner.drain_events()] == [
        "started", "completed", "started", "completed"]


def test_double_start_is_rejected_and_stop_is_deterministic():
    process = FakeProcess(slow=True)
    runner = ManagedCliRunner(process_factory=lambda *a, **k: process)
    assert runner.start(["watch"])
    wait_for(runner, "running")
    assert not runner.start(["watch"])
    assert runner.stop()
    wait_for(runner, "stopped")
    assert process.terminated
    assert any(event.kind == "rejected" for event in runner.drain_events())


def test_stop_kills_unresponsive_process_and_close_leaves_no_worker():
    process = FakeProcess(slow=True, ignore_terminate=True)
    runner = ManagedCliRunner(process_factory=lambda *a, **k: process, stop_timeout=.01)
    runner.start(["watch"])
    wait_for(runner, "running")
    runner.close()
    assert process.terminated and process.killed
    assert runner.state == "stopped"


def test_worker_exception_is_reported_as_error():
    def fail(*args, **kwargs):
        raise OSError("processo non avviabile")
    runner = ManagedCliRunner(process_factory=fail)
    runner.start(["watch"])
    wait_for(runner, "error")
    event = runner.drain_events()[-1]
    assert event.kind == "error"
    assert "non avviabile" in event.message


def test_close_during_start_stops_process_when_it_becomes_available():
    process = FakeProcess(slow=True)
    release_factory = threading.Event()

    def delayed_factory(*args, **kwargs):
        release_factory.wait(2)
        return process

    runner = ManagedCliRunner(process_factory=delayed_factory)
    runner.start(["watch"])
    closer = threading.Thread(target=runner.close)
    closer.start()
    release_factory.set()
    closer.join(2)
    wait_for(runner, "stopped")
    assert process.terminated
