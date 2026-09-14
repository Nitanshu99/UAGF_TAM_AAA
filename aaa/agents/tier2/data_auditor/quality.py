"""Quality-verdict derivation and finding translation for Phase 2."""
from __future__ import annotations

from typing import Any

from aaa.tools.findings import make_finding


def quality_verdict(miss_result: dict, balance_result: dict, pii_result: dict) -> str:
    """Derive the overall quality verdict from tool results."""
    issues = []
    if miss_result.get("high_missingness_columns"):
        issues.append("high_missingness")
    if balance_result.get("imbalance_severity") in {"moderate", "severe"}:
        issues.append("class_imbalance")
    if pii_result.get("entities_found"):
        severities = {e["severity"] for e in pii_result["entities_found"]}
        if "critical" in severities:
            return "FAIL"
        if "high" in severities:
            issues.append("pii_high_severity")
    if not issues:
        return "PASS"
    return "PASS_WITH_OBSERVATIONS"


def verdict_findings(verdict: str, miss_result: dict, balance_result: dict,
                     pii_result: dict) -> list[dict[str, Any]]:
    """Translate the quality verdict into Art. 10 findings."""
    if verdict == "FAIL":
        return [make_finding(
            finding_id="P2-DQ-FAIL",
            description="Critical data-quality / PII issue detected in the training data.",
            materiality="material",
            articles=["Art.10"],
            source_phase="P2",
            recommendation="Remediate the dataset before the system can be considered compliant.",
        )]
    if verdict == "PASS_WITH_OBSERVATIONS":
        issues = []
        if miss_result.get("high_missingness_columns"):
            issues.append("high missingness columns")
        if balance_result.get("imbalance_severity") in {"moderate", "severe"}:
            issues.append(f"class imbalance ({balance_result.get('imbalance_severity')})")
        if any(e.get("severity") == "high" for e in pii_result.get("entities_found", [])):
            issues.append("high-severity PII present")
        return [make_finding(
            finding_id="P2-DQ-OBS",
            description="Data-quality observations: " + (", ".join(issues) or "minor issues") + ".",
            materiality="possibly_material",
            articles=["Art.10"],
            source_phase="P2",
            recommendation="Address the noted data-quality observations.",
        )]
    return []
