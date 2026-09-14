"""Evaluation-set loading for the Tier-3 privacy deep-dive (finding P5).

The agent's own comment says *"re-scan the evaluation set for leaks"*, and it
called ``pii_scan(df=decl.get("X_eval"))``.  No dispatch has ever carried an
``X_eval`` key, so the scan received ``None`` on every run: Presidio raised,
the keyword heuristic read an empty column list, and the deep-dive reported no
PII and no special categories — a clean result from a scan of nothing.

The dataset is resolved the way Phase 2 and Phase 3 resolve theirs, from the
Stage B dossier the runner now passes.  The evaluation set is preferred over
the training set because that is the population this agent is auditing; a
missing dataset returns ``None`` and a reason, never an empty frame, so
:mod:`aaa.agents.tier3.privacy_agent.t08_update` can say the scan did not run
instead of recording its emptiness as a finding of no PII.
"""
from __future__ import annotations

from typing import Any

from aaa.platform.artifact_loader import ArtifactUnavailable, load_artifact_from_uri

#: Stage B keys naming the frame to scan, most specific first.
_DATASET_KEYS = ("evaluation_dataset_uri", "training_dataset_uri")


def load_scan_frame(store: Any, decl: dict[str, Any]) -> tuple[Any, str]:
    """Return the frame the PII deep-dive scans, and why there is none.

    :param store: Evidence store used to resolve the dataset URI.
    :param decl: Declaration summary from the dispatch (carries ``stage_b``).
    :returns: ``(dataframe_or_None, reason)`` — *reason* is empty on success.
    """
    stage_b: dict[str, Any] = decl.get("stage_b") or {}
    uri = next((stage_b.get(key) for key in _DATASET_KEYS if stage_b.get(key)), None)
    if not uri:
        return None, "no evaluation or training dataset URI was supplied"
    try:
        kind = "parquet" if str(uri).lower().endswith(".parquet") else "csv"
        return load_artifact_from_uri(uri, store, kind), ""
    except ArtifactUnavailable as exc:
        return None, f"the dataset at {uri} could not be loaded ({exc.reason})"


__all__ = ["load_scan_frame"]
