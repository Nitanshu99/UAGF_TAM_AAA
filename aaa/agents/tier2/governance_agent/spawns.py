"""Tier-3 sub-agent spawn decisions for Phase 5 (§3.3)."""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest import IngestResult


def decide_tier3_spawns(decl: dict[str, Any], result: IngestResult) -> dict[str, Any]:
    """Decide Cyber / Privacy sub-agent spawns per §3.3.

    Cyber: ``risk_tier=high`` OR Art. 15 evidence missing/FAIL.
    Privacy: ``gdpr_overlap`` OR ``special_category_data`` OR Annex III §1.

    :param decl: Declaration summary from the dispatch.
    :param result: CGSA ingest result (unused today, kept for parity).
    :returns: ``{cyber_spawn, cyber_rationale, privacy_spawn, privacy_rationale}``.
    """
    del result  # reserved for future spawn heuristics
    risk_tier = (decl.get("risk_tier") or "").lower()
    art15_verdict = (decl.get("phase3_robustness_verdict") or "").upper()
    cyber_spawn, cyber_rationale = False, None
    if risk_tier == "high":
        cyber_spawn = True
        cyber_rationale = "risk_tier=high → Cyber Sub-Agent per §3.3."
    elif art15_verdict in {"FAIL", "NOT_TESTED"}:
        cyber_spawn = True
        cyber_rationale = (
            f"Phase 3 robustness verdict={art15_verdict} — Art. 15 evidence missing/failed."
        )

    annex_iii_sections = decl.get("annex_iii_sections") or []
    section_ids = {str(s) for s in annex_iii_sections} if isinstance(annex_iii_sections, list) else set()

    privacy_spawn, privacy_rationale = False, None
    if decl.get("gdpr_overlap"):
        privacy_spawn = True
        privacy_rationale = "gdpr_overlap=true → Privacy/DPO Sub-Agent per §3.3."
    elif decl.get("special_category_data"):
        privacy_spawn = True
        privacy_rationale = "special_category_data=true → Privacy/DPO Sub-Agent per §3.3."
    elif "1" in section_ids:
        privacy_spawn = True
        privacy_rationale = "Annex III §1 biometric use case → Privacy/DPO Sub-Agent per §3.3."

    return {
        "cyber_spawn": cyber_spawn,
        "cyber_rationale": cyber_rationale,
        "privacy_spawn": privacy_spawn,
        "privacy_rationale": privacy_rationale,
    }
