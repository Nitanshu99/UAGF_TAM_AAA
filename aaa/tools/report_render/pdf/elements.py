"""Reusable platypus building blocks for the customer-facing PDF report."""
from __future__ import annotations

import logging
from typing import Any

from reportlab.lib.units import cm
from reportlab.platypus import CondPageBreak, KeepTogether, Paragraph, Spacer

from aaa.tools.report_render.pdf.theme import STYLES

logger = logging.getLogger(__name__)


def section(title: str, sub: str = "") -> list[Any]:
    """Build a section heading (title + optional muted subtitle).

    :param title: Section heading text.
    :type title: str
    :param sub: Optional one-line explanation under the heading.
    :type sub: str
    :returns: Flowables for the heading block.
    :rtype: list[Any]
    """
    flow: list[Any] = [Paragraph(title, STYLES["h1"])]
    if sub:
        flow.append(Paragraph(sub, STYLES["muted"]))
    flow.append(Spacer(1, 4))
    return flow


def keep_section(flow: list[Any], min_cm: float = 5.0) -> list[Any]:
    """Keep a section's heading with the block it introduces.

    Adding the measured-evidence and roadmap blocks pushed the report from five
    pages to seven and left two governance rows stranded at the top of one page
    and three dossier rows alone on another. ``CondPageBreak`` moves a heading
    that cannot carry *min_cm* of its own content to the next page;
    ``KeepTogether`` holds the block itself intact when it fits on one, and
    degrades to an ordinary split when it does not.

    :param flow: Heading flowables followed by the block they introduce.
    :param min_cm: Space the heading must have below it to stay put.
    :returns: The same flowables, page-break guarded.
    """
    return [CondPageBreak(min_cm * cm), KeepTogether(flow)]
