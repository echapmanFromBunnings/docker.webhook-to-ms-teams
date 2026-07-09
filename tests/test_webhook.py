"""Unit tests for the Teams webhook sender."""

import json
import os
from pathlib import Path

from tests.mock_server import get_captured_requests, start_mock_server, stop_mock_server

from src.teams_webhook import main as webhook_main

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _send_and_capture(event: str, fixture: str) -> dict:
    server, url = start_mock_server()
    try:
        payload_path = FIXTURES_DIR / f"{fixture}.json"
        rc = webhook_main(["--url", url, "--event", event, "--payload", str(payload_path)])
        assert rc == 0
        requests = get_captured_requests()
        assert len(requests) == 1
        return requests[0]
    finally:
        stop_mock_server(server)


def test_send_push_event():
    req = _send_and_capture("push", "push")
    assert req["headers"]["Content-Type"] == "application/json"
    assert req["json"]["text"]
    assert "Update webhook integration" in req["json"]["text"]
    assert "refs/heads/main" not in req["json"]["text"]  # branch only
    assert "main" in req["json"]["text"]


def test_send_pull_request_event():
    req = _send_and_capture("pull_request", "pull_request")
    assert "Pull Request Opened" in req["json"]["text"]
    assert "Update Teams integration" in req["json"]["text"]


def test_send_workflow_run_event():
    req = _send_and_capture("workflow_run", "workflow_run")
    assert "Workflow Run" in req["json"]["text"]
    assert "failure" in req["json"]["text"]
    assert "❌" in req["json"]["text"]


def test_dry_run_prints_payload(capsys):
    payload_path = FIXTURES_DIR / "push.json"
    rc = webhook_main(["--event", "push", "--payload", str(payload_path), "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "text" in data


def test_missing_url_fails():
    # Ensure env var is not present.
    os.environ.pop("WORKFLOW_WEBHOOK_URL", None)
    rc = webhook_main(["--event", "push", "--payload", str(FIXTURES_DIR / "push.json")])
    assert rc == 1
