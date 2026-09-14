"""Governance section (S4 maturity scores + radar figure) for the PDF."""
from __future__ import annotations

from typing import Any

from reportlab.platypus import Spacer

from aaa.tools.report_render.pdf.elements import keep_section, section
from aaa.tools.report_render.pdf.images import fetch_image
from aaa.tools.report_render.pdf.tables import kv_table


def build_governance(state: dict[str, Any], t18: dict[str, Any], store: Any) -> list[Any]:
    """Build the AI-governance maturity section from the CGSA surface.

    :param state: The audit state carrying the ``cgsa_*`` fields.
    :type state: dict[str, Any]
    :param t18: The T18 payload (radar figure URI).
    :type t18: dict[str, Any]
    :param store: Evidence store for figure resolution; may be ``None``.
    :type store: Any
    :returns: Section flowables (empty when no governance data is present).
    :rtype: list[Any]
    """
    score = state.get("cgsa_composite_maturity_score")
    if score is None:
        return []
    domains = state.get("cgsa_domain_scores") or {}
    rows = [("Composite maturity", f"{score}  ({state.get('cgsa_composite_maturity_label') or '—'})"),
            ("Governance verdict", state.get("cgsa_governance_verdict") or "—"),
            # Q18: the cover already shows "Regulatory coverage", which is the
            # audit's own KPI 2 over in-scope articles. This is the governance
            # partner's control coverage — a different measurement entirely.
            ("CGSA control coverage",
             f"{state.get('cgsa_eu_ai_act_coverage_pct') or 0:.1f}% of the 38 controls "
             f"mapped to EU AI Act obligations")]
    rows += [(f"Domain — {name}", str(value)) for name, value in sorted(domains.items())]
    flow = section("AI governance maturity",
                   "38-control governance assessment of the provider's management system (Art. 9 / 17).")
    flow.append(kv_table(rows))
    kept = keep_section(flow)
    radar = fetch_image(t18.get("maturity_radar_uri"), store, 11, 9)
    if radar is not None:
        kept += [Spacer(1, 8), radar]
    return kept
