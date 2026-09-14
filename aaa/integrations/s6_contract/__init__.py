"""The S6 field projection — every value its contract names, in its vocabulary.

``build_handoff`` has always shipped the whole audit state and let S6 dig the
fields out. That works while both sides agree on where a field lives and what
its values mean, and the 2026-09-05 sweep found they do not: five values outside
S6's accepted sets, two derivations S6 cannot compute from the sources its sheet
names, and one field (``domain_scores``) keyed differently on each side.

This package is the projection that removes the digging. The audit state stays
the source of truth and travels unchanged; ``s6_fields`` is a flat, derived,
vocabulary-checked view of exactly the rows in
``s5_s4_json_fields_consumed_by_s6.xlsx``. Anything that cannot be expressed in
S6's vocabulary is reported as a warning rather than coerced — see
:mod:`.vocabulary` for why translating a disagreement is worse than naming it.
"""
from __future__ import annotations

from typing import Final

from aaa.integrations.s6_contract import vocabulary as vocab  # noqa: F401
from aaa.integrations.s6_contract.columns import (  # noqa: F401
    _domain_scores,
    _sensitive_feature_columns,
)
from aaa.integrations.s6_contract.fields import (  # noqa: F401
    _CHECKED,
    _STAGE_B_PASSTHROUGH,
    build_s6_fields,
)
from aaa.integrations.s6_contract.translate import (  # noqa: F401
    annex_iii_sections,
    application_domain,
    split_modality,
)

#: Keys the projection is stamped under on a delivered ``AuditState`` (fix F16,
#: finding S24). ``build_s6_fields`` had been computed correctly since F8-F15
#: but never reached a persisted deliverable — only ``build_handoff``'s
#: transient return value, consumed solely by the mid-pipeline external XAI /
#: security evaluate-API call. A human reviewing the actual
#: ``<engagement_id>_audit_state.json`` file never saw it.
S6_FIELDS_KEY: Final = "s6_fields"
S6_CONTRACT_WARNINGS_KEY: Final = "s6_contract_warnings"









__all__ = ["build_s6_fields", "vocab", "S6_FIELDS_KEY", "S6_CONTRACT_WARNINGS_KEY"]
