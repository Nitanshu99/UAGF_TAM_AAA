"""The Cyber sub-agent's injection suite and the finding it raises."""
from __future__ import annotations

from typing import Any

from aaa.tools.prompt_injection_suite import prompt_injection_suite
from aaa.tools.prompt_injection_suite.judge import judge_injection


def _injection(decl: dict[str, Any], modality: str, engagement_id: str,
               blocking_findings: list[dict]) -> dict | None:
    """Specialist probe 2: the injection suite, for generative modalities only."""
    if modality not in {"llm", "agentic", "gpai"}:
        return None
    injection = prompt_injection_suite(
        target_uri=decl.get("stage_c", {}).get("read_only_api_endpoint"),
        system_prompt=decl.get("system_prompt_text"))
    finding = injection_finding(injection, decl, engagement_id)
    blocking_findings += [finding] if finding else []
    return injection


def injection_finding(injection: dict[str, Any], decl: dict[str, Any],
                      engagement_id: str) -> dict[str, Any] | None:
    """A finding for an overstated declaration (critical) or demonstrated attacks (major).

    Was a critical finding above a fixed 5 % vulnerability rate (T-20260914-008).
    """
    outcome, sentence = judge_injection(
        injection, (decl.get("stage_b") or {}).get("robustness_metrics"))
    if outcome not in ("overstated", "demonstrated"):
        return None
    return {"finding_id": f"CYBER-{engagement_id[:4]}-01", "phase": "CyberSecurity",
            "article": "Art.15", "description": sentence,
            "severity": "critical" if outcome == "overstated" else "major",
            "evidence_uri": ""}  # set after store


__all__ = ["_injection", "injection_finding"]
