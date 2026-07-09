"""A tiny HTTP server that captures webhook POSTs for local testing."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List


class _CaptureHandler(BaseHTTPRequestHandler):
    requests: List[Dict[str, Any]] = []

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        _CaptureHandler.requests.append(
            {
                "path": self.path,
                "headers": dict(self.headers.items()),
                "body": body,
                "json": json.loads(body) if body else None,
            }
        )
        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"accepted"}')

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress default request logging noise in tests.
        pass


def start_mock_server(host: str = "127.0.0.1", port: int = 0) -> tuple[HTTPServer, str]:
    """Start a capture server on an ephemeral port. Returns (server, url)."""
    _CaptureHandler.requests.clear()
    server = HTTPServer((host, port), _CaptureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    actual_port = server.server_address[1]
    return server, f"http://{host}:{actual_port}/webhook"


def get_captured_requests() -> List[Dict[str, Any]]:
    return list(_CaptureHandler.requests)


def stop_mock_server(server: HTTPServer) -> None:
    server.shutdown()
    server.server_close()
