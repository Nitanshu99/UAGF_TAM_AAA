"""Part 1 of the former ``triage_render`` module (auto-split)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from aaa.platform.repo_root import REPO_ROOT

_SCHEMA_PATH = REPO_ROOT / "templates" / "T01a_stage_a_triage.json"


with _SCHEMA_PATH.open() as _f:
    _T01A_SCHEMA: dict[str, Any] = json.load(_f)


_ANNEX_III_LABELS: dict[str, str] = {
    "1": "Biometrics (remote ID, categorisation, emotion recognition)",
    "2": "Critical infrastructure (energy, water, traffic)",
    "3": "Education and vocational training",
    "4": "Employment, workers management, self-employment",
    "5": "Access to essential private/public services",
    "6": "Law enforcement",
    "7": "Migration, asylum, border control",
    "8": "Administration of justice and democratic processes",
}


_MODALITY_LABELS: dict[str, str] = {
    "tabular": "Tabular / structured data classifier",
    "cv": "Computer vision",
    "nlp": "Natural language processing",
    "time_series": "Time-series / forecasting",
    "llm": "Large Language Model (LLM)",
    "agentic": "Agentic AI system (tool-using)",
    "gpai": "General-Purpose AI (GPAI) model",
}


_RISK_TIER_LABELS: dict[str, str] = {
    "high": "High-risk (Annex III)",
    "limited": "Limited risk (Art. 50 transparency obligations)",
    "minimal": "Minimal / no risk",
    "gpai": "General-Purpose AI (Arts. 51–55)",
}


@dataclass
class TriageRenderResult:
    """Output contract for triage_render."""
    is_valid: bool
    schema_errors: list[str] = field(default_factory=list)
    rendered: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the the rendered triage payload as a plain dict."""
        return {
            "is_valid": self.is_valid,
            "schema_errors": self.schema_errors,
            "rendered": self.rendered,
        }
