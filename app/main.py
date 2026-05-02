"""Minimal stdlib HTTP server for the challenge endpoints."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

from app.router import handle_context, handle_healthz, handle_metadata, handle_reply, handle_tick
from config.constants import DEFAULT_PORT


class VeraRequestHandler(BaseHTTPRequestHandler):
    server_version = "VeraDeterministic/1.0"

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def _send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        routes: dict[str, Callable[[], tuple[int, dict]]] = {
            "/v1/healthz": handle_healthz,
            "/v1/metadata": handle_metadata,
        }
        handler = routes.get(self.path)
        if not handler:
            self._send_json(404, {"error": "not_found"})
            return
        status, payload = handler()
        self._send_json(status, payload)

    def do_POST(self) -> None:
        routes: dict[str, Callable[[dict], tuple[int, dict]]] = {
            "/v1/context": handle_context,
            "/v1/tick": handle_tick,
            "/v1/reply": handle_reply,
        }
        handler = routes.get(self.path)
        if not handler:
            self._send_json(404, {"error": "not_found"})
            return
        try:
            body = self._read_json()
            status, payload = handler(body)
        except json.JSONDecodeError as exc:
            status, payload = 400, {"error": "invalid_json", "details": str(exc)}
        except Exception as exc:
            status, payload = 500, {"error": "server_error", "details": str(exc)}
        self._send_json(status, payload)

    def log_message(self, format: str, *args) -> None:
        return


def create_server(host: str = "0.0.0.0", port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), VeraRequestHandler)


def main() -> None:
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    server = create_server(port=port)
    print(f"Vera deterministic bot listening on http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
