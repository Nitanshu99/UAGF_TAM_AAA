"""T14/T15 build-annotate-store step for Phase 5."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.governance_agent.acquire import source_note
from aaa.agents.tier2.governance_agent.context import gather_t15_evidence
from aaa.agents.tier2.governance_agent.decision import phase5_hitl
from aaa.agents.tier2.governance_agent.scope_note import cgsa_scope_note
from aaa.agents.tier2.governance_agent.t14 import build_t14
from aaa.agents.tier2.governance_agent.t15 import build_t15
from aaa.tools.cgsa_ingest import IngestResult


def build_and_store_artefacts(
    agent: Any, engagement_id: str, result: IngestResult, decl: dict[str, Any],
    spawn: dict[str, Any], risk_tier_mismatch: bool, now: str,
    t01b: dict[str, Any], llm_summary: str | None, prompt_note: str,
) -> tuple[dict, dict, str, str]:
    """Build T14 + T15, annotate with the prompt note, and persist them.

    T15 is built on the answers its questions find in the dossier and documents.

    :returns: ``(t14, t15, t14_uri, t15_uri)``.
    """
    scope = {"risk_tier": decl.get("risk_tier"), "binding_articles": decl.get("binding_articles")}
    t14 = build_t14(engagement_id, result, decl, spawn, risk_tier_mismatch, now)
    t15 = build_t15(engagement_id, t01b, result, now,
                    gather_t15_evidence(decl, engagement_id, t01b), scope=scope)
    # The artefact states the phase's own review decision (T-20260913-040).
    t14["hitl_required"], t14["hitl_reason"] = phase5_hitl(result, t15, risk_tier_mismatch)
    # The CGSA assessment's own narrative, not the LLM's retelling of it, which could
    # contradict the fields beside it as T02's did (T-20260914-010); the prose feeds the
    # phase Report. *llm_summary* is kept in the signature for that caller.
    del llm_summary
    t14["phase5_narrative_summary"] = (
        f"{t14['phase5_narrative_summary']}{source_note(result.state_delta.get('cgsa_source'))}"
        f"{cgsa_scope_note(result.payload, scope)} {prompt_note}".strip())
    t15["observations"] = list(t15.get("observations", [])) + [prompt_note]

    t14_uri = agent.store.store_artefact(
        engagement_id, "phase_5", "T14_governance_findings", t14, agent.name)
    t15_uri = agent.store.store_artefact(
        engagement_id, "phase_5", "T15_monitoring_logging_review", t15, agent.name)

    return t14, t15, t14_uri, t15_uri
