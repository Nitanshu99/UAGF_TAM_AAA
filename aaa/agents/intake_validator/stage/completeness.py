"""The T01c intake-completeness content, assembled from the calculator's report."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def completeness_content(report: Any, art43_preview_procedure: str) -> dict[str, Any]:
    """Build the T01c payload stored beside the dossier.

    The Art. 43 fields are placeholders here: the preview comes from Stage A and
    the final procedure and delta are filled in by Phase 1.

    :param report: The ``CompletenessReport`` from the calculator.
    :type report: Any
    :param art43_preview_procedure: Stage A's Art. 43 preview.
    :type art43_preview_procedure: str
    :returns: The T01c content dictionary.
    :rtype: dict[str, Any]
    """
    return {
        **report.to_dict(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "art43_preview_procedure": art43_preview_procedure,
        "art43_final_procedure": None,
        "art43_delta": None,
    }
