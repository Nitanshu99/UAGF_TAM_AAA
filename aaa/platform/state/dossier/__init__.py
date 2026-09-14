"""Stage B / Stage C intake types and the root submission bundle.

Split into submodules when Stage B gained its provenance fields; the public
import path (``aaa.platform.state.dossier``) is unchanged.
"""
from __future__ import annotations

from aaa.platform.state.dossier.annex_iv import AnnexIVDossier
from aaa.platform.state.dossier.submission import ClientSubmission, StageCAccess

__all__ = ["AnnexIVDossier", "ClientSubmission", "StageCAccess"]
