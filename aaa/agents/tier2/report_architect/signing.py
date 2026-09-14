"""Finding F15 — a signature is a claim, and it was the only ungated one.

Case 01 call #035: the ReportArchitect returned ``report_signed: true`` beside
``summary: ""``, ``artefact_uri: ""`` and ``confidence: 0.0``.  The reply was a
retrieval plan; the flag asserting that the audit report was signed rode along
with it.  Nothing anywhere read the flag, let alone gated it — ``report_signed``
appeared exactly once in the repository, in the Phase 6 prompt's REPORT FORMAT
skeleton, pre-set to ``true``.  The model emitted the value it was shown.

In an assurance product the signature is the strongest claim the system makes,
so it should be the most heavily guarded field.  Two rules follow:

*The runtime derives it; the model never asserts it.*  A signature attested by
the same party that drafted the narrative is not a control.  The model's own
``report_signed`` is discarded and, when it claims one, logged — see
``report_architect.llm``.

*It is withheld with reasons, not silently.*  :func:`signing_status` returns the
conditions that failed, and they travel into the delivered T18 as
``signature_withheld`` so a reader sees *why* a report is unsigned rather than
merely that it is.

The conditions are what "signed" has to mean here: the report is reachable at a
URI, it says something (a non-empty executive summary), an assurance narrative
was actually synthesised rather than falling back to machine-assembled
boilerplate, the evidence it cites is still reachable after this process exits
(fix 22 / P9), and the engagement is not still waiting on its human reviewer.  A
``DISCLAIMER_OF_OPINION`` is deliberately **not** a bar — under ISAE 3000 a
disclaimer is a conclusion reached and signed, not a failure to conclude.

The evidence condition is the one the *report* cannot see for itself.  Every
other field it carries is inspectable in the payload; whether ``minio://`` is an
address or a fiction is a property of the store, so it is passed in.

Evaluated after ``report_render`` and before the T18 is stored, so the flag
reaches the delivered report and the stored artefact alike.
"""
from __future__ import annotations

from typing import Any


def signing_status(t18: dict[str, Any], report_uri: str,
                   llm_summary: str | None, evidence_durable: bool) -> tuple[bool, list[str]]:
    """Decide whether the assembled report may be reported as signed.

    :param t18: The final T18 audit-report payload.
    :param report_uri: URI the rendered report is reachable at ("" when the
        render degraded and produced nothing to sign).
    :param llm_summary: Executive summary returned by the assurance synthesis,
        or ``None``/empty when it fell back to deterministic assembly.
    :param evidence_durable: Whether the evidence store's URIs outlive this
        process (``EvidenceStore.is_durable``).  Required rather than defaulted:
        a signature must not be granted by a caller that forgot to say.
    :returns: ``(signed, withheld_reasons)``; reasons are empty when signed.
    """
    reasons: list[str] = []
    if not str(report_uri or "").strip():
        reasons.append("the report was not rendered to a retrievable URI")
    if not str(t18.get("executive_summary") or "").strip():
        reasons.append("the report has no executive summary")
    if not str(llm_summary or "").strip():
        reasons.append("assurance synthesis did not run — the narrative is "
                       "machine-assembled, not an auditor's")
    if not evidence_durable:
        reasons.append("the evidence store does not persist beyond this run — "
                       "the minio:// URIs this report cites will not resolve")
    if t18.get("report_status") != "FINAL":
        reasons.append("the engagement is pending human review")
    return not reasons, reasons


__all__ = ["signing_status"]
