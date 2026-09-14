"""What the filled form says: completeness, scope, documents, the prior CGSA."""
from __future__ import annotations

import re

from playwright.sync_api import Page

from scripts.wizard_fill import form_spec as spec
from scripts.wizard_fill.widgets import open_tab, selected


def report_state(page: Page) -> str:
    """Summarise what the filled form now says.

    :param page: The page, sitting on step 3.
    :returns: A short report: completeness, scope, documents, the prior CGSA and the
        declared ranking columns.
    """
    # `inner_text` skips hidden tab panels, and the CGSA note is on the first
    # tab while filling ends on the third — reading without switching back
    # reports "none found" for an assessment that is attached.
    open_tab(page, spec.TABS["documents"])
    slots = re.search(r"(\d+) of (\d+) document slots filled",
                      page.locator("body").inner_text())
    ranking = [selected(page, label) or "—" for label in spec.RANKING_SELECTS]
    open_tab(page, spec.TABS["stage_a"])
    text = page.locator("body").inner_text()
    meter = re.search(r"(\d+)% of 80% needed", text)
    scope = re.search(r"(Your system is in scope[^\n]*|This may sit outside[^\n]*)", text)
    cgsa = ("evaluated" if "We found your governance self-assessment" in text
            and "unscored" not in text else
            "unscored" if "unscored" in text else "none found")
    return "\n".join([
        f"  completeness : {meter.group(1) + '%' if meter else '?'} of the 80% gate",
        f"  documents    : {slots.group(0) if slots else '?'}",
        f"  scope        : {scope.group(1) if scope else '?'}",
        f"  prior CGSA   : {cgsa}",
        f"  ranking      : query {ranking[0]}, rank {ranking[1]}",
    ])


__all__ = ["report_state"]
