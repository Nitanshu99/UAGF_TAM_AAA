"""Step 3, *Your system*: identity, classification and the advanced FLI fields."""
from __future__ import annotations

from aaa.ui.wizard.step3.stage_a.contacts import CONTACT_LABELS
from aaa.ui.wizard.step3.stage_a.fli.spec import _EXCLUSION_OPTIONS, _MULTISELECTS

#: Step 3 Stage A — plain text/area label → Stage A field.
STEP3_STAGE_A_TEXT = {
    "Legal provider name": "provider_name",
    "System name": "system_name",
    "Version": "version",
    "Intended purpose": "intended_purpose",
}

#: Step 3 Stage A — selectbox label → Stage A field.
STEP3_SELECTS = {
    "AI modality": "declared_modality",
    "Self-assessed risk tier": "declared_risk_tier",
    "Deployment context": "deployment_context",
}

#: Step 3 Stage A — the Annex III multiselect, which stores *labels* and derives
#: the section numbers (see ``classification.render_classification``).
STEP3_ANNEX_LABEL = "Annex III high-risk categories"

#: Step 3 advanced — FLI multiselect label → Stage A field, derived from the
#: session keys the spec declares (``s3_a_<field>``).
FLI_MULTISELECTS = {label: key.removeprefix("s3_a_")
                    for label, (key, _) in _MULTISELECTS.items()}

#: Step 3 advanced — the one FLI selectbox, and the options it offers.
FLI_EXCLUSION = ("FLI-R2 · Art. 2 exclusion category (if any)", "art2_exclusion",
                 [o for o in _EXCLUSION_OPTIONS if o])

#: Step 3 advanced — checkbox label → Stage A field.
FLI_CHECKBOXES = {
    "FLI-HR3 · Third-party conformity assessment legally required":
        "third_party_ca_legally_required",
    "FLI-HR5 · Art. 6 §3 derogation claimed (no significant risk of harm)":
        "art6_derogation_claimed",
    "FLI-R1 · GPAI meets Art. 51 §2 systemic-risk threshold (>10^25 FLOPs)":
        "gpai_systemic_risk",
    "FLI-R5 · Public-law body or private entity providing public services":
        "is_public_body_or_public_service",
}

#: Step 3 — the optional remediation-owner expander, and label → contact role.
CONTACTS_EXPANDER = "Remediation owners (optional)"
STEP3_CONTACTS = dict(CONTACT_LABELS)

__all__ = ["CONTACTS_EXPANDER", "FLI_CHECKBOXES", "STEP3_CONTACTS", "FLI_EXCLUSION", "FLI_MULTISELECTS", "STEP3_ANNEX_LABEL",
           "STEP3_SELECTS", "STEP3_STAGE_A_TEXT"]
