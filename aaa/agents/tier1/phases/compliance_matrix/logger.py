"""Part 1 of the former ``compliance_matrix`` module (auto-split)."""
from __future__ import annotations

import logging

from aaa.platform.state.admission import ADMITTED_VERDICTS
from aaa.tools.regulatory_coverage.artefact_contract import ARTEFACT_ARTICLES
from aaa.tools.regulatory_coverage.engagement_scope import core_article

logger = logging.getLogger(__name__)


#: Fix 50: this map and ``node_stubs.TEMPLATE_ARTICLES`` were two copies of one
#: fact and disagreed in seven places — see
#: :mod:`aaa.tools.regulatory_coverage.artefact_contract` for what each cost.
#: The name stays because a dozen modules in this package use it.
_TEMPLATE_ARTICLES = ARTEFACT_ARTICLES


#: Kept as a module-local name for the auto-split re-exports; the rule
#: itself lives in :mod:`aaa.platform.state.admission`.
_ADMITTED_VERDICTS = ADMITTED_VERDICTS


_CORE_HIGH_RISK_ARTICLES = {
    "Art.9", "Art.10", "Art.11", "Art.12", "Art.13", "Art.14", "Art.15", "Art.17",
}


#: Fix 40 moved this to :mod:`aaa.tools.regulatory_coverage.engagement_scope`,
#: where the scope test that needs it lives; aliased here because a dozen modules
#: in this package name it.
_core_article = core_article
