"""Part 1 of the former ``annex_iv_validator`` module (auto-split)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from aaa.platform.repo_root import REPO_ROOT

_SCHEMA_PATH = REPO_ROOT / "templates" / "T01b_annex_iv_dossier.json"


with _SCHEMA_PATH.open() as _f:
    _T01B_SCHEMA: dict[str, Any] = json.load(_f)


_L_BRANCH_MODALITIES = {"llm", "agentic", "gpai"}


_L_BRANCH_REQUIRED_FIELDS = [
    "system_prompt_uri",
    "rag_manifest_uri",
    "guardrail_config_uri",
    "golden_set_uri",
]


_AGENTIC_REQUIRED_FIELDS = ["tool_inventory"]


@dataclass
class FieldError:
    """A schema violation for one Annex IV field."""

    field: str
    section: int
    reason: str


@dataclass
class ConditionalFieldStatus:
    """Whether a conditionally-required field applies and is present."""

    field: str
    condition: str
    applicable: bool
    present: bool
