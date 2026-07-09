"""Send GitHub webhook events to a Microsoft Teams Power Automate workflow."""

import argparse
import json
import os
import sys
from typing import Any, Dict

import requests

from .formatters import format_event


def load_event(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def send_to_teams(webhook_url: str, payload: Dict[str, Any], timeout: int = 30) -> requests.Response:
    """POST a JSON payload to the Power Automate workflow URL.

    The default Teams workflow template "Post to a channel when a webhook
    request is received" reads the `text` field and posts it to the channel.
    """
    headers = {"Content-Type": "application/json"}
    response = requests.post(webhook_url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    return response


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Forward a GitHub webhook event to a Teams Power Automate workflow."
    )
    parser.add_argument("--url", help="Teams workflow webhook URL (or set WORKFLOW_WEBHOOK_URL)")
    parser.add_argument("--event", help="GitHub event name (or set GITHUB_EVENT_NAME)")
    parser.add_argument("--payload", help="Path to GitHub event JSON (or set GITHUB_EVENT_PATH)")
    parser.add_argument(
        "--format",
        choices=["adaptive", "text", "raw"],
        default="adaptive",
        help="Message format: adaptive (Adaptive Card, default), text (plain), or raw",
    )
    parser.add_argument("--timeout", type=int, default=30, help="HTTP request timeout in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Print payload instead of sending")
    args = parser.parse_args(argv)

    webhook_url = args.url or os.environ.get("WORKFLOW_WEBHOOK_URL")
    if not webhook_url and not args.dry_run:
        print("ERROR: --url or WORKFLOW_WEBHOOK_URL is required", file=sys.stderr)
        return 1

    event_name = args.event or os.environ.get("GITHUB_EVENT_NAME", "unknown")

    event_path = args.payload or os.environ.get("GITHUB_EVENT_PATH")
    if event_path:
        try:
            event = load_event(event_path)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"ERROR: cannot read event payload: {exc}", file=sys.stderr)
            return 1
    else:
        event = {}

    if args.format == "raw":
        payload = event
    else:
        payload = format_event(event_name, event, fmt=args.format)

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    try:
        response = send_to_teams(webhook_url, payload, timeout=args.timeout)
        print(f"Sent successfully: HTTP {response.status_code}")
        return 0
    except requests.RequestException as exc:
        print(f"ERROR: failed to send webhook: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
