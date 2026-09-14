"""Verification-delta assembly for the Phase 4 report."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.output_fairness.context import FairnessInputs, SuiteResult
from aaa.tools.findings import backfill_finding_evidence, collect_evidence_uris


def build_delta(message: dict[str, Any], inp: FairnessInputs, suite: SuiteResult,
                t13: dict[str, Any], uris: dict[str, str]) -> dict[str, Any]:
    """Assemble the ``declaration_verification_delta`` for the Report.

    :param message: Original dispatch message.
    :param inp: Phase 4 inputs with findings and insufficiency flags.
    :param suite: Fairness suite result.
    :param t13: T13 sampling-log content.
    :param uris: Stored artefact URIs keyed by template id.
    :returns: Delta dictionary including any HITL escalation.
    """
    delta: dict[str, Any] = {"phase_artefacts": {
        template_id: {"uri": uri, "sha256": "", "template_id": template_id}
        for template_id, uri in uris.items()}}
    # F11 (finding S18): the cohorts each metric was computed over, promoted from
    # inside T12 onto the state so the S6 hand-off can carry them without
    # resolving an artefact URI. S6 read `sensitive_feature_columns` as a list of
    # names and concluded `age` should not be there because it is numeric — not
    # knowing the suite had already binned it into five bands (smallest n=49) and
    # that it was the only attribute in the case that yielded a verdict at all.
    # Names alone cannot carry that; this is the same record T12 keeps.
    resolutions = [a["resolution"] for a in suite.per_attribute if a.get("resolution")]
    if resolutions:
        delta["sensitive_feature_groups"] = resolutions
    evidence_pool = collect_evidence_uris(
        message.get("evidence_uris", []), list(uris.values()))
    backfill_finding_evidence(inp.findings, evidence_pool)
    if inp.findings:
        delta["blocking_findings"] = inp.findings
    if inp.insufficient:
        delta["insufficient_evidence_articles"] = sorted(inp.insufficient)
    discriminatory = t13["discriminatory_pattern_detected"]
    material = any(f.get("materiality") == "material" for f in inp.findings)
    if not (suite.overall_verdict == "FAIL" or discriminatory
            or material or inp.insufficient):
        return delta
    delta["hitl_required"] = True
    reasons = []
    if suite.overall_verdict == "FAIL":
        reasons.append(f"Phase 4 fairness verdict is FAIL ({suite.overall_verdict}).")
    if discriminatory:
        reasons.append(f"Discriminatory pattern flagged in output sample "
                       f"({t13['toxicity_results']['flagged_count']} entries).")
    if inp.insufficient:
        reasons.append("Fairness not independently verifiable: "
                       + ", ".join(sorted(inp.insufficient)) + ".")
    delta["hitl_reason"] = " ".join(reasons) or "Phase 4 escalation."
    return delta
