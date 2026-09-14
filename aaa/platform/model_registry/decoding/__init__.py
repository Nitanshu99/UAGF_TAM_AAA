"""Decoding parameters: greedy by default, so a run can be reproduced.

An audit opinion that changes when the same evidence is re-examined is not an
audit opinion. Until 2026-09-13 nothing here set ``temperature``, ``seed`` or
``top_p``, so every call sampled at the provider's default and four runs of the
same case disagreed on **9 of 17** artefact verdicts — ``completeness_score`` is
``admitted / expected``, so it moved with them (0.29 → 0.41 across those runs).

Greedy decoding with a fixed seed is the standard control for an LLM judge, and
it is the proportionate one here: it changes no decision rule and costs no extra
calls, where N-of-M voting would change what the verdict *means* and triple the
bill. It is applied to every agent, not only the Verifier, because the artefacts
under critique are model-written too — pinning the judge while the evidence still
moves would fix half the chain.

**What this does and does not guarantee.** ``temperature=0`` removes sampling,
which is the dominant term. ``seed`` is best-effort: providers differ in whether
they honour it. Batching, mixture-of-experts routing and floating-point
non-associativity can still move a token — measured on MiniMax-M3, two greedy
calls worded a critique differently while agreeing on the verdict and on every
materiality tag. So this makes a run *reproducible in practice*, not bitwise
identical by construction.

**Not every model can be greedy.** OpenAI's reasoning models accept only the
default temperature, so :func:`decoding_kwargs` does not ask them for one (see
``capability``): on the default OpenAI roster only ``seed`` is sent and greedy
decoding is not in effect. The record says so rather than assuming it. Every
audit row carries both halves — :func:`decoding_kwargs` for the request and
:func:`sent_decoding` for what LiteLLM's parameter mapping put on the wire — and
:func:`decoding_provenance` states per roster model whether greedy applied.

Override for deliberate exploration: ``AAA_LLM_TEMPERATURE`` and ``AAA_LLM_SEED``
(set the seed empty to send none at all).
"""
from aaa.platform.model_registry.decoding.capability import refuses_temperature  # noqa: F401
from aaa.platform.model_registry.decoding.policy import (  # noqa: F401
    DEFAULT_SEED,
    DEFAULT_TEMPERATURE,
    decoding_kwargs,
)
from aaa.platform.model_registry.decoding.provenance import decoding_provenance  # noqa: F401
from aaa.platform.model_registry.decoding.wire import sent_decoding  # noqa: F401

__all__ = [
    "DEFAULT_SEED",
    "DEFAULT_TEMPERATURE",
    "decoding_kwargs",
    "decoding_provenance",
    "refuses_temperature",
    "sent_decoding",
]
