"""The stub's HTTP surface, OpenAI-shaped."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from scripts.bootstrap.stub.vectors import vector

CHAT_REFUSAL = {"error": {"message": "bootstrap --mock-llm: chat completions are not served; "
                                     "agents take their deterministic paths",
                          "type": "invalid_request_error", "code": 400}}


def embeddings_reply(body: dict[str, Any]) -> dict[str, Any]:
    """Build the ``/embeddings`` response for *body*."""
    raw = body.get("input", [])
    inputs = [raw] if isinstance(raw, str) else [str(t) for t in raw]
    return {"object": "list", "model": body.get("model", ""),
            "data": [{"object": "embedding", "index": i, "embedding": vector(t)}
                     for i, t in enumerate(inputs)],
            "usage": {"prompt_tokens": len(inputs), "total_tokens": len(inputs)}}


class Handler(BaseHTTPRequestHandler):
    """Routes on the path's tail so any ``/api/v1``-style prefix works."""

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802  pylint: disable=invalid-name
        """Liveness only."""
        if self.path.endswith("/health"):
            self._send(200, {"ok": True})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802  pylint: disable=invalid-name
        """Embeddings are served; chat is refused with a terminal 400."""
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length) or b"{}")
        if self.path.endswith("/embeddings"):
            self._send(200, embeddings_reply(body))
        elif self.path.endswith("/chat/completions"):
            self._send(400, CHAT_REFUSAL)
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, format: str, *args: Any) -> None:  # pylint: disable=redefined-builtin
        """Quiet: the bootstrap's own output is the log."""


def serve(port: int) -> ThreadingHTTPServer:
    """Bind the stub on loopback."""
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
