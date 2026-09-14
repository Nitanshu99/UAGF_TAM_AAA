"""aaa.agents.tier1.phases.compliance_matrix — Compliance matrix assembly node.

Single exported function: ``node_compliance_matrix(state)``.

Derives each EU AI Act article verdict from *actual evidence* — phase findings,
the independent-verifier critiques, and per-article insufficient-evidence signals —
instead of the previous behaviour of stamping every admitted article ``PASS``.

Verdict precedence per article:
  1. a confirmed material non-conformity finding   → FAIL
  2. required independent analysis not performed    → INSUFFICIENT_EVIDENCE
  3. a qualifying (possibly-material/observation)   → PASS_WITH_OBSERVATIONS
  4. admitted, verifier-accepted, no findings       → PASS
  5. referenced but no admitted evidence            → INSUFFICIENT_EVIDENCE

It also builds ``state['article_evidence']`` (rationale + evidence URIs + supporting
template ids + CGSA control ids + finding ids per article) so the T17 compliance
matrix is traceable, and computes the final verdict + opinion-disclaimer flag."""
from aaa.agents.tier1.phases.compliance_matrix.collect_admitted_articles import (  # noqa: F401
    _collect_admitted_articles,
)
from aaa.agents.tier1.phases.compliance_matrix.compute_final_verdict import (  # noqa: F401
    _compute_final_verdict,
)
from aaa.agents.tier1.phases.compliance_matrix.derive_verdicts import _derive_verdicts  # noqa: F401
from aaa.agents.tier1.phases.compliance_matrix.evidence_entry import _evidence_entry  # noqa: F401
from aaa.agents.tier1.phases.compliance_matrix.finalise_verdict import (  # noqa: F401
    _finalise_verdict,
)
from aaa.agents.tier1.phases.compliance_matrix.findings_by_article import (  # noqa: F401
    _cgsa_controls_for,
    _findings_by_article,
)
from aaa.agents.tier1.phases.compliance_matrix.logger import (  # noqa: F401
    _ADMITTED_VERDICTS,
    _CORE_HIGH_RISK_ARTICLES,
    _TEMPLATE_ARTICLES,
    _core_article,
    logger,
)
from aaa.agents.tier1.phases.compliance_matrix.node_compliance_matrix import (  # noqa: F401
    node_compliance_matrix,
)
from aaa.agents.tier1.phases.compliance_matrix.rationale import (  # noqa: F401
    _exclusion_note,
    _rationale,
    _scope_note,
)
from aaa.agents.tier1.phases.compliance_matrix.scope_articles import (  # noqa: F401
    GATE_ARTICLES,
    SCOPE_FINDING_ID,
    record_scoped_unevidenced,
    scope_gate_articles,
)
from aaa.agents.tier1.phases.compliance_matrix.supporting_tids import (  # noqa: F401
    _article_verdict,
    _excluded_tids,
    _supporting_tids,
)
from aaa.platform.state.admission import admitted_artefacts  # noqa: F401

__all__ = [
    'logger', '_TEMPLATE_ARTICLES', '_ADMITTED_VERDICTS', '_CORE_HIGH_RISK_ARTICLES', '_core_article',
    '_collect_admitted_articles', '_findings_by_article', '_cgsa_controls_for', '_supporting_tids',
    'admitted_artefacts', '_excluded_tids', '_exclusion_note', '_scope_note',
    'GATE_ARTICLES', 'SCOPE_FINDING_ID', 'scope_gate_articles', 'record_scoped_unevidenced',
    '_article_verdict', '_rationale', '_evidence_entry', '_derive_verdicts', '_compute_final_verdict',
    '_finalise_verdict', 'node_compliance_matrix', '__all__',
]
