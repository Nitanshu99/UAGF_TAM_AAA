"""The fairness pre-check shown beside the data dictionary, and what it needs to run."""
from __future__ import annotations

import streamlit as st

from aaa.tools.fairness_groups import resolve_groups


def _fairness_precheck(selected: list[str]) -> None:
    """Show, at selection time, how each protected attribute will be grouped.

    Runs the pipeline's own :func:`~aaa.tools.fairness_groups.resolve_groups`
    over the uploaded dataset, so what the wizard says here is what Phase 4 will
    do — not a second opinion that could drift from it.

    Both facts this surfaces were knowable the moment the CSV was uploaded and
    previously cost a full run to discover: whether a column is binned, and how
    small its smallest cohort is. Small cohorts are tested, not refused; the
    smallest one bounds how precisely a disparity can be placed, so a reviewer who
    sees ``smallest n=10`` before the run can supply a larger evaluation set.

    :param selected: Sensitive feature columns the user has chosen.
    """
    values = st.session_state.get("s3_dataset_values") or {}
    rows = [name for name in selected if values.get(name)]
    if not rows:
        return
    st.caption("How each attribute will be grouped for fairness testing:")
    for name in rows:
        resolution = resolve_groups(name, values[name])
        if not resolution.tested:
            st.warning(f"**{name}** — will not be tested. {resolution.reason}")
        elif resolution.binned:
            st.info(f"**{name}** — continuous, so it is binned into "
                    f"{resolution.group_count} bands (smallest n="
                    f"{resolution.smallest_group_size}). Tested.")
        else:
            st.success(f"**{name}** — {resolution.group_count} groups, smallest n="
                       f"{resolution.smallest_group_size}. Tested; the smaller the "
                       "cohorts, the wider the interval a disparity is judged by.")
def _actionability_inputs(columns: list[str]) -> None:
    """Render the immutable / actionable multiselects and check for overlap.

    :param columns: Feature columns from the uploaded dataset header.
    """
    st.multiselect(
        "Immutable feature columns", options=columns, key="s3_b_dd_immutable_ms",
        help="Features a counterfactual must hold fixed because the subject "
             "cannot change them, e.g. age, credit_history.")
    st.multiselect(
        "Actionable feature columns", options=columns, key="s3_b_dd_actionable_ms",
        help="Features a counterfactual is explicitly allowed to vary. Leave "
             "empty to allow anything not marked immutable.")
    clash = (set(st.session_state.get("s3_b_dd_immutable_ms") or [])
             & set(st.session_state.get("s3_b_dd_actionable_ms") or []))
    if clash:
        st.error(f"A column cannot be both immutable and actionable: "
                 f"{', '.join(sorted(clash))}. Remove it from one of the two lists.")


__all__ = ["_actionability_inputs", "_fairness_precheck"]
