"""Executive summary, auditor opinion, and risk classification for the PDF."""
from __future__ import annotations

from typing import Any

from reportlab.platypus import Paragraph, Spacer

from aaa.tools.report_render.pdf.elements import section
from aaa.tools.report_render.pdf.tables import kv_table
from aaa.tools.report_render.pdf.theme import STYLES


def _scrub(text: str) -> str:
    """Drop internal prompt-metadata sentences from customer-facing prose.

    Q14: this split on ``". "`` and rejoined on ``" "``, which discarded every
    sentence terminator it split on. The model's executive summary is correctly
    punctuated; the delivered PDF rendered it as one unbroken run-on because the
    scrubber ate the full stops. The separator is put back.
    """
    kept = [s.strip() for s in text.split(". ")
            if not s.strip().startswith("Prompt metadata")]
    joined = ". ".join(s for s in kept if s).strip()
    if joined and not joined.endswith((".", "!", "?")):
        joined += "."
    return joined


def build_summary(t18: dict[str, Any], state: dict[str, Any]) -> list[Any]:
    """Build the executive summary + opinion + risk classification flowables.

    :param t18: The T18 audit-report payload.
    :type t18: dict[str, Any]
    :param state: The audit state (may be empty for legacy renders).
    :type state: dict[str, Any]
    :returns: Section flowables.
    :rtype: list[Any]
    """
    flow = section("Executive summary")
    flow.append(Paragraph(_scrub(t18.get("executive_summary") or ""), STYLES["body"]))
    opinion = t18.get("auditor_opinion") or {}
    if opinion.get("opinion_paragraph"):
        flow += section("Auditor opinion",
                        f"Opinion type: {opinion.get('opinion_type', '—')}")
        flow.append(Paragraph(opinion["opinion_paragraph"], STYLES["body"]))
    flow += section("Risk classification",
                    "Why this system falls under the EU AI Act's high-risk regime.")
    annex = ", ".join(f"Annex III §{s}" for s in state.get("declared_annex_iii_sections") or [])
    flow.append(kv_table([
        ("Risk tier", (state.get("risk_tier") or "—").upper()),
        ("Annex III scope", annex or "—"),
        ("Modality", state.get("modality") or "—"),
        ("Deployment context", state.get("deployment_context") or "—"),
        ("Art. 43 route", (t18.get("art43_decision") or {}).get("procedure") or "—"),
    ]))
    flow.append(Spacer(1, 6))
    return flow
