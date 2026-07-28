import json
import socket

import pytest

from fixtures import command_payload
from virgilio_connector.caronte_http import (
    BRIDGE_ACTION,
    CaronteDryRunClientError,
    CaronteDryRunHttpClient,
    CaronteDryRunUrlNotConfigured,
)


def response_payload(*, ok=True):
    return {
        "ok": ok,
        "dry_run": True,
        "accepted_attachments": 1 if ok else 0,
        "rejected_attachments": 0 if ok else 1,
        "limbo_drive_ids": [],
        "bucoliche_rows": [],
        "message": "validated" if ok else "rejected",
        "errors": [] if ok else [{"code": "INVALID", "message": "rejected"}],
    }


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")
        self.closed = False

    def read(self):
        return self.payload

    def close(self):
        self.closed = True


def write_command(tmp_path, mutate=None):
    payload = command_payload(dry_run=True)
    if mutate:
        mutate(payload)
    path = tmp_path / "command.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_url_not_configured_never_attempts_network(tmp_path):
    calls = []
    client = CaronteDryRunHttpClient(None, opener=lambda *args, **kwargs: calls.append(args))
    with pytest.raises(CaronteDryRunUrlNotConfigured, match="not configured"):
        client.send_command_file(write_command(tmp_path))
    assert calls == []


def test_valid_payload_is_sent_as_metadata_only_envelope(tmp_path):
    captured = {}

    def opener(request, *, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(response_payload())

    result = CaronteDryRunHttpClient(
        "https://example.invalid/exec", timeout_seconds=7, opener=opener
    ).send_command_file(write_command(tmp_path))
    envelope = json.loads(captured["request"].data.decode("utf-8"))
    serialized = captured["request"].data.decode("utf-8")
    assert result.ok is True
    assert captured["timeout"] == 7
    assert envelope["action"] == BRIDGE_ACTION
    assert envelope["payload"]["dry_run"] is True
    for forbidden in ("local_path", "file_path", "file_bytes", "base64", '"content"', '"raw"'):
        assert forbidden not in serialized


def test_timeout_is_reported_without_retry(tmp_path):
    calls = 0

    def opener(request, *, timeout):
        nonlocal calls
        calls += 1
        raise socket.timeout()

    client = CaronteDryRunHttpClient("https://example.invalid/exec", opener=opener)
    with pytest.raises(CaronteDryRunClientError, match="timed out"):
        client.send_command_file(write_command(tmp_path))
    assert calls == 1


@pytest.mark.parametrize("ok", [True, False])
def test_standard_ok_and_error_responses_are_parsed(tmp_path, ok):
    client = CaronteDryRunHttpClient(
        "https://example.invalid/exec",
        opener=lambda request, timeout: FakeResponse(response_payload(ok=ok)),
    )
    result = client.send_command_file(write_command(tmp_path))
    assert result.ok is ok
    assert result.dry_run is True


@pytest.mark.parametrize("field", [
    "local_path", "file_path", "file_bytes", "base64", "content", "raw",
])
def test_forbidden_fields_are_blocked_before_network(tmp_path, field):
    calls = []
    path = write_command(tmp_path, lambda payload: payload["attachments"][0].update({field: "x"}))
    client = CaronteDryRunHttpClient(
        "https://example.invalid/exec", opener=lambda *args, **kwargs: calls.append(args)
    )
    with pytest.raises(CaronteDryRunClientError, match="forbidden"):
        client.send_command_file(path)
    assert calls == []


def test_operational_command_is_blocked_before_network(tmp_path):
    calls = []
    path = write_command(tmp_path, lambda payload: payload.update({"dry_run": False}))
    client = CaronteDryRunHttpClient(
        "https://example.invalid/exec", opener=lambda *args, **kwargs: calls.append(args)
    )
    with pytest.raises(CaronteDryRunClientError, match="dry_run=true"):
        client.send_command_file(path)
    assert calls == []


def test_inconsistent_response_counts_are_rejected(tmp_path):
    response = response_payload()
    response["accepted_attachments"] = 0
    client = CaronteDryRunHttpClient(
        "https://example.invalid/exec",
        opener=lambda request, timeout: FakeResponse(response),
    )
    with pytest.raises(CaronteDryRunClientError, match="counts are inconsistent"):
        client.send_command_file(write_command(tmp_path))
