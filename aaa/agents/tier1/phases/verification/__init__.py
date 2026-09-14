"""aaa.agents.tier1.phases.verification — Real Verifier wiring for phase runners.

Previously every phase hardcoded ``verifier_critiques[tid] = {"verdict": "accept"}``,
so the independent-critique gate (``aaa.agents.tier1.verifier.Verifier``) was built
but never invoked. This module actually runs the Verifier against each produced
artefact, records the *real* critique, and honours its verdict:

  - ``rerun``         → re-dispatch the phase agent (bounded by ``MAX_RERUNS``).
  - ``escalate_hitl`` → flag the engagement for human review.
  - ``accept`` / ``accept_with_notes`` → admit.
  - ``unverified`` → the critique did not run (P6).

Every verdict but the two admitting ones takes the artefact's articles with it:
``gate_on_unadmitted`` records them INSUFFICIENT_EVIDENCE rather than letting
them fall out of the compliance matrix unnamed (Q1).

The Verifier applies the four-dimension LLM rubric, falling back to
deterministic checks (non-empty artefact, evidence linkage) when the LLM
call fails."""
from aaa.agents.tier1.phases.verification.confidence import (  # noqa: F401
    CONFIDENCE_FLOOR,
    gate_on_confidence,
    read_confidence,
)
from aaa.agents.tier1.phases.verification.critique_artefact import _critique_artefact  # noqa: F401
from aaa.agents.tier1.phases.verification.finish_phase import _finish_phase  # noqa: F401
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
from aaa.agents.tier1.phases.verification.phase_outcome import record_phase_outcome  # noqa: F401
from aaa.agents.tier1.phases.verification.rerun_context import build_rerun_context
from aaa.agents.tier1.phases.verification.run_phase_with_verification import (  # noqa: F401
    run_phase_with_verification,
)
from aaa.agents.tier1.phases.verification.unadmitted import gate_on_unadmitted  # noqa: F401
from aaa.agents.tier1.phases.verification.verify_artefacts import _verify_artefacts  # noqa: F401

__all__ = [
    'logger', '_VERDICT_ORDER', '_REPORT_TIDS', '_VERIFIER', '_get_verifier', '_worse',
    '_artefact_uri', '_artefact_content', '_merge_critique', 'record_phase_outcome',
    'build_rerun_context', 'CONFIDENCE_FLOOR', 'read_confidence', 'gate_on_confidence',
    'gate_on_unadmitted',
    '_finish_phase', '_critique_artefact',
    '_verify_artefacts', 'run_phase_with_verification', '__all__',
]
