"""Judge LLM and embedding model for the RAGAs evaluation.

ragas builds its own default OpenAI clients when ``evaluate`` is called
without ``llm``/``embeddings``. Those defaults are incompatible with the
pinned ``langchain-openai`` (the embedding object it constructs has no
``embed_query``, and its async path rejects the sync client), so the judge
models are constructed explicitly here instead.

Both are overridable so the evaluation judge can be pinned independently of
the agent roster:

* ``RAGAS_JUDGE_MODEL``      (default: the run's own UAGF-TAM-L roster model)
* ``RAGAS_EMBEDDING_MODEL``  (default: the platform's embedding model)

Under ``PROVIDER=openrouter`` both clients go through OpenRouter's
OpenAI-compatible gateway with the OpenRouter key. The judge used to default to
``openai/gpt-4o-mini`` there — a paid model the rest of the run never touches;
case 04 made 360 evaluation jobs through it (T-20260914-011). It now judges on
the route the L-branch agent itself uses.
"""
from __future__ import annotations

import os
from typing import Any

#: Greedy, for the same reason the agent path is: a RAGAs score that moves
#: on re-run is not a measurement. See `model_registry.decoding`.
_TEMPERATURE = 0.0

#: The roster entry whose model judges the evaluation: the agent that runs it.
JUDGE_AGENT = "UAGF-TAM-L"
#: Outside OpenRouter, OpenAI's small embedding model (the SDK reads its own key).
DEFAULT_EMBEDDING = "text-embedding-3-small"


def _routing() -> dict[str, Any]:
    """Connection kwargs for the judge clients under the active provider.

    :returns: ``base_url``/``api_key`` for OpenRouter; empty for OpenAI, whose
        SDK reads ``OPENAI_API_KEY`` itself.
    """
    from aaa.platform.model_registry.provider import OPENROUTER, active_provider

    if active_provider() != OPENROUTER:
        return {}
    from aaa.platform.embeddings.openrouter import api_base, api_key

    return {"base_url": api_base(), "api_key": api_key()}


def judge_models() -> tuple[str, str]:
    """The judge LLM and embedding model names this process would use.

    :returns: ``(judge_model, embedding_model)``, vendor-prefixed for OpenRouter.
    """
    from aaa.platform.model_registry.resolve import resolve_model

    routed = bool(_routing())
    judge = resolve_model(JUDGE_AGENT)
    embedding = DEFAULT_EMBEDDING
    if routed:
        from aaa.platform.embeddings import openrouter

        judge = judge.removeprefix("openrouter/")  # the gateway takes the bare slug
        embedding = openrouter.MODEL
    return (os.getenv("RAGAS_JUDGE_MODEL", judge),
            os.getenv("RAGAS_EMBEDDING_MODEL", embedding))


def build_judge() -> tuple[Any, Any]:
    """Construct the ragas-wrapped judge LLM and embedding model.

    :returns: ``(llm, embeddings)`` ready to pass to ``ragas.evaluate``.
    :rtype: tuple[Any, Any]
    """
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from pydantic import SecretStr
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper

    routing = _routing()
    judge, embedding = judge_models()
    if not routing:
        return (LangchainLLMWrapper(ChatOpenAI(model=judge, temperature=_TEMPERATURE)),
                LangchainEmbeddingsWrapper(OpenAIEmbeddings(model=embedding)))
    base, key = str(routing["base_url"]), SecretStr(str(routing["api_key"]))
    llm = LangchainLLMWrapper(
        ChatOpenAI(model=judge, base_url=base, api_key=key, temperature=_TEMPERATURE))
    # A gateway takes plain strings; langchain's default pre-tokenises the
    # input for OpenAI's tokenizer, which only OpenAI itself accepts.
    embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(
        model=embedding, base_url=base, api_key=key, check_embedding_ctx_length=False))
    return llm, embeddings
