"""The finalize-HITL recompute pipeline."""
from __future__ import annotations

import json
import sys

from scripts.finalize_hitl.files import REPO_ROOT, find_customer_dir, write_json
from scripts.finalize_hitl.render import print_summary, render_final_reports


def main(engagement_id: str) -> int:
    """Apply human decisions, recompute, and write the FINAL deliverables.

    :param engagement_id: Engagement whose review packet should be resolved.
    :returns: Process exit code (2 when required files are missing).
    """
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    cdir, state_path = find_customer_dir(engagement_id)
    if state_path is None or cdir is None:
        print(f"error: no audit_state for {engagement_id} under data/customer/",
              file=sys.stderr)
        return 2
    review_path = cdir / f"{engagement_id}_hitl_review.json"
    if not review_path.exists():
        print(f"error: no {engagement_id}_hitl_review.json (nothing to finalize)",
              file=sys.stderr)
        return 2

    state = json.loads(state_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))

    from aaa.agents.tier1.phases.compliance_matrix import node_compliance_matrix
    from aaa.tools.hitl_review import apply_human_decisions

    # 1. Fold human decisions into the Verifier verdicts + HITL gate.
    summary = apply_human_decisions(state, review)
    # 2. Recompute the compliance matrix, KPIs, final verdict, opinion flag.
    node_compliance_matrix(state)
    # 3. Re-render T17/T18 from the resolved state.
    t17, t18, now = render_final_reports(state, engagement_id)
    # 4. Persist FINAL deliverables + update the review packet status.
    eid = state.get("engagement_id", engagement_id)
    write_json(state_path, state)
    write_json(cdir / f"{eid}_T17.json", t17)
    write_json(cdir / f"{eid}_T18.json", t18)
    review["status"] = "RESOLVED" if not summary["still_hitl"] else "PARTIALLY_RESOLVED"
    review["resolved_at"] = now
    review["resolution_summary"] = summary
    write_json(review_path, review)

    print_summary(eid, state, t17, summary, cdir)
    return 0
