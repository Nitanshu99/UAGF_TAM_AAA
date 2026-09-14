"""Stage A remediation owners for wizard step 3 (optional).

The T01a contract has carried ``organisation_contacts`` since the schema was
written, and Phase 5 assigns every roadmap item to one of its roles — but no
screen asked for it, so every owner in every report was unassigned
(T-20260913-042). Names or roles are both acceptable; blanks stay unassigned and
the roadmap then names the role that should take the item.
"""
from __future__ import annotations

import streamlit as st

#: Widget label → ``organisation_contacts`` role. Literal labels, so the form
#: driver's label check can find them in this file.
CONTACT_LABELS = {
    "Technical lead": "technical_lead",
    "Data governance lead": "data_lead",
    "Compliance / legal lead": "compliance_lead",
    "Data protection officer": "dpo",
    "Executive accountable for AI governance": "executive_sponsor",
}


def render_contacts() -> None:
    """Render the optional remediation-owner inputs."""
    with st.expander("Remediation owners (optional)", expanded=False):
        st.caption("Who should own the actions this audit recommends. A name or a role; "
                   "leave blank if not yet decided.")
        for label, role in CONTACT_LABELS.items():
            st.text_input(label, key=f"s3_a_contact_{role}", placeholder="e.g. Jane Doe, CTO")


__all__ = ["CONTACT_LABELS", "render_contacts"]
