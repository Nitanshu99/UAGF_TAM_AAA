"""Run the report architect phase and file its artefacts."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from aaa.agents.base import Dispatch, Report
from aaa.agents.tier2.report_architect.charts import attach_charts
from aaa.agents.tier2.report_architect.llm import run_llm_synthesis
from aaa.agents.tier2.report_architect.report import assemble_report
from aaa.agents.tier2.report_architect.signing import signing_status
from aaa.agents.tier2.report_architect.t17 import build_t17
from aaa.agents.tier2.report_architect.t18 import build_t18
from aaa.tools.report_render import report_render
from aaa.tools.template_render import template_render

logger = logging.getLogger(__name__)


async def run_report_architect(agent: Any, message: Dispatch) -> Report:
    """Run the report architect phase and file its artefacts.

    :param agent: The agent making the call and holding the evidence store.
    :param message: The dispatch to act on.
    :returns: The phase Report.
    """
    decl = message.get("declaration_summary", {})
    engagement_id: str = decl.get("engagement_id") or message["phase_id"]
    now = datetime.now(timezone.utc).isoformat()

    t17 = build_t17(engagement_id, decl, now)
    t17_ref = template_render("T17_compliance_matrix", t17,
                              engagement_id=engagement_id, phase="phase_6",
                              agent_name=agent.name, store=agent.store)
    # dict() casts: downstream helpers take plain dicts, and pyright will
    # not assign TypedDicts (ArtefactRef / Dispatch) to dict[str, Any].
    t18 = build_t18(engagement_id, decl, dict(t17_ref), now)
    attach_charts(agent, engagement_id, decl, t18)
    llm_summary, prompt_note = await run_llm_synthesis(agent, dict(message), decl, t17, t18)
    t18["executive_summary"] = (
        f"{llm_summary or t18['executive_summary']} {prompt_note}".strip())

    rendered = report_render(t18, engagement_id=engagement_id,
                             store=agent.store, agent_name=agent.name,
                             t17_payload=t17, audit_state=decl)
    t18["rendered_report"] = {
        "pdf_uri": rendered.get("pdf_uri"),
        "pdf_bytes_size": rendered.get("pdf_bytes_size"),
        "json_uri": rendered["json_uri"],
        "renderer": rendered.get("renderer"),
    }
    # F15: the signature is derived here, from the report that was actually
    # produced, and stamped before the T18 is stored so the delivered
    # artefact carries both the claim and any reason it was withheld.
    signed, withheld = signing_status(t18, rendered.get("json_uri", ""), llm_summary,
                                      agent.store.is_durable)
    t18["report_signed"] = signed
    t18["signature_withheld"] = withheld
    if not signed:
        logger.warning("Engagement %s: T18 issued UNSIGNED — %s.",
                       engagement_id, "; ".join(withheld))
    t18_ref = template_render("T18_audit_report", t18,
                              engagement_id=engagement_id, phase="phase_6",
                              agent_name=agent.name, store=agent.store)
    return assemble_report(t17, dict(t17_ref), t18, dict(t18_ref), rendered,
                           llm_summary, prompt_note)


__all__ = ["run_report_architect"]
