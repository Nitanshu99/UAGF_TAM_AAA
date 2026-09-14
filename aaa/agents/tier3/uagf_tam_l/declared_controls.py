"""Read the two L-branch documents the audit collected but never opened.

``guardrail_config_uri`` and ``rag_manifest_uri`` are Annex IV conditional
documents. The wizard asks for them, the completeness gate counts them, the
report lists them by name — and until 2026-09-11 no code path passed either to
``load_artifact_from_uri``. A client uploaded them, they moved the 80 % gate,
and nothing read a byte.

That is not a cosmetic gap. Case 06's guardrail configuration states, in its own
``implementation_status`` block, that four declared controls are **not yet
implemented in production** — among them
``input_guardrails.prompt_injection_detection``, which is precisely what the
L-branch's injection suite probes and what the Verifier flagged as unevidenced.
The client had already answered the question in a file the audit was holding.

Nothing here scores or judges. It extracts what the client *declares* so the
T16 narrative and the Verifier reason over evidence rather than over its
absence — a declared-but-unimplemented control is a fact the audit should
carry, not discover by inference.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier3.uagf_tam_l.control_sources import _guardrails, _retrieval
from aaa.agents.tier3.uagf_tam_l.control_status import _load

logger = logging.getLogger(__name__)


def resolve_declared_controls(stage_b: dict[str, Any], store: Any) -> dict[str, Any] | None:
    """Read the guardrail configuration and RAG manifest the client supplied.

    :param stage_b: The Annex IV dossier.
    :param store: Evidence store used to resolve ``minio://`` URIs.
    :returns: ``{"guardrails": …, "retrieval": …}`` for whichever documents were
        supplied and readable, or ``None`` when neither was.
    """
    guardrails = _load(stage_b.get("guardrail_config_uri"), store, "guardrail_config_uri")
    manifest = _load(stage_b.get("rag_manifest_uri"), store, "rag_manifest_uri")
    if guardrails is None and manifest is None:
        return None
    declared: dict[str, Any] = {}
    for key, document, summarise in (("guardrails", guardrails, _guardrails),
                                     ("retrieval", manifest, _retrieval)):
        if document is not None:
            declared[key] = _summary(key, document, summarise)
    return declared


def _summary(key: str, document: Any, summarise: Any) -> dict[str, Any]:
    """*summarise(document)*, or a record of why the document could not be read.

    A client document is data in whatever shape its author chose; its shape must
    never take the phase down with it.
    """
    if not isinstance(document, dict):
        return {"unreadable": f"{key} document is not a JSON object ({type(document).__name__})"}
    try:
        return summarise(document)
    except (AttributeError, TypeError, ValueError) as exc:
        logger.warning("L-branch: the %s document could not be summarised (%s).", key, exc)
        return {"unreadable": f"{type(exc).__name__}: {exc}"}
