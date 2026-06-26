"""
aaa.tools.findings — Canonical finding constructors shared across phase agents.

A "real auditor" grounds every verdict in a traceable finding. Phase agents emit
findings via their ``declaration_verification_delta`` under the accumulator keys
``blocking_findings`` / ``positive_findings`` (see ``agent_runner._apply_delta``),
and the compliance-matrix node (WS5) reads ``materiality`` + ``eu_ai_act_articles``
to derive per-article verdicts.

The dict shape here is the union of what every downstream consumer already reads:
``report_architect._auditor_opinion`` / ``_management_response_shell`` /
``_build_t17`` and ``compliance_matrix.node_compliance_matrix``.

Materiality ladder (drives article verdicts in WS5):
  - ``material``           → contributes a FAIL to its articles.
  - ``possibly_material``  → contributes a PASS_WITH_OBSERVATIONS.
  - ``observation``        → informational; PASS_WITH_OBSERVATIONS note only.
"""
from __future__ import annotations

from typing import Any, Iterable, Literal

Materiality = Literal["material", "possibly_material", "observation"]

# Articles whose finding materiality should force a hard FAIL when material.
BLOCKING_MATERIALITY = "material"


def make_finding(
    *,
    finding_id: str,
    description: str,
    materiality: Materiality,
    articles: Iterable[str],
    source_phase: str,
    recommendation: str = "",
    control_id: str | None = None,
    declared: Any = None,
    observed: Any = None,
    evidence_uris: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build a canonical finding dict consumed by the report + compliance matrix."""
    return {
        "finding_id": finding_id,
        "description": description,
        "materiality": materiality,
        "eu_ai_act_articles": list(articles),
        "source_phase": source_phase,
        "recommendation": recommendation,
        "control_id": control_id,
        "declared": declared,
        "observed": observed,
        "evidence_uris": list(evidence_uris or []),
    }


def make_positive_finding(
    *,
    finding_id: str,
    description: str,
    articles: Iterable[str],
    source_phase: str,
    control_id: str | None = None,
    evidence_uris: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build a positive (corroborating) finding for the T18 positive register."""
    return {
        "finding_id": finding_id,
        "description": description,
        "materiality": "observation",
        "eu_ai_act_articles": list(articles),
        "source_phase": source_phase,
        "control_id": control_id,
        "evidence_uris": list(evidence_uris or []),
    }


def is_blocking(finding: dict[str, Any]) -> bool:
    """True if the finding's materiality should force a FAIL on its articles."""
    return finding.get("materiality") == BLOCKING_MATERIALITY


def articles_for(finding: dict[str, Any]) -> list[str]:
    """Return the EU AI Act articles a finding maps to (tolerant of legacy shapes)."""
    arts = finding.get("eu_ai_act_articles")
    if arts:
        return list(arts)
    single = finding.get("article")
    return [single] if single else []


__all__ = [
    "Materiality",
    "make_finding",
    "make_positive_finding",
    "is_blocking",
    "articles_for",
]
