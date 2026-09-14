"""The robustness section's rows, read from the probe's own result."""
from __future__ import annotations

from typing import Any

from aaa.tools.report_render.numbers import fmt


def robustness_rows(t11: dict[str, Any]) -> list[tuple[str, str]]:
    """Clean accuracy and the measured perturbation curve from T11."""
    if not t11:
        return []
    rows: list[tuple[str, str]] = [
        ("Verdict", str(t11.get("overall_robustness_verdict") or "—")),
        ("Clean accuracy", fmt(t11.get("clean_accuracy"))),
        ("Evaluation sample", str(t11.get("evaluation_sample_size") or "—")),
    ]
    for probe in t11.get("probes") or []:
        rows.append((f"  {probe.get('probe_name', 'probe')}",
                     f"adversarial accuracy {fmt(probe.get('adversarial_accuracy'))}"))
    rows.append(("Worst observed", fmt(t11.get("min_adversarial_accuracy"))))
    if t11.get("skipped_reason"):
        rows.append(("Degraded", str(t11["skipped_reason"])))
    return rows


__all__ = ["robustness_rows"]
