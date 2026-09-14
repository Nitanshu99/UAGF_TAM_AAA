"""Translate the S5 adapter's dialect into the CGSA contract this repo pins.

S5 ships its hand-off as ``schema_version: "s5-aaa-adapter-v1.0"``, and that is
not the ``1.0.0`` contract in ``schemas/cgsa/``. The first real payload
failed validation in hundreds of places, so the GovernanceAgent escalates
before reading a single control and Phase 5 contributes no governance evidence.

The two are the same assessment, described differently. Every field the contract
requires and the dialect omits is derivable from the dialect's own content, and
most of it is *richer* there: every control names its articles and most carry a
written gap explanation, against boilerplate counters in the summary list AAA
was reading.

Which is why the repair belongs here and not in the consumers. Left to the
summary list, no governance finding maps to an article at all, and an
Art. 17 — whose FAIL rests on governance controls and nothing else — re-derives
to **PASS**. A clean bill from evidence that was present and unread.

This module changes no verdict and adds no content: it moves what S5 sent into
the fields the contract names, and leaves anything underivable absent so schema
validation still reports it.
"""
from __future__ import annotations

import copy
import logging
from typing import Any

from aaa.tools.cgsa_ingest.s5.adapt import (
    adapt_constraints,
    adapt_controls,
    adapt_handoff,
    adapt_matrix,
)
from aaa.tools.cgsa_ingest.s5.fields import actions_by_control, controls_by_id, coverage_pct

logger = logging.getLogger(__name__)

#: ``schema_version`` prefix identifying the dialect. Gating on the version S5
#: declares keeps the translation off every payload that already states the
#: contract, so a conforming producer is never reshaped on a guess.
S5_DIALECT_PREFIX = "s5-aaa-adapter"


def is_s5_dialect(payload: Any) -> bool:
    """Whether *payload* declares itself as the S5 adapter dialect."""
    return (isinstance(payload, dict)
            and str(payload.get("schema_version", "")).startswith(S5_DIALECT_PREFIX))


def adapt_s5_dialect(payload: dict[str, Any]) -> dict[str, Any]:
    """Return *payload* restated in the pinned CGSA contract's shape.

    The input is not mutated. Fields the payload already carries are kept as
    they are — the translation only fills what the contract requires and the
    dialect leaves out.

    :param payload: A payload for which :func:`is_s5_dialect` is true.
    :returns: A new payload in the ``1.0.0`` shape.
    """
    adapted = copy.deepcopy(payload)
    domains = adapted.get("domains") or []
    controls = controls_by_id(domains)
    actions = actions_by_control(adapted.get("remediation_roadmap") or [])

    adapt_controls(domains)
    adapt_handoff(adapted.setdefault("aaa_phase5_handoff", {}), controls, actions)
    adapt_constraints(adapted.setdefault("hard_constraint_results", {}), controls)
    adapt_matrix(adapted.setdefault("eu_ai_act_compliance_matrix", {}))

    scores = adapted.setdefault("overall_scores", {})
    if scores.get("eu_ai_act_coverage_pct") is None:
        pct = coverage_pct(adapted["eu_ai_act_compliance_matrix"])
        if pct is not None:
            scores["eu_ai_act_coverage_pct"] = pct

    logger.info(
        "CGSA: translated %s from the S5 dialect — %d control(s), %d blocking "
        "finding(s) given their article, Art. 9/10/13 coverage %.1f%%.",
        payload.get("schema_version"), len(controls),
        sum(1 for f in adapted["aaa_phase5_handoff"].get("blocking_findings") or []
            if f.get("eu_ai_act_article")),
        scores.get("eu_ai_act_coverage_pct") or 0.0)
    return adapted


__all__ = ["S5_DIALECT_PREFIX", "is_s5_dialect", "adapt_s5_dialect"]
