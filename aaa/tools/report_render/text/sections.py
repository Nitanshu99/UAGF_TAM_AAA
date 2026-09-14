"""Article 43, matrix, artefact, finding, and roadmap report sections."""
from __future__ import annotations

from typing import Any


def art43_matrix_lines(t18: dict[str, Any]) -> list[str]:
    """Render the Art. 43 decision and T17 compliance-matrix reference."""
    lines: list[str] = []
    art43 = t18.get("art43_decision") or {}
    if art43:
        lines += [
            "Article 43 — Conformity assessment procedure", "-" * 70,
            f"Procedure : {art43.get('procedure', '')}",
            f"Rationale : {art43.get('rationale', '')}", "",
        ]
    matrix_ref = t18.get("compliance_matrix_ref") or {}
    lines += [
        "Compliance matrix (T17)", "-" * 70,
        f"URI       : {matrix_ref.get('uri', '')}",
        f"SHA-256   : {matrix_ref.get('sha256', '')}", "",
    ]
    return lines


def artefact_lines(t18: dict[str, Any]) -> list[str]:
    """Render the embedded artefact (T01a–T16) URI listing.

    The manifest holds every artefact produced, so each line carries the
    Verifier's verdict: a URI on its own does not say whether the artefact
    behind it was admitted.
    """
    embedded = t18.get("embedded_artefacts", {}) or {}
    lines = ["Embedded artefacts (T01a–T16)", "-" * 70]
    for tid in sorted(embedded.keys()):
        ref = embedded[tid] or {}
        verdict = ref.get("verifier_verdict")
        mark = "" if verdict is None else f"  [{verdict}]"
        lines.append(f"  {tid:36s} → {ref.get('uri', '')}{mark}")
    lines.append("")
    return lines


def findings_roadmap_lines(t18: dict[str, Any]) -> list[str]:
    """Render blocking findings and the remediation roadmap."""
    lines: list[str] = []
    blocking = t18.get("blocking_findings", []) or []
    if blocking:
        lines += ["Blocking findings", "-" * 70]
        for f in blocking:
            lines.append(f"  [{f.get('severity', 'major'):>10s}] "
                         f"{f.get('article', '')} · {f.get('description', '')}")
        lines.append("")
    roadmap = t18.get("remediation_roadmap", []) or []
    if roadmap:
        lines += ["Remediation roadmap", "-" * 70]
        for item in roadmap:
            lines.append(
                f"  #{item.get('rank', 0):02d} {item.get('control_id', ''):8s} "
                f"[{item.get('gap_severity', '')}] "
                f"owner={item.get('assigned_owner', 'To be assigned')} · "
                f"priority={item.get('priority_label', '')} · "
                f"deadline={item.get('deadline_weeks', '')}w · "
                f"{item.get('action', item.get('recommended_action', ''))}")
        lines.append("")
    return lines
