"""Part 3 of the former ``verification`` module (auto-split)."""
from __future__ import annotations

import time

from aaa.agents.tier1.phases.verification.logger import (  # noqa: F401
    _REPORT_TIDS,
    _VERDICT_ORDER,
    _VERIFIER,
    _artefact_content,
    _artefact_uri,
    _get_verifier,
    _worse,
    logger,
)
from aaa.agents.tier1.phases.verification.merge_critique import _merge_critique  # noqa: F401


def _finish_phase(state: dict, worst: str, rerun_count: int,
                  phase_label: str, t_phase: float) -> None:
    """Flag HITL on an unresolved verdict, record metrics, log completion."""
    from aaa.observability.metrics import PHASE_COUNTER, PHASE_LATENCY_HISTOGRAM

    elapsed = time.monotonic() - t_phase
    PHASE_COUNTER.labels(phase=phase_label, verdict=worst).inc()
    PHASE_LATENCY_HISTOGRAM.labels(phase=phase_label).observe(elapsed)
    if worst == "unverified":
        # An artefact nobody checked is a reviewer's problem, not a pass. It is
        # named separately because the reason is the Verifier's availability,
        # not anything the phase did (P6).
        state["hitl_required"] = True
        state["hitl_reason"] = (
            f"{phase_label}: artefact(s) closed 'unverified' — the Verifier's "
            f"critique did not run and only structural checks were applied."
        )
    elif worst in {"rerun", "escalate_hitl"}:
        state["hitl_required"] = True
        state["hitl_reason"] = (
            f"{phase_label}: Verifier verdict '{worst}' on artefact(s) "
            f"after {rerun_count} rerun(s)."
        )
    logger.info(
        "%s: complete in %.1fs (worst verdict '%s', %d rerun(s)).",
        phase_label, elapsed, worst, rerun_count,
    )
