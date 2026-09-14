"""The OpenRouter embedding provider: same model, one key, gateway on record."""
from __future__ import annotations

import pytest

from aaa.platform.embeddings import (
    credentials_present,
    embedding_dim,
    get_embedder,
    missing_credential,
    provider_for,
    reset_cache,
)
from aaa.platform.embeddings.openrouter import DEFAULT_API_BASE, OpenRouterEmbedder, gateway_tag


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    """Cached providers and the gateway/key variables must not leak between tests."""
    reset_cache()
    for name in ("OPENROUTER_API_BASE", "OPENROUTER_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    yield
    reset_cache()


def _route_all_to_openrouter(monkeypatch) -> None:
    from aaa.settings import settings
    for field in ("embeddings_client_docs", "embeddings_regulatory", "embeddings_evidence"):
        monkeypatch.setattr(settings, field, "openrouter")
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    monkeypatch.setattr(settings, "openai_api_key", "")


def test_openrouter_is_a_selectable_provider(monkeypatch):
    """It resolves through the seam like the other two."""
    _route_all_to_openrouter(monkeypatch)
    assert provider_for("regulatory") == "openrouter"
    assert isinstance(get_embedder("regulatory"), OpenRouterEmbedder)


def test_it_is_the_same_model_at_the_same_width(monkeypatch):
    """A corpus built through OpenRouter has OpenAI's 3072-wide vectors."""
    _route_all_to_openrouter(monkeypatch)
    assert embedding_dim("regulatory") == 3072
    assert get_embedder("regulatory").model_id == "openrouter:openai/text-embedding-3-large"


def test_a_non_default_gateway_is_part_of_the_identity(monkeypatch):
    """Vectors from a proxy or the stub must never pass for the public gateway's."""
    monkeypatch.setenv("OPENROUTER_API_BASE", "http://127.0.0.1:4321/api/v1")
    assert OpenRouterEmbedder().model_id == \
        "openrouter@127.0.0.1:4321:openai/text-embedding-3-large"
    assert gateway_tag(DEFAULT_API_BASE) == "openrouter"
    assert gateway_tag(DEFAULT_API_BASE + "/") == "openrouter"


def test_the_gate_asks_for_the_openrouter_key_not_the_openai_one(monkeypatch):
    """OPENAI_API_KEY is irrelevant to this provider, present or not."""
    _route_all_to_openrouter(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-irrelevant")
    assert missing_credential("client_docs") == "OPENROUTER_API_KEY"
    assert credentials_present("evidence") is False
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test")
    assert credentials_present("evidence") is True


def test_a_local_provider_needs_no_key(monkeypatch):
    """Nothing leaves the host, so nothing has to be unlocked."""
    from aaa.settings import settings
    monkeypatch.setattr(settings, "embeddings_client_docs", "local")
    assert missing_credential("client_docs") is None


def test_embed_goes_to_the_gateway_with_the_openrouter_key(monkeypatch):
    """The OpenAI SDK is pointed at OPENROUTER_API_BASE and given the OpenRouter key."""
    import openai

    seen: dict = {}

    class _Data:
        def __init__(self, n: int) -> None:
            self.data = [type("E", (), {"embedding": [float(i)] * 3})() for i in range(n)]

    class _Client:
        def __init__(self, api_key: str, base_url: str) -> None:
            seen["api_key"], seen["base_url"] = api_key, base_url
            self.embeddings = self

        def create(self, model: str, input: list[str]):  # noqa: A002 - SDK signature
            seen["model"], seen["input"] = model, list(input)
            return _Data(len(input))

    monkeypatch.setattr(openai, "OpenAI", _Client)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test")
    monkeypatch.setenv("OPENROUTER_API_BASE", "http://127.0.0.1:9/api/v1/")
    vectors = OpenRouterEmbedder().embed(["a", "b"])
    assert seen == {"api_key": "sk-or-v1-test", "base_url": "http://127.0.0.1:9/api/v1",
                    "model": "openai/text-embedding-3-large", "input": ["a", "b"]}
    assert vectors == [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]


def test_embed_without_a_key_fails_before_any_request(monkeypatch):
    """A blank key is a configuration error, named as such."""
    from aaa.platform.embeddings import EmbeddingConfigError
    from aaa.settings import settings
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    with pytest.raises(EmbeddingConfigError, match="OPENROUTER_API_KEY"):
        OpenRouterEmbedder().embed(["x"])
