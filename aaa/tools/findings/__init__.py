"""aaa.tools.findings — Canonical finding constructors shared across phase agents.

A "real auditor" grounds every verdict in a traceable finding. Phase agents emit
findings via their ``declaration_verification_delta`` under the accumulator keys
``blocking_findings`` / ``positive_findings`` (see ``agent_runner._apply_delta``),
and the compliance-matrix node (WS5) reads ``materiality`` + ``eu_ai_act_articles``
to derive per-article verdicts.

The dict shape here is the union of what every downstream consumer already reads:
``report_architect._auditor_opinion`` / ``_management_response_shell`` /
``_build_t17`` and ``compliance_matrix.node_compliance_matrix``.

Materiality ladder (drives article verdicts in WS5):
  - ``material``           → contributes a FAIL to its articles.
  - ``possibly_material``  → contributes a PASS_WITH_OBSERVATIONS.
  - ``observation``        → informational; PASS_WITH_OBSERVATIONS note only.
  - ``not_material``       → the Verifier judged an issue immaterial; no qualification.

The vocabulary itself is defined once, in :mod:`aaa.platform.state.findings`."""
from aaa.tools.findings.backfill_finding_evidence import (  # noqa: F401
    articles_for,
    backfill_finding_evidence,
    is_blocking,
    normalise_article,
)
from aaa.tools.findings.make_positive_finding import (  # noqa: F401
    collect_evidence_uris,
    make_positive_finding,
)
from aaa.tools.findings.materiality import (  # noqa: F401
    BLOCKING_MATERIALITY,
    Materiality,
    make_finding,
)

__all__ = [
    'Materiality',
    'BLOCKING_MATERIALITY',
    'make_finding',
    'make_positive_finding',
    'collect_evidence_uris',
    'backfill_finding_evidence',
    'is_blocking',
    'articles_for',
    'normalise_article',
]
