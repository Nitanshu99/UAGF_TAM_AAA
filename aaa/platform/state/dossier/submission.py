"""Stage C access grant and the root client-submission bundle."""
from __future__ import annotations

from typing import TypedDict

from aaa.platform.state.dossier.annex_iv import AnnexIVDossier
from aaa.platform.state.intake import StageATriage


class StageCAccess(TypedDict):
    """Scoped live-system access credentials granted in Stage C."""
    read_only_api_endpoint: str | None
    credential_ref: str
    access_scope: list[str]
    access_expiry_utc: str
    revocation_webhook: str | None


class ClientSubmission(TypedDict):
    """Root intake bundle — union of Stage A + B + C artefacts."""
    stage_a: StageATriage
    stage_b: AnnexIVDossier
    stage_c: StageCAccess | None
    intake_completeness_score: float
