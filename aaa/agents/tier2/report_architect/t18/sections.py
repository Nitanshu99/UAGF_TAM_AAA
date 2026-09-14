"""Section builders for the T18 audit report."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.report_architect.constants import kpi_band
from aaa.platform.state.admission import admitted_artefacts, artefact_verdict
from aaa.platform.state.artefact_keys import base_template_id


def embedded_artefacts(state: dict[str, Any]) -> dict[str, Any]:
    """Build the T18 ``embedded_artefacts`` block, dropping stub URIs.

    The block is the report's *manifest* — everything the engagement produced —
    so an artefact the Verifier rejected stays in it and is labelled, rather
    than being filtered out.  Filtering would leave a reader unable to tell a
    model card that was produced and sent back from one that was never produced
    at all, which is a worse report than the over-claiming one this replaces
    (fix 21 makes the same argument one deliverable over).

    :param state: Declaration summary carrying ``phase_artefacts`` and
        ``verifier_critiques``.
    :returns: Embedded-artefact references keyed by template id, each carrying
        the Verifier's verdict and whether that verdict admits it.
    """
    admitted = admitted_artefacts(state)
    # A tier-3 spawn's key is `<template_id>@<spawn>` (P5), so the ref's own
    # ``template_id`` — not the slot it occupies — names the schema it meets.
    return {
        tid: {"uri": ref.get("uri", ""), "sha256": ref.get("sha256", ""),
              "template_id": ref.get("template_id") or base_template_id(tid),
              "verifier_verdict": artefact_verdict(state, tid),
              "admitted": tid in admitted}
        for tid, ref in (state.get("phase_artefacts", {}) or {}).items()
        if isinstance(ref, dict) and ref.get("uri") and "stub" not in ref.get("uri", "")
    }


def metadata_section(decl: dict[str, Any], stage_a: dict[str, Any]) -> dict[str, Any]:
    """Build the T18 ``engagement_metadata`` block.

    :param decl: Declaration summary from the dispatch.
    :param stage_a: Stage A triage payload.
    :returns: Engagement-metadata section dictionary.
    """
    return {
        "provider_name": stage_a.get("provider_name", ""),
        "deployer_name": stage_a.get("deployer_name"),
        "system_name": stage_a.get("system_name", ""),
        # Was "1.0" when undeclared, which T09 then contradicted.
        "version": str(stage_a.get("version") or "not declared"),
        "intended_purpose": stage_a.get("intended_purpose"),
        "modality": decl.get("modality", "tabular"),
        "risk_tier": decl.get("risk_tier", "high"),
        "deployment_context": decl.get("deployment_context", "b2b"),
        "is_llm_or_agentic": bool(decl.get("is_llm_or_agentic", False)),
        "annex_iii_sections": decl.get("annex_iii_sections", []),
    }


def kpis_section(ics: float | None, cs: float | None, rc: float | None) -> dict[str, Any]:
    """Build the T18 ``kpis`` block with banding.

    :param ics: KPI0 intake-completeness score.
    :param cs: KPI1 completeness score.
    :param rc: KPI2 regulatory-coverage percentage.
    :returns: KPI section dictionary.
    """
    return {
        "intake_completeness_score": ics,
        "completeness_score": cs,
        "regulatory_coverage_pct": rc,
        "kpi0_band": kpi_band(ics),
        "kpi1_band": kpi_band(cs),
        "kpi2_band": kpi_band(rc, pct=True),
    }


def executive_summary(engagement_id: str, final_verdict: str, n_blocking: int,
                      ics: float | None, cs: float | None, rc: float | None) -> str:
    """Compose the deterministic executive summary for T18.

    :param engagement_id: Engagement identifier.
    :param final_verdict: The engagement's final verdict.
    :param n_blocking: Number of blocking findings.
    :param ics: KPI0 intake-completeness score.
    :param cs: KPI1 completeness score.
    :param rc: KPI2 regulatory-coverage percentage.
    :returns: Executive-summary paragraph.
    """
    kpis = (f"KPI0={ics:.2f}" if ics is not None else "KPI0=n/a",
            f"KPI1={cs:.2f}" if cs is not None else "KPI1=n/a",
            f"KPI2={rc:.1f}%" if rc is not None else "KPI2=n/a")
    return (f"Autonomous AI audit complete for engagement {engagement_id}. "
            f"Final verdict: {final_verdict}. {', '.join(kpis)}. "
            f"Blocking findings: {n_blocking}. "
            "See embedded artefacts T01a–T17 for full evidence chain.")
