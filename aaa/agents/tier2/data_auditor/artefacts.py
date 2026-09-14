"""Build, annotate, and store the three Phase 2 artefacts."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aaa.agents.tier2.data_auditor.declared_counts import declared_size
from aaa.agents.tier2.data_auditor.t06 import build_t06
from aaa.agents.tier2.data_auditor.t07 import build_t07
from aaa.agents.tier2.data_auditor.t08 import build_t08
from aaa.tools.regulatory_coverage.binding_notes import annotate_non_binding


def build_and_store_artefacts(agent: Any, engagement_id: str, t01a: dict, t01b: dict,
                              decl: dict, ctx: dict[str, Any], prompt_note: str) -> dict[str, str]:
    """Assemble T06–T08, annotate provenance, and persist them.

    :returns: ``{template_id: uri}`` for the three stored artefacts.
    """
    now = datetime.now(timezone.utc).isoformat()
    t06 = build_t06(engagement_id, t01a, t01b, decl, now, measured=ctx.get("measurement"),
                    found=ctx.get("t06_found"), label_bias=ctx.get("label_bias"))
    t07 = build_t07(engagement_id, ctx["profile_result"], ctx["miss_result"],
                    ctx["balance_result"], ctx["pii_result"], ctx["verdict"], now,
                    drift_result=ctx.get("drift_result"),
                    reference_uri=(t01b or {}).get("training_dataset_uri"),
                    label_bias=ctx.get("label_bias"), declared_size=declared_size(t01b, decl, ctx))
    t08 = build_t08(engagement_id, ctx["effective_special_cat"],
                    ctx["pii_result"], ctx["special_cat_delta"], now, found=ctx.get("t06_found"))
    t06["art10_compliance_notes"] = f"{t06['art10_compliance_notes']} {prompt_note}".strip()
    # A measurement narrative is built from this artefact's own fields. The LLM's
    # reply summarises the whole phase and quoted numbers the artefact does not hold —
    # T11 carried metric-suite accuracy and SHAP values beside its probe fields, and
    # the Verifier refused it (case 03, T-20260913-067). It stays the Report summary.
    t07["quality_narrative"] = f"{t07['quality_narrative']} {prompt_note}".strip()
    t08["compliance_narrative"] = f"{t08['compliance_narrative']} {prompt_note}".strip()
    for payload in (t06, t07, t08):
        annotate_non_binding(payload, decl.get("risk_tier"))

    uris = {
        tid: agent.store.store_artefact(engagement_id, "phase_2", tid, payload, agent.name)
        for tid, payload in (("T06_datasheet_for_datasets", t06),
                             ("T07_data_quality_report", t07),
                             ("T08_special_category_data_log", t08))
    }
    return uris
