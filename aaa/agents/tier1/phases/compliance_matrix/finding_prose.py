"""The prose one finding contributes to a rationale, and how a long list of it is cut."""
from __future__ import annotations

#: How much finding prose a rationale may carry before it is cut.
_MAX_DESCS = 300


def _clip(text: str, limit: int = _MAX_DESCS) -> str:
    """Cut *text* at the last sentence that fits, never mid-word (Q15).

    The old ``[:300]`` produced ``"…is FAIL (d."`` in the delivered PDF, four
    times over. A rationale that stops mid-token reads as corruption rather
    than as a summary, so the cut falls back through sentence, then word.

    :param text: Joined finding descriptions.
    :param limit: Maximum characters.
    :returns: The clipped text, ellipsised when anything was dropped.
    """
    if len(text) <= limit:
        return text
    head = text[:limit]
    for sep in ("; ", ". "):
        cut = head.rfind(sep)
        if cut > limit // 2:
            return head[:cut + 1].rstrip() + " …"
    return head[:head.rfind(" ") if " " in head else limit].rstrip() + " …"


def _prose(finding: dict) -> str:
    """The finding's own account of the gap, whichever shape carries it.

    Two shapes reach one list. A phase finding writes its prose under
    ``description``; a CGSA governance finding writes it under ``finding``,
    which ``schemas/cgsa/v1.0.0`` requires and alongside which it names no
    ``description`` at all. Reading only ``description`` therefore rendered an
    article failing purely on governance controls as ``"; ; ; ."`` — Mariposa's
    Art. 17, stating a material non-conformity with no reason attached.

    ``finding`` is *preferred* rather than merely fallen back to. Where the S5
    dialect supplies both, its ``description`` is a counter — "Hard constraint
    violated for control C02." across 26 of 32 findings — and the substantive
    sentence is the one :func:`~aaa.tools.cgsa_ingest.s5.fields.finding_fields`
    placed in ``finding``.

    :param finding: A phase or CGSA blocking finding.
    :returns: The prose, named by the control it belongs to where the finding
        identifies one, or ``""`` when it carries none.
    """
    text = str(finding.get("finding") or finding.get("description") or "").strip()
    if not text:
        return ""
    # Only a governance finding identifies a control; a phase finding carries
    # the key as ``None``, so its sentence is left exactly as it was.
    control = str(finding.get("control_id") or "").strip()
    if not control:
        return text
    name = str(finding.get("control_name") or "").strip()
    return f"{control} ({name}): {text}" if name else f"{control}: {text}"


__all__ = ["_clip", "_prose"]
