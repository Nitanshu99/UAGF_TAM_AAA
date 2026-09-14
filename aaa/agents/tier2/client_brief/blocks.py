"""The fixed prose blocks and the header the client brief opens with."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aaa.agents.tier2.client_brief.constants import verdict_label

#: Section heading → the overview key it renders.
_OVERVIEW_BLOCKS: tuple[tuple[str, str], ...] = (
    ("In short", "overall_explanation"),
    ("What is already working", "what_is_working_well"),
    ("What is holding the result back", "what_is_blocking_the_verdict"),
    ("What we could not check", "what_could_not_be_checked"),
    ("What to fix first", "top_priorities"),
)
#: Sub-heading → the section key it renders, in reading order.
_ARTICLE_BLOCKS: tuple[tuple[str, str], ...] = (
    ("What you told us", "what_you_told_us"),
    ("What the evidence shows", "what_the_evidence_shows"),
    ("Why this is the result", "why_this_verdict"),
    ("The rule this falls under", "regulatory_basis"),
    ("What is working here", "what_is_working"),
    ("What to do", "what_to_do"),
)
_FOOTER = (
    "## How to read this document\n\n"
    "This brief explains, in plain language, the same result as the formal audit "
    "report. Where the two differ in wording, the formal report and its evidence "
    "URIs govern.\n\n"
    "**Met** means the requirement was assessed against admitted evidence and no "
    "finding was raised. **Not met** means a finding contradicts the requirement. "
    "**Could not be checked** is neither: the audit could not reach a conclusion "
    "on the material supplied, and the requirement still applies to you.\n"
)
def _header(state: dict[str, Any], engagement_id: str) -> str:
    """Render the title block and the headline result."""
    stage_a = (state.get("client_submission") or {}).get("stage_a") or {}
    verdict = str(state.get("final_verdict") or "not recorded")
    opinion = (state.get("auditor_opinion") or {}).get("opinion_type") or "not recorded"
    name = stage_a.get("system_name") or engagement_id
    return (f"# {name} — what the compliance audit found\n\n"
            f"{stage_a.get('provider_name', 'Provider not recorded')} · "
            f"{name} {stage_a.get('version', '')} · engagement `{engagement_id}` · "
            f"{datetime.now(timezone.utc).date().isoformat()}\n\n"
            f"> **Result: {verdict_label(verdict)} ({verdict}).** "
            f"Auditor's opinion: {opinion}.\n")


__all__ = ["_ARTICLE_BLOCKS", "_FOOTER", "_OVERVIEW_BLOCKS", "_header"]
