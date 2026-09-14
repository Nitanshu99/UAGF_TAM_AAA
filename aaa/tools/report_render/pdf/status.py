"""Whether this report may be relied on — finding Q12.

Fix 10 derives ``report_signed`` and ``signature_withheld`` from the report that
was actually produced, and the run that exposed this recorded
``report_status: PROVISIONAL_PENDING_HITL``, ``report_signed: false`` and a
``hitl_reason`` naming six artefacts awaiting a human.  None of it reached the
PDF: the cover read ``FINAL VERDICT: FAIL`` and the words "provisional",
"unsigned" and "human review" appeared nowhere in the document.

The PDF is the artefact a client actually reads.  A signature withheld in a
JSON nobody opens is not a control, so the status is rendered where the verdict
is — on the cover, above the fold, in the same visual weight as the verdict it
qualifies.
"""
from __future__ import annotations

from typing import Any

from reportlab.platypus import Paragraph, Spacer

from aaa.tools.report_render.pdf.tables import badge, kv_table
from aaa.tools.report_render.pdf.theme import AMBER, GREEN, STYLES

#: Shown beside the verdict when the engagement has not been through review.
PROVISIONAL_NOTE = (
    "This report is <b>provisional</b>. It has not been signed, and the conclusions below "
    "are the automated assessment's own — they are subject to change on human review.")

SIGNED_NOTE = "This report is signed and may be relied on as issued."


def is_provisional(t18: dict[str, Any]) -> bool:
    """Whether the report is anything other than a signed, final one.

    :param t18: The T18 audit-report payload.
    :returns: ``True`` when the report is unsigned or not ``FINAL``.
    """
    return (t18.get("report_status") != "FINAL"
            or not t18.get("report_signed")
            or bool(t18.get("hitl_required")))


def verdict_label(t18: dict[str, Any]) -> str:
    """The verdict banner's text, marked provisional when it is.

    ``FINAL VERDICT`` on an unsigned, review-pending report is the claim Q12 is
    about; the word "FINAL" is dropped rather than qualified in a footnote.

    :param t18: The T18 audit-report payload.
    :returns: Banner text for the cover badge.
    """
    verdict = (t18.get("final_verdict") or "UNKNOWN").upper()
    return (f"PROVISIONAL VERDICT: {verdict}" if is_provisional(t18)
            else f"FINAL VERDICT: {verdict}")


def build_status(t18: dict[str, Any]) -> list[Any]:
    """Build the report-status block for the cover page.

    :param t18: The T18 audit-report payload.
    :returns: Flowables naming the signature state and any reasons it is withheld.
    """
    provisional = is_provisional(t18)
    flow: list[Any] = [Spacer(1, 10)]
    flow.append(badge("PROVISIONAL — PENDING HUMAN REVIEW" if provisional
                      else "SIGNED — FINAL", AMBER if provisional else GREEN))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph(PROVISIONAL_NOTE if provisional else SIGNED_NOTE, STYLES["body"]))

    withheld = [str(r) for r in (t18.get("signature_withheld") or []) if r]
    rows: list[tuple[str, str]] = [
        ("Report status", str(t18.get("report_status") or "—")),
        ("Signed", "no" if not t18.get("report_signed") else "yes"),
    ]
    if withheld:
        rows.append(("Signature withheld because",
                     "; ".join(withheld) + "."))
    if t18.get("hitl_reason"):
        rows.append(("Referred to human review", str(t18["hitl_reason"])))
    flow.append(Spacer(1, 6))
    flow.append(kv_table(rows))
    return flow


__all__ = ["PROVISIONAL_NOTE", "SIGNED_NOTE", "build_status", "is_provisional",
           "verdict_label"]
