"""Each embedding purpose resolves independently, and defaults are unchanged."""
from __future__ import annotations

import pytest

from aaa.platform.embeddings import (
    PURPOSES,
    EmbeddingConfigError,
    embedding_dim,
    get_embedder,
    provider_for,
    reset_cache,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    """Providers are cached per purpose; isolate every test."""
    reset_cache()
    yield
    reset_cache()


def test_all_purposes_default_to_openai():
    """Defaults must reproduce the pre-seam behaviour exactly."""
    assert {p: provider_for(p) for p in PURPOSES} == {
        "client_docs": "openai", "regulatory": "openai", "evidence": "openai"}


def test_openai_provider_reports_its_true_width():
    """3072 is text-embedding-3-large's width, not a hardcoded assumption."""
    assert embedding_dim("client_docs") == 3072


def test_provider_identity_is_recorded():
    """Identity is what lets a store detect a later provider swap."""
    assert get_embedder("regulatory").model_id == "openai:text-embedding-3-large"


def test_unknown_purpose_is_rejected():
    """A typo'd purpose fails loudly rather than silently picking a default."""
    with pytest.raises(EmbeddingConfigError):
        provider_for("not_a_purpose")


def test_unknown_provider_is_rejected(monkeypatch):
    """An unrecognised provider name never falls back to a default."""
    from aaa.settings import settings
    monkeypatch.setattr(settings, "embeddings_evidence", "sbert-ish")
    with pytest.raises(EmbeddingConfigError):
        get_embedder("evidence")


def test_local_without_a_model_names_the_setting(monkeypatch):
    """EMBEDDINGS_LOCAL_MODEL has no default; the error must say so."""
    from aaa.settings import settings
    monkeypatch.setattr(settings, "embeddings_client_docs", "local")
    monkeypatch.setattr(settings, "embeddings_local_model", "")
    with pytest.raises(EmbeddingConfigError, match="EMBEDDINGS_LOCAL_MODEL"):
        get_embedder("client_docs")


def test_purposes_are_configured_independently(monkeypatch):
    """The client dossier can go local while the corpus stays hosted."""
    from aaa.settings import settings
    monkeypatch.setattr(settings, "embeddings_client_docs", "local")
    assert provider_for("client_docs") == "local"
    assert provider_for("regulatory") == "openai"
