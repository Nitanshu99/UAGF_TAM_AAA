"""Step 3, *The dossier*: the nine Annex IV sections' free text, metrics and standards."""
from __future__ import annotations

import json

from playwright.sync_api import Page

from scripts.wizard_fill import form_spec as spec
from scripts.wizard_fill.widgets import fill_text, open_tab


def step3_stage_b(page: Page, stage_b: dict) -> None:
    """Fill the *The dossier* tab from the Stage B declaration.

    :param page: The page.
    :param stage_b: The Stage B declaration.
    """
    open_tab(page, spec.TABS["stage_b"])
    for label, field in spec.STEP3_STAGE_B_TEXT.items():
        value = str(stage_b.get(field) or "")
        if value:
            fill_text(page, label, value)
    # The wrapped form keeps the two blocks apart. Merging them into one flat object
    # filed an operational ratio from the robustness block under
    # accuracy_metrics, and dropped the latency figures (T-20260913-028).
    accuracy = stage_b.get("accuracy_metrics") or {}
    robustness = stage_b.get("robustness_metrics") or {}
    metrics = ({"accuracy_metrics": accuracy, "robustness_metrics": robustness}
               if robustness else accuracy)
    raw: dict[str, str] = {
        "accuracy_metrics": json.dumps(metrics, indent=2) if metrics else "",
        "lifecycle_change_log": "\n".join(stage_b.get("lifecycle_change_log") or []),
        "harmonised_standards": ", ".join(stage_b.get("harmonised_standards") or []),
        "other_standards": ", ".join(stage_b.get("other_standards") or []),
        "tool_inventory": ", ".join(stage_b.get("tool_inventory") or []),
    }
    for label, field in spec.STEP3_STAGE_B_RAW.items():
        if raw[field]:
            fill_text(page, label, raw[field])


__all__ = ["step3_stage_b"]
