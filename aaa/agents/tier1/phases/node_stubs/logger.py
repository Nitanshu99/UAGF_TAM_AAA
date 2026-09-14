"""Part 1 of the former ``node_stubs`` module (auto-split)."""
from __future__ import annotations

import logging

from aaa.tools.regulatory_coverage.artefact_contract import ARTEFACT_ARTICLES

logger = logging.getLogger(__name__)


#: Fix 50: one declaration, shared with the compliance matrix. This map and
#: that one were two copies that disagreed in seven places.
TEMPLATE_ARTICLES = ARTEFACT_ARTICLES


def _stub_artefact(engagement_id: str, tid: str) -> dict:
    return {"uri": f"mem://{engagement_id}/{tid}", "sha256": "stub", "template_id": tid}


def _stub_critique(note: str) -> dict:
    # accept_with_notes (not accept) makes the stub visibly non-authoritative.
    return {
        "verdict": "accept_with_notes", "issues": [], "notes": [note],
        "article_citations": [], "rerun_required": False,
    }


def _mark_stub_insufficient(state: dict, tid: str) -> None:
    """Record that a stubbed template's articles lack real verification."""
    ie = state.setdefault("insufficient_evidence_articles", [])
    for art in TEMPLATE_ARTICLES.get(tid, []):
        if art not in ie:
            ie.append(art)


def node_phase1_stub(state: dict) -> dict:
    """Phase 1 stub — used when ScopeAgent is not wired."""
    logger.info("Engagement %s: Phase 1 (Scope) — stub", state["engagement_id"])
    for tid in ["T02_system_card", "T03_annex_iii_mapping",
                "T04_risk_tier_decision", "T05_art43_decision"]:
        state["phase_artefacts"][tid] = _stub_artefact(state["engagement_id"], tid)
        state["verifier_critiques"][tid] = _stub_critique(
            "Phase 1 stub — no real ScopeAgent analysis performed."
        )
        _mark_stub_insufficient(state, tid)
    return state
