import subprocess
import threading
import time

from virgilio_connector.application.home_control import HomeRunController
from virgilio_connector.application.operation_runner import ManagedOperationRunner


class SlowProcess:
    def __init__(self, *, ignore_terminate=False):
        self.returncode = None
        self.ignore_terminate = ignore_terminate
        self.released = threading.Event()
        self.terminated = False
        self.killed = False

    def communicate(self):
        self.released.wait(2)
        if self.returncode is None:
            self.returncode = 0
        return "", ""

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


def _controller(tmp_path, process, *, timeout=0.05):
    runner = ManagedOperationRunner(
        process_factory=lambda *args, **kwargs: process,
        stop_timeout=timeout,
    )
    return HomeRunController(tmp_path / "config.yaml", runner)


def _wait_for(controller, state):
    deadline = time.monotonic() + 2
    while controller.state != state and time.monotonic() < deadline:
        time.sleep(0.005)
    assert controller.state == state


def test_check_now_returns_before_slow_worker_finishes(tmp_path):
    process = SlowProcess()
    controller = _controller(tmp_path, process)

    assert controller.check_now() is True
    _wait_for(controller, "running")
    assert process.released.is_set() is False
    controller.pause()


def test_continuous_start_returns_before_slow_worker_finishes(tmp_path):
    process = SlowProcess()
    controller = _controller(tmp_path, process)

    assert controller.start() is True
    _wait_for(controller, "running")
    assert process.released.is_set() is False
    controller.pause()


def test_slow_runner_keeps_an_intermediate_progress_event_observable(tmp_path):
    process = SlowProcess()
    controller = _controller(tmp_path, process)

    assert controller.check_now() is True
    _wait_for(controller, "running")
    # The acceptance feedback remains available while the worker has not completed.
    assert controller.drain_feedback()[0].state == "Controllo in corso"
    assert process.released.is_set() is False
    controller.pause()


def test_pause_stops_active_worker_and_reaches_final_state(tmp_path):
    process = SlowProcess()
    controller = _controller(tmp_path, process)
    controller.start()
    _wait_for(controller, "running")

    assert controller.pause() is True
    _wait_for(controller, "stopped")
    assert process.terminated is True


def test_concurrent_second_start_is_rejected(tmp_path):
    process = SlowProcess()
    controller = _controller(tmp_path, process)
    assert controller.start() is True
    _wait_for(controller, "running")

    assert controller.check_now() is False
    assert any(event.kind == "rejected" for event in controller.drain_events())
    controller.pause()


def test_close_kills_unresponsive_worker_and_leaves_no_orphan(tmp_path):
    process = SlowProcess(ignore_terminate=True)
    controller = _controller(tmp_path, process, timeout=0.01)
    controller.start()
    _wait_for(controller, "running")

    controller.close()

    assert process.terminated is True
    assert process.killed is True
    assert controller.state == "stopped"
