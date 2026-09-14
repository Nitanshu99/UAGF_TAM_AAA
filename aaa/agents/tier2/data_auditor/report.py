"""Final Report assembly for Phase 2."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import Report
from aaa.agents.tier2.data_auditor.delta import build_delta
from aaa.tools.findings.measured import measured


def assemble_report(ctx: dict[str, Any], uris: dict[str, str],
                    llm_summary: str | None, prompt_note: str) -> Report:
    """Build the Phase 2 ``Report`` from the processing context."""
    findings = ctx["findings"]
    material = any(f.get("materiality") == "material" for f in findings)
    escalated = ctx["special_cat_delta"] or material or ctx["insufficient"]
    return Report(
        phase_id="P2",
        artefact_uri=uris["T06_datasheet_for_datasets"],
        summary=(
            llm_summary
            or f"Phase 2 complete. quality_verdict={ctx['verdict']}, "
               f"pii_detected={measured(ctx['pii_result']['pii_detected'])}, "
               f"special_category_data={ctx['effective_special_cat']}, "
               f"imbalance={measured(ctx['balance_result']['imbalance_detected'])}."
        ),
        confidence=0.85 if not escalated else 0.6,
        tool_calls=[
            {"tool": "data_profile",
             "result": f"rows={measured(ctx['profile_result']['num_rows'])}, "
                       f"cols={measured(ctx['profile_result']['num_columns'])}"},
            {"tool": "missingness_scan",
             "result": f"overall={measured(ctx['miss_result']['overall_missingness_pct'], '.1f', '%')}"},
            {"tool": "class_balance",
             "result": f"imbalance={measured(ctx['balance_result']['imbalance_detected'])}"},
            {"tool": "pii_scan",
             "result": f"entities={len(ctx['pii_result']['entities_found'])}"},
            {"tool": "drift_test",
             "result": (f"computed={ctx['drift_result']['computed']}, "
                        f"verdict={ctx['drift_result']['verdict']}, "
                        f"drifted={len(ctx['drift_result']['drifted_features'])}")},
            {"tool": "client_doc_search", "result": f"hits={len(ctx['client_doc_hits'])}"},
            {"tool": "prompt_runtime", "result": prompt_note},
        ],
        declaration_verification_delta=build_delta(ctx, uris),
    )
