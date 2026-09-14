"""Resolve deferred HITL cases and render the FINAL report.

After an audit completes with deferred HITL cases, the pipeline writes a
*provisional* report plus an editable ``<id>_hitl_review.json`` into
``data/customer/<company>/``.  A human auditor fills in each case's
``human_decision`` (and rationale), then runs this script to

1. apply those decisions to the Verifier verdicts,
2. recompute the compliance matrix + KPIs + final verdict,
3. re-render FINAL ``audit_state`` / ``T17`` / ``T18`` into the same folder,
4. mark the review packet RESOLVED (or PARTIALLY_RESOLVED if cases remain).

It needs no MinIO, LLM, or Qdrant — it is a pure recompute over saved state.

Usage::

    python -m scripts.finalize_hitl eng-01_finclear_gmbh
"""
from __future__ import annotations

from scripts.finalize_hitl.finalize import main

__all__ = ["main"]
