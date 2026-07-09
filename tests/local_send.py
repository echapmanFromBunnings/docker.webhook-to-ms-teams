"""Local test harness: start a mock server and send a sample GitHub event.

Usage:
    python -m tests.local_send [--event push|pull_request|...] [--fixture push]
"""

import argparse
import json
from pathlib import Path

from tests.mock_server import get_captured_requests, start_mock_server, stop_mock_server

from src.teams_webhook import main as webhook_main

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a sample event to a local mock Teams webhook.")
    parser.add_argument("--event", default="push", help="GitHub event name")
    parser.add_argument("--fixture", default="push", help="Fixture file stem under tests/fixtures")
    args = parser.parse_args()

    fixture_path = FIXTURES_DIR / f"{args.fixture}.json"
    if not fixture_path.exists():
        print(f"Fixture not found: {fixture_path}")
        return 1

    server, url = start_mock_server()
    print(f"Mock Teams workflow listening at {url}")
    try:
        rc = webhook_main(["--url", url, "--event", args.event, "--payload", str(fixture_path)])
        if rc != 0:
            return rc

        requests = get_captured_requests()
        if requests:
            print("\nCaptured request body:")
            print(json.dumps(requests[0]["json"], indent=2))
        else:
            print("No requests captured.")
            return 1
    finally:
        stop_mock_server(server)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
