"""Loading the Phase 2 dataset and resolving its target column."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier2.data_auditor.dataset import load_dataset
from aaa.agents.tier2.data_auditor.frames import empty_frame
from aaa.tools.data_dictionary import resolve_data_dictionary


def resolve_dataframe(agent: Any, t01b: dict, decl: dict, stage_b: dict,
                      target_col: str | None, findings: list,
                      ) -> tuple[Any, bool, str | None]:
    """Load the dataset and resolve the target column for the tool runs.

    :returns: ``(df_for_tools, data_available, target_col)`` — the frame is
        an empty stub when the real dataset is unavailable.
    """
    df, dataset_finding = load_dataset(agent.store, t01b, decl)
    if dataset_finding:
        findings.append(dataset_finding)
    data_available = df is not None and len(df) > 0
    if df is not None and data_available and not target_col:
        # Resolve target silently; Phase 3 owns the data-dictionary findings.
        target_col = resolve_data_dictionary(stage_b or t01b, list(df.columns)).target_column
    return (df if df is not None else empty_frame()), data_available, target_col


__all__ = ["resolve_dataframe"]
