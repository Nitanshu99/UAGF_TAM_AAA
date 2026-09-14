"""Verifier — Tier-1 cross-cutting agent (§3.1 #2, §8.1).

Implements the independent critique loop that gates every phase artefact
before it is admitted to the Evidence Store.

Verdict codes: ``accept`` · ``accept_with_notes`` · ``rerun`` (bounded by
``MAX_RERUNS``) · ``escalate_hitl``, plus ``unverified`` — which the Verifier
never *chooses*: it is what the deterministic fallback records when the LLM
critique could not run, so that a gate which did not run is distinguishable
from one that ran and passed (P6).

Rubric checks (four dimensions per §8.1): factual accuracy, completeness,
evidence linkage, citation correctness.
"""
from __future__ import annotations

from aaa.agents.tier1.verifier.agent import Verifier
from aaa.agents.tier1.verifier.messages import (  # noqa: F401 (test access)
    _SYSTEM_PROMPT,
    _build_critique_messages,
)
from aaa.agents.tier1.verifier.verdicts import (
    MAX_RERUNS,
    UNVERIFIED,
    VerifierError,
    VerifierVerdict,
)

__all__ = ["MAX_RERUNS", "UNVERIFIED", "Verifier", "VerifierError", "VerifierVerdict"]
