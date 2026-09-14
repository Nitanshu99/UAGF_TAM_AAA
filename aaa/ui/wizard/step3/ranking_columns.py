"""The data dictionary's two ranking columns, for a system that ranks items per query.

A ranking case declared precision@k and NDCG@k, and its evaluation set records the
system's rank per query and a human relevance decision on each row. The wizard
could not say which columns those were, so a submission made through it left the declared
figures unverified (T-20260914-033). The columns are declared, never guessed from their
names: the auditor recomputes the metrics within the query column, in rank-column order.
"""
from __future__ import annotations

import streamlit as st

#: Data-dictionary field → (label, select key, free-text key, help).
RANKING_FIELDS = {
    "query_column": (
        "Ranking query column (optional)", "s3_b_dd_rank_query_sel", "s3_b_dd_rank_query",
        "Only for a system that ranks items: the column naming each ranked list, "
        "e.g. a request id. Precision@k and NDCG@k are computed within it."),
    "rank_column": (
        "Rank position column (optional)", "s3_b_dd_rank_position_sel",
        "s3_b_dd_rank_position",
        "Only for a system that ranks items: each row's position in its list, 1 = top."),
}


def render_ranking_columns(columns: list[str]) -> None:
    """Render the query and rank-position inputs, and flag a partial or clashing pair.

    :param columns: Column names from the uploaded dataset header; free text when empty.
    """
    chosen = []
    for label, select_key, text_key, help_text in RANKING_FIELDS.values():
        if columns:
            st.selectbox(label, options=["", *columns], key=select_key, help=help_text)
        else:
            st.text_input(label, key=text_key, help=help_text)
        chosen.append(str(st.session_state.get(select_key if columns else text_key) or "").strip())
    if chosen[0] and chosen[0] == chosen[1]:
        st.error("The ranking query column and the rank position column must differ.")
    elif bool(chosen[0]) != bool(chosen[1]):
        st.warning("Declare both ranking columns or neither — one alone is not recorded.")


__all__ = ["RANKING_FIELDS", "render_ranking_columns"]
