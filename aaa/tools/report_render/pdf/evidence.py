"""Explainability & fairness and security & robustness sections for the PDF.

Each section leads with the measurements the phase actually produced, resolved
from the evidence store (Q13), and closes with the artefact references that
carry them. The landing zones (`xai_evidence` / `security_evidence`, populated
by internal tools or an external partner and never branded either way) provide
the reference rows; the numbers come from the artefacts themselves.
"""
from __future__ import annotations

from typing import Any

from reportlab.platypus import Paragraph

from aaa.tools.report_render.pdf.artefact_evidence import (
    explainability_rows,
    fairness_rows,
    resolve,
    robustness_rows,
)
from aaa.tools.report_render.pdf.elements import section
from aaa.tools.report_render.pdf.evidence_rows import _document, _measured
from aaa.tools.report_render.pdf.theme import STYLES


def build_evidence(state: dict[str, Any], store: Any = None) -> list[Any]:
    """Build both evidence sections: the measurements, then their provenance.

    :param state: The audit state (evidence zones populated or absent).
    :type state: dict[str, Any]
    :param store: Evidence store used to resolve T10 / T11 / T12; without one
        the sections degrade to the reference rows they carried before.
    :type store: Any
    :returns: Section flowables.
    :rtype: list[Any]
    """
    from aaa.integrations.security import InternalSecurityProvider
    from aaa.integrations.xai import InternalXAIProvider
    xai = state.get("xai_evidence") or InternalXAIProvider().evaluate(state)
    security = state.get("security_evidence") or InternalSecurityProvider().evaluate(state)

    flow = section("Explainability & fairness (Art. 13)",
                   "Feature attribution, model transparency, and output-fairness evidence.")
    flow += _measured(explainability_rows(resolve(state, store, "T10_explainability_report")),
                      "Feature attribution (T10)")
    flow += _measured(fairness_rows(resolve(state, store, "T12_output_fairness_report")),
                      "Output fairness (T12)")
    flow.append(Paragraph("Artefact references", STYLES["h2"]))
    flow += _document(xai)

    flow += section("Security & robustness (Art. 15)",
                    "Adversarial robustness, output sampling, and monitoring evidence.")
    flow += _measured(robustness_rows(resolve(state, store, "T11_robustness_report")),
                      "Robustness probes (T11)")
    flow.append(Paragraph("Artefact references", STYLES["h2"]))
    flow += _document(security)
    return flow
