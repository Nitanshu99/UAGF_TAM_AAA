"""The no-spend stub answers embeddings with the real shape and refuses chat."""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from scripts.bootstrap.stub.server import serve
from scripts.bootstrap.stub.vectors import DIM, vector


@pytest.fixture
def stub_url():
    server = serve(0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/api/v1"
    server.shutdown()
    server.server_close()


def _post(url: str, payload: dict) -> tuple[int, dict]:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310 - loopback
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def test_vectors_are_deterministic_unit_vectors_of_the_model_width() -> None:
    a, b = vector("Article 9"), vector("Article 9")
    assert a == b and len(a) == DIM == 3072
    assert abs(sum(x * x for x in a) - 1.0) < 1e-3
    assert vector("Article 10") != a


def test_embeddings_are_served_openai_shaped(stub_url: str) -> None:
    status, body = _post(f"{stub_url}/embeddings",
                         {"model": "openai/text-embedding-3-large", "input": ["x", "y"]})
    assert status == 200
    assert [d["index"] for d in body["data"]] == [0, 1]
    assert len(body["data"][0]["embedding"]) == DIM
    assert body["model"] == "openai/text-embedding-3-large"
    status, body = _post(f"{stub_url}/embeddings", {"model": "m", "input": "one string"})
    assert status == 200 and len(body["data"]) == 1


def test_chat_is_refused_with_a_terminal_400(stub_url: str) -> None:
    status, body = _post(f"{stub_url}/chat/completions", {"model": "m", "messages": []})
    assert status == 400
    assert body["error"]["type"] == "invalid_request_error"


def test_health_answers(stub_url: str) -> None:
    with urllib.request.urlopen(f"{stub_url}/health") as resp:  # noqa: S310 - loopback
        assert json.load(resp) == {"ok": True}
