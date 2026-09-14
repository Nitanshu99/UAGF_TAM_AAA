"""
groundedness_check — TruLens groundedness score (§4.4).

Production path: a TruLens feedback provider (``trulens.providers.*``), which
scores how far an answer's claims are supported by the retrieved context.

When no provider is installed the tool reports **not computed** — it never
invents a score. An earlier version returned ``random.uniform(0.7, 0.98)``
as a "mock", which is indistinguishable from a measurement once it reaches a
T16 artefact and would misrepresent an audit.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _not_computed(reason: str) -> dict[str, Any]:
    """Build the explicit not-computed result.

    :param reason: Why groundedness could not be measured.
    :type reason: str
    :returns: T16 ``groundedness_metrics`` shape with null scores.
    :rtype: dict[str, Any]
    """
    return {
        "computed": False,
        "groundedness_score": None,
        "context_relevance": None,
        "answer_relevance": None,
        "rationale": f"Groundedness not computed: {reason}.",
    }


def groundedness_check(
    context: str | None = None,
    answer: str | None = None,
) -> dict[str, Any]:
    """
    Compute groundedness score (claims in answer supported by context).

    :param context: Retrieved context or reference text.
    :type context: str | None
    :param answer: The generated answer to verify.
    :type answer: str | None
    :returns: Dict matching the T16 ``groundedness_metrics`` sub-schema;
        ``computed`` is ``False`` and every score ``None`` when no TruLens
        provider is available.
    :rtype: dict[str, Any]
    """
    if not context or not answer:
        return _not_computed("empty context or answer")
    try:
        return _compute_trulens(context, answer)
    except Exception as exc:  # noqa: BLE001 — any provider failure is reported, not faked
        logger.info("TruLens groundedness unavailable (%s); reporting not computed.", exc)
        return _not_computed(f"TruLens provider unavailable ({type(exc).__name__})")


def _compute_trulens(context: str, answer: str) -> dict[str, Any]:
    """Score groundedness with a TruLens provider.

    :param context: Retrieved context or reference text.
    :type context: str
    :param answer: The generated answer to verify.
    :type answer: str
    :returns: Populated ``groundedness_metrics`` with ``computed`` true.
    :rtype: dict[str, Any]
    :raises ImportError: When no TruLens provider package is installed.
    """
    # Optional at runtime: trulens-eval installs core/feedback/dashboard but
    # not the provider packages, so this resolves only when
    # `trulens-providers-litellm` is present. pylint cannot see that.
    from trulens.providers.litellm import (  # type: ignore  # pylint: disable=no-name-in-module,import-outside-toplevel
        LiteLLM,
    )

    from aaa.platform.model_registry.resolve import resolve_model

    # The run's own route. LiteLLM() alone meant OpenAI's default engine: no key, every
    # call failed "Missing credentials" on the free route (T-20260914-011).
    provider = LiteLLM(model_engine=resolve_model("UAGF-TAM-L"))
    score, reasons = provider.groundedness_measure_with_cot_reasons(context, answer)
    return {
        "computed": True,
        "groundedness_score": float(score),
        "context_relevance": None,   # separate TruLens feedback functions
        "answer_relevance": None,
        "rationale": str(reasons),
    }
