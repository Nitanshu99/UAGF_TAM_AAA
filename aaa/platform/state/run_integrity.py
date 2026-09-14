"""Whether a run's artefacts are the ones it was supposed to produce — fix F2 (S3).

A stub artefact and a real one are byte-indistinguishable to a consumer. Both are
an ``ArtefactRef`` with a ``uri``, a ``sha256`` and a ``template_id``; the only
difference is that the stub's URI names nothing and its ``sha256`` is the literal
string ``"stub"``. So the 2026-09-03 delivery handed S6 a state whose Phase 1 had
never run, and the reviewer's only available symptom was that
``annex_iii_mapping`` was ``[]`` — which they filed, reasonably, as a missing
field in the S5 contract. Two of the four tickets that review produced were one
pipeline incident wearing a schema costume.

The repair is not to remove the stub. It has a job on the **unwired** path, where
no dispatch was attempted and a deterministic placeholder is an honest answer
(see :mod:`aaa.agents.tier1.phases.verification.no_report`). The repair is to make
the run say, in one place a consumer can read before it reads anything else,
*which artefacts are placeholders and which phases therefore did not deliver*.

Three consumers ask this and must get the same answer — the customer writer
stamping a deliverable, the S6 hand-off deciding whether to warn, and the wizard
deciding whether to let a human download it — which is why it lives here beside
:mod:`aaa.platform.state.admission` rather than in whichever one needed it first.

``suitable_for_handoff`` is deliberately the *narrow* claim: it says the run
produced no placeholders, not that its conclusions are sound. A run can be fully
wired and still reach ``DISCLAIMER_OF_OPINION`` on the evidence — that is an
audit outcome, not an integrity failure, and conflating the two would teach a
reader to ignore this field.
"""
from __future__ import annotations

import subprocess
import uuid
from datetime import datetime, timezone
from typing import Any, Final, Iterable

from aaa.platform.model_registry.decoding import decoding_provenance
from aaa.platform.state.degradation import (
    STUB_SHA,
    degraded_phases,
    fallback_critique_ids,
    is_degraded,
    stub_artefact_ids,
)

#: Key under which the block is stamped into a delivered ``AuditState``.
RUN_INTEGRITY_KEY: Final = "run_integrity"










def code_revision() -> str | None:
    """The git revision this run executed, or ``None`` when it cannot be read.

    Fail-soft by contract: a deliverable written from a tarball, a container
    without git, or a detached checkout still gets written. An absent revision
    is a weaker provenance claim, not a reason to lose the run.

    :returns: Short commit sha, ``"<sha>-dirty"`` on a dirty tree, else ``None``.
    """
    def _git(*args: str) -> str | None:
        try:
            out = subprocess.run(("git", *args), capture_output=True,
                                 text=True, timeout=5, check=False)
        except (OSError, subprocess.SubprocessError):
            return None
        return out.stdout.strip() if out.returncode == 0 else None

    sha = _git("rev-parse", "--short", "HEAD")
    if sha is None:
        return None
    return f"{sha}-dirty" if _git("status", "--porcelain") else sha


def build_run_integrity(state: dict[str, Any], *,
                        unwired_agents: Iterable[str] | None = None) -> dict[str, Any]:
    """Assemble the integrity block for a delivered *state*.

    :param state: Final audit state.
    :param unwired_agents: Agent attribute names that failed to construct, from
        ``initialise_agents``. Names *why* a phase was stubbed, which the
        artefacts alone cannot say. Defaults to what the Orchestrator recorded
        on the state, so neither caller has to thread it through.
    :returns: The ``run_integrity`` block, JSON-serialisable.
    """
    unwired = list(unwired_agents if unwired_agents is not None
                   else (state.get("unwired_agents") or ()))
    stubs = stub_artefact_ids(state)
    unverified = fallback_critique_ids(state)
    # An artefact nothing *wrote*, as against one nothing checked. A phase agent
    # whose LLM call fails assembles its artefacts deterministically and returns
    # a Report like any other, so the phase logs "complete" and the Verifier
    # admits the result (see `verification.phase_outcome._record_fallback_phase`).
    unwritten = [entry["phase_id"] for entry in (state.get("fallback_phases") or [])]
    return {
        "run_id": str(state.get("run_id") or uuid.uuid4().hex),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "code_revision": code_revision(),
        "stub_artefact_ids": stubs,
        "fallback_critique_ids": unverified,
        "fallback_authored_phases": unwritten,
        "degraded_phases": degraded_phases(state),
        "unwired_agents": sorted(unwired),
        "artefact_count": len(state.get("phase_artefacts") or {}),
        # How reproducible this run was asked to be, and whether each roster
        # model actually received it. Under greedy decoding a disagreement
        # between runs is a finding; under sampling it may be only the sample.
        "decoding": decoding_provenance(),
        # Audit-programme procedures that were not performed (audit_programme).
        "scope_limitations": list(state.get("scope_limitations") or []),
        # Three ways to hold a placeholder, and each bars a hand-off: an
        # artefact nothing produced, one nothing independently checked, and one
        # no model wrote. The claim stays narrow — it says the run produced no
        # placeholders, not that its conclusions are sound.
        "suitable_for_handoff": not stubs and not unverified and not unwritten,
    }


__all__ = ["STUB_SHA", "RUN_INTEGRITY_KEY", "stub_artefact_ids", "degraded_phases",
           "fallback_critique_ids", "is_degraded", "code_revision",
           "build_run_integrity"]
