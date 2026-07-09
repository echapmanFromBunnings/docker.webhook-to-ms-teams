"""Unit tests for the Teams webhook sender."""

import json
import os
from pathlib import Path

from tests.mock_server import get_captured_requests, start_mock_server, stop_mock_server

from src.teams_webhook import main as webhook_main

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _send_and_capture(event: str, fixture: str, fmt: str = "adaptive") -> dict:
    server, url = start_mock_server()
    try:
        payload_path = FIXTURES_DIR / f"{fixture}.json"
        rc = webhook_main(
            ["--url", url, "--event", event, "--payload", str(payload_path), "--format", fmt]
        )
        assert rc == 0
        requests = get_captured_requests()
        assert len(requests) == 1
        return requests[0]
    finally:
        stop_mock_server(server)


def _card_text(req: dict) -> str:
    """Return the concatenated text of all TextBlocks in the adaptive card."""
    body = req["json"]["attachments"][0]["content"]["body"]
    return "\n".join(block.get("text", "") for block in body)


def _assert_valid_card(req: dict) -> None:
    payload = req["json"]
    assert payload["type"] == "message"
    attachment = payload["attachments"][0]
    assert attachment["contentType"] == "application/vnd.microsoft.card.adaptive"
    content = attachment["content"]
    assert content["type"] == "AdaptiveCard"
    assert content["$schema"] == "http://adaptivecards.io/schemas/adaptive-card.json"
    assert content["version"]
    assert content["body"]


def test_send_push_event():
    req = _send_and_capture("push", "push")
    assert req["headers"]["Content-Type"] == "application/json"
    _assert_valid_card(req)
    text = _card_text(req)
    assert "Update webhook integration" in text
    assert "refs/heads/main" not in text  # branch only
    assert "main" in text


def test_send_pull_request_event():
    req = _send_and_capture("pull_request", "pull_request")
    _assert_valid_card(req)
    text = _card_text(req)
    assert "Pull Request Opened" in text
    assert "Update Teams integration" in text


def test_send_workflow_run_event():
    req = _send_and_capture("workflow_run", "workflow_run")
    _assert_valid_card(req)
    text = _card_text(req)
    assert "Workflow Run" in text
    assert "failure" in text
    assert "❌" in text


def test_text_format_still_supported():
    req = _send_and_capture("push", "push", fmt="text")
    assert "text" in req["json"]
    assert "attachments" not in req["json"]
    assert "Update webhook integration" in req["json"]["text"]


def test_dry_run_prints_adaptive_card(capsys):
    payload_path = FIXTURES_DIR / "push.json"
    rc = webhook_main(["--event", "push", "--payload", str(payload_path), "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["type"] == "message"
    assert data["attachments"][0]["content"]["type"] == "AdaptiveCard"


def test_missing_url_fails():
    # Ensure env var is not present.
    os.environ.pop("WORKFLOW_WEBHOOK_URL", None)
    rc = webhook_main(["--event", "push", "--payload", str(FIXTURES_DIR / "push.json")])
    assert rc == 1
