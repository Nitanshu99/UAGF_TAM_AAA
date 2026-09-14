"""Verdict derivation for the deterministic Phase 2 analysis."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.data_auditor.diffing import diff_declared_data
from aaa.agents.tier2.data_auditor.quality import quality_verdict, verdict_findings
from aaa.tools.findings import make_finding


def apply_verdict(data_available: bool, dossier: dict[str, Any],
                  profile_result: dict[str, Any], miss_result: dict[str, Any],
                  balance_result: dict[str, Any], pii_result: dict[str, Any],
                  findings: list[dict[str, Any]], insufficient: set[str],
                  special_cat_delta: bool) -> str:
    """Derive the verdict and extend the findings / insufficient sets.

    :param data_available: Whether a real dataset could be loaded.
    :param dossier: Stage B dossier (or T01b) used for declaration diffing.
    :param profile_result: ``data_profile`` output.
    :param miss_result: ``missingness_scan`` output.
    :param balance_result: ``class_balance`` output.
    :param pii_result: ``pii_scan`` output.
    :param findings: Findings list extended in place.
    :param insufficient: Insufficient-evidence articles extended in place.
    :param special_cat_delta: Undeclared special-category data was detected.
    :returns: The Phase 2 data-quality verdict.
    """
    if not data_available:
        verdict = "INSUFFICIENT_EVIDENCE"
        insufficient.update({"Art.10", "Art.10§2(f)"})
    else:
        verdict = quality_verdict(miss_result, balance_result, pii_result)
        findings.extend(verdict_findings(verdict, miss_result, balance_result, pii_result))
        findings.extend(diff_declared_data(dossier, profile_result))
    if special_cat_delta:
        findings.append(make_finding(
            finding_id="P2-SPECIAL-CAT",
            description="PII scan detected undeclared special-category data in the dataset.",
            materiality="material",
            articles=["Art.10"],
            source_phase="P2",
            recommendation="Declare special-category data and document the "
                           "Art. 10 §5 lawful basis.",
        ))
    return verdict
