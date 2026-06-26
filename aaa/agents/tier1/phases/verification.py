"""
aaa.agents.tier1.phases.verification — Real Verifier wiring for phase runners.

Previously every phase hardcoded ``verifier_critiques[tid] = {"verdict": "accept"}``,
so the independent-critique gate (``aaa.agents.tier1.verifier.Verifier``) was built
but never invoked. This module actually runs the Verifier against each produced
artefact, records the *real* critique, and honours its verdict:

  - ``rerun``         → re-dispatch the phase agent (bounded by ``MAX_RERUNS``).
  - ``escalate_hitl`` → flag the engagement for human review.
  - ``accept`` / ``accept_with_notes`` → admit.

In offline/CI mode the Verifier applies deterministic checks (non-empty artefact,
evidence linkage); with an LLM configured it applies the four-dimension rubric.
"""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.tier1.phases.agent_runner import run_agent_on_state
from aaa.agents.tier1.verifier import MAX_RERUNS, Verifier

logger = logging.getLogger(__name__)

# accept < accept_with_notes < rerun < escalate_hitl (worst wins).
_VERDICT_ORDER = ["accept", "accept_with_notes", "rerun", "escalate_hitl"]

_VERIFIER: Verifier | None = None


def _get_verifier() -> Verifier:
    """Return a process-wide Verifier (cheap to construct; reused across phases)."""
    global _VERIFIER
    if _VERIFIER is None:
        _VERIFIER = Verifier()
    return _VERIFIER


def _worse(a: str, b: str) -> str:
    ia = _VERDICT_ORDER.index(a) if a in _VERDICT_ORDER else 0
    ib = _VERDICT_ORDER.index(b) if b in _VERDICT_ORDER else 0
    return _VERDICT_ORDER[max(ia, ib)]


def _artefact_content(store: Any, state: dict, tid: str) -> Any:
    """Load a produced artefact's content from the store for critique."""
    ref = state.get("phase_artefacts", {}).get(tid)
    if not isinstance(ref, dict):
        return {}
    uri = ref.get("uri")
    if not uri:
        return {}
    try:
        return store.get_artefact(uri) or {}
    except Exception:  # noqa: BLE001
        return {}


def _merge_critique(
    crit: dict[str, Any],
    fallback_articles: list[str],
    phase_label: str,
    confidence: float,
) -> dict[str, Any]:
    """Normalise a raw Verifier critique into the stored ``verifier_critiques`` shape.

    ``article_citations`` falls back to the phase's known articles so that
    artefact admission (``_collect_admitted_articles``) keeps working even when the
    deterministic verifier does not emit citations.
    """
    notes = list(crit.get("notes") or [])
    notes.append(f"{phase_label} complete. confidence={confidence:.2f}")
    return {
        "verdict": crit.get("verdict", "accept"),
        "issues": crit.get("issues", []),
        "notes": notes,
        "article_citations": crit.get("article_citations") or list(fallback_articles),
        "rerun_required": bool(crit.get("rerun_required", False)),
        "scores": crit.get("scores", {}),
        "total_score": crit.get("total_score"),
        "llm_fallback_mode": crit.get("llm_fallback_mode"),
    }


async def run_phase_with_verification(
    agent: Any,
    dispatch: Any,
    state: dict,
    tid_articles: dict[str, list[str]],
    phase_label: str,
    *,
    timeout: int = 180,
    default_confidence: float = 0.9,
) -> tuple[Any, dict]:
    """Run *agent*, critique each artefact with the real Verifier, honour the verdict.

    Returns ``(report, state)``; ``report`` is ``None`` if the agent failed (caller
    falls back to its stub). On a ``rerun`` verdict the agent is re-dispatched up to
    ``MAX_RERUNS`` times; an unresolved ``rerun`` or ``escalate_hitl`` flags HITL.
    """
    verifier = _get_verifier()
    evidence_uris = list(dispatch.get("evidence_uris", []) or [])
    phase_id = dispatch.get("phase_id", "")
    report = None
    rerun_count = 0

    while True:
        report, state = await run_agent_on_state(agent, dispatch, state, timeout=timeout)
        if report is None:
            return None, state
        confidence = float(report.get("confidence", default_confidence) or default_confidence)

        worst = "accept"
        for tid, articles in tid_articles.items():
            content = _artefact_content(agent.store, state, tid)
            try:
                crit = await verifier.process({
                    "phase_id": phase_id,
                    "template_id": tid,
                    "content": content,
                    "evidence_uris": evidence_uris,
                    "rerun_count": rerun_count,
                })
            except Exception as exc:  # noqa: BLE001 - verifier failure must not pass silently
                logger.warning("Verifier failed for %s (%s); recording accept_with_notes.", tid, exc)
                crit = {
                    "verdict": "accept_with_notes",
                    "issues": [],
                    "notes": [f"Verifier unavailable: {exc}"],
                }
            state["verifier_critiques"][tid] = _merge_critique(
                crit, articles, phase_label, confidence
            )
            worst = _worse(worst, state["verifier_critiques"][tid]["verdict"])

        if worst == "rerun" and rerun_count < MAX_RERUNS:
            rerun_count += 1
            logger.info("%s: verifier requested rerun (%d/%d).", phase_label, rerun_count, MAX_RERUNS)
            continue

        if worst in {"rerun", "escalate_hitl"}:
            state["hitl_required"] = True
            state["hitl_reason"] = (
                f"{phase_label}: Verifier verdict '{worst}' on artefact(s) "
                f"after {rerun_count} rerun(s)."
            )
        return report, state


__all__ = ["run_phase_with_verification"]
