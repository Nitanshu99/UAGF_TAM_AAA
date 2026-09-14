"""Persisting a finished run, and what a rejected intake reports instead."""
from __future__ import annotations

import logging

import streamlit as st

from aaa.agents.intake_validator import IntakeValidatorError
from aaa.data.writer import save_customer_artefacts, save_result
from aaa.platform.evidence import EvidenceStore

logger = logging.getLogger(__name__)


def _intake_failed(exc: IntakeValidatorError) -> None:
    """Send the customer back to the field that stopped the audit.

    Named for what it is to them — something on the form needs fixing — with
    the validator's own words kept, but folded away rather than shouted.

    :param exc: The validation error raised before any phase ran.
    """
    st.error("We could not start the audit — something on the previous step "
             f"needs correcting.\n\n**{exc.reason}**")
    if exc.details:
        with st.expander("The exact validation error", expanded=False):
            st.json(exc.details)
    if st.button("←  Back to the form", type="primary"):
        st.session_state["step"] = 3
        st.rerun()
def _persist(eid: str, final: dict, store: EvidenceStore) -> None:
    """Write the run's deliverables to disk, as the API path does (M30).

    The wizard calls ``run_pipeline`` directly and so never reached
    ``api.routes.workflow.finish.record_completion``, which is the only caller
    of ``save_result`` / ``save_customer_artefacts``. A UI run therefore
    rendered its results on screen and wrote **nothing**: no
    ``data/results/<id>/``, no ``data/customer/<company>/`` deliverables, and no
    entry in the run archive — so the run-identity record that exists to make
    every delivered audit reproducible simply did not cover audits started from
    the UI, which is the way a customer starts one.

    Failures here must not cost the customer the results they are looking at, so
    the run stands and the problem is surfaced rather than raised.

    :param eid: Engagement identifier.
    :param final: The final audit state.
    :param store: Evidence store holding the engagement's artefacts.
    """
    try:
        save_result(eid, final)
        save_customer_artefacts(eid, final, store)
        # The API's finish step counts every completed engagement for the
        # "engagements by final verdict" panel; a wizard run never reached it,
        # so runs started the way a customer starts one stayed off the
        # dashboard. Counted after the deliverables so a failed write is not
        # reported as a completion.
        from aaa.observability.metrics import ENGAGEMENT_COUNTER
        ENGAGEMENT_COUNTER.labels(
            status="completed", final_verdict=str(final.get("final_verdict"))).inc()
    except Exception as exc:  # noqa: BLE001 — the results on screen are still valid
        logger.warning("Could not persist deliverables for %s: %s", eid, exc)
        st.warning(
            "The audit completed, but its deliverables could not be written to "
            f"disk ({exc}). The results below are correct; download them from "
            "this page, because they are not archived.")


__all__ = ["_intake_failed", "_persist"]
