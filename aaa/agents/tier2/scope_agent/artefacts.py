"""Build, annotate, and store the four Phase 1 artefacts (T02–T05)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aaa.agents.tier2.scope_agent.t02_t03 import build_t02, build_t03
from aaa.agents.tier2.scope_agent.t04 import build_t04, transparency_basis
from aaa.agents.tier2.scope_agent.t04_t05 import build_t05
from aaa.tools.findings import collect_evidence_uris


def build_and_store_artefacts(agent: Any, ctx: dict[str, Any],
                              llm_summary: str | None, prompt_note: str,
                              ) -> dict[str, str]:
    """Assemble T02–T05, annotate provenance, and persist them.

    :param agent: The ScopeAgent (evidence store + name).
    :param ctx: Processing context (see ``ScopeAgent.process``).
    :param llm_summary: The LLM narrative; it no longer replaces T02's summary, which is
        built from T02's own fields (kept for the call signature and the Report).
    :param prompt_note: Prompt-provenance note appended to each narrative.
    :returns: ``{template_id: uri}`` for the four stored artefacts.
    """
    engagement_id, t01a = ctx["engagement_id"], ctx["t01a"]
    now = datetime.now(timezone.utc).isoformat()
    t02 = build_t02(engagement_id, t01a, ctx["verified_modality"], ctx["is_llm_or_agentic"],
                    ctx["verification_map"], ctx["gpai_result"], ctx["art5_prohibited"], now)
    t03 = build_t03(engagement_id, ctx["annex_entries"], ctx["verified_risk_tier"],
                    ctx["art5_prohibited"], now, transparency_basis(t01a, ctx["verified_risk_tier"]))
    t04 = build_t04(engagement_id, t01a.get("declared_risk_tier", "minimal"),
                    ctx["verified_risk_tier"], ctx["art5_prohibited"],
                    ctx["verified_sections"], now, t01a)
    t05 = build_t05(engagement_id, ctx["art43"], ctx["preview_procedure"],
                    ctx["art43_delta"], ctx["pseudo_state"], now, t01a.get("declared_risk_tier"))
    # The summary is T02's own; the LLM's prose feeds the phase Report only (T-20260914-010).
    t02["phase1_summary"] = f"{t02['phase1_summary']} {prompt_note}".strip()
    t03["classification_narrative"] = f"{t03['classification_narrative']} {prompt_note}".strip()
    t04["risk_tier_rationale"] = f"{t04['risk_tier_rationale']} {prompt_note}".strip()
    # M16: the binding statement is the artefact's legal declaration, and the
    # Verifier scored a `major` issue against carrying `source=PROMPT.md,
    # prompt_version_hash=…` inside it. The provenance is kept — it is real
    # audit-trail — in a field of its own, where nothing reads it as part of the
    # conformity conclusion.
    t05["prompt_provenance"] = prompt_note

    # Stamp the inspected provenance (intake URIs + retrieved client-doc chunks)
    # onto each artefact so the Verifier can confirm claim-level evidence linkage.
    cited_evidence = collect_evidence_uris(ctx["evidence_uris"], ctx["client_doc_hits"])
    for artefact in (t02, t03, t04, t05):
        artefact.setdefault("evidence_uris", cited_evidence)

    payloads = {"T02_system_card": t02, "T03_annex_iii_mapping": t03,
                "T04_risk_tier_decision": t04, "T05_art43_decision": t05}
    return {
        tid: agent.store.store_artefact(engagement_id, "phase_1", tid, payload, agent.name)
        for tid, payload in payloads.items()
    }
