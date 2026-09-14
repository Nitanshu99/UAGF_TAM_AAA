"""The CyberSecurity spawn's declaration-verification delta."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier3.cyber_agent.template import T11
from aaa.platform.audit_programme import outcome
from aaa.platform.state.artefact_keys import SPAWN_CYBER, namespaced_key


def cyber_delta(t11_uri: str, base_uri: str, blocking_findings: list[dict[str, Any]],
                probe_skipped: str | None, skipped_reason: str | None) -> dict[str, Any]:
    """The spawn's T11 slot, findings, probe outcome and escalation.

    :param t11_uri: URI of the spawn's T11.
    :param base_uri: URI of the Phase 3 T11 it extends ("" when none).
    :param blocking_findings: Findings the specialist probes raised.
    :param probe_skipped: Why the specialist probe did not run, or ``None`` when it ran.
    :param skipped_reason: The T11's own skip reason, used when the probe gave none.
    """
    return {
        # P5: the spawn's copy is a second T11, not Phase 3's. It lands in
        # its own slot; the runner enforces that regardless of this key.
        "phase_artefacts": {namespaced_key(T11, SPAWN_CYBER): {
            "uri": t11_uri, "sha256": "", "template_id": T11, "extends": base_uri}},
        "blocking_findings": blocking_findings,
        "procedure_outcomes": outcome("specialist_adversarial_probe", not probe_skipped,
                                      probe_skipped or skipped_reason),
        "hitl_required": len(blocking_findings) > 0,
        "hitl_reason": ("CyberSecurity Sub-Agent detected critical vulnerabilities."
                        if blocking_findings else None),
    }


__all__ = ["cyber_delta"]
