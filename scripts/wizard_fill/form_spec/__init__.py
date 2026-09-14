"""What the wizard asks, read from the wizard's own source.

Every label here is **imported from the module that renders it**, never copied.
That is the whole point: a driver that hardcodes "Risk management file" keeps
working silently after the label becomes "Risk management documentation" — it
just stops filling that slot, and the run that follows is quietly thinner than
the one it is compared against. Importing the same constants the UI renders from
turns a renamed field into an ImportError or a failed assertion at start-up,
before a browser is even launched.

The constants that are genuinely private to a render module (`_TEXT_FIELDS`,
`_MULTISELECTS`) are imported with their underscore. That is deliberate: reaching
into them is what makes this file break when they move, which is the behaviour
worth having.

``steps`` covers steps 0–2, the tabs and the buttons; ``stage_a`` and ``stage_b``
cover the two halves of step 3.
"""
from scripts.wizard_fill.form_spec.stage_a import (
    CONTACTS_EXPANDER,
    FLI_CHECKBOXES,
    FLI_EXCLUSION,
    FLI_MULTISELECTS,
    STEP3_ANNEX_LABEL,
    STEP3_CONTACTS,
    STEP3_SELECTS,
    STEP3_STAGE_A_TEXT,
)
from scripts.wizard_fill.form_spec.stage_b import (
    MODEL_META_SELECTS,
    RANKING_SELECTS,
    STEP3_STAGE_B_RAW,
    STEP3_STAGE_B_TEXT,
    UPLOADERS,
    accepted_types,
    uploader_for,
)
from scripts.wizard_fill.form_spec.steps import (
    BUTTONS,
    STEP0_TEXT,
    STEP1_UPLOADERS,
    STEP2_CHECKBOXES,
    STEP2_MULTISELECTS,
    STEP2_SELECTS,
    TABS,
)

__all__ = [
    "BUTTONS", "CONTACTS_EXPANDER", "FLI_CHECKBOXES", "FLI_EXCLUSION", "FLI_MULTISELECTS", "MODEL_META_SELECTS",
    "RANKING_SELECTS", "STEP0_TEXT", "STEP1_UPLOADERS", "STEP2_CHECKBOXES", "STEP2_MULTISELECTS",
    "STEP2_SELECTS",
    "STEP3_ANNEX_LABEL", "STEP3_CONTACTS", "STEP3_SELECTS", "STEP3_STAGE_A_TEXT", "STEP3_STAGE_B_RAW",
    "STEP3_STAGE_B_TEXT", "TABS", "UPLOADERS", "accepted_types", "uploader_for",
]
