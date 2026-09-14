"""Part 7 of the former ``verification`` module (auto-split)."""
from __future__ import annotations

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
from aaa.agents.tier1.phases.verification.run_phase_with_verification import (  # noqa: F401
    run_phase_with_verification,
)
from aaa.agents.tier1.phases.verification.verify_artefacts import _verify_artefacts  # noqa: F401

__all__ = ["run_phase_with_verification"]
