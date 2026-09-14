"""Wizard progress rail and extraction-provenance captions."""
from __future__ import annotations

import streamlit as st

from aaa.ui.styles import render_stepper
from aaa.ui.wizard.parsing import confidence_label

_STEP_LABELS = ["Get started", "Your documents", "A few questions",
                "Check the details", "Your results"]


def render_progress(step: int) -> None:
    """Render the five-step progress rail.

    :param step: Zero-based index of the active step.
    """
    render_stepper(step, _STEP_LABELS)


#: Statuses that are not a failure to apologise for. ``ok`` and
#: ``no_documents`` describe an extraction that ran; ``not_attempted`` is the
#: wizard since it stopped extracting at all. Telling a customer "the agent
#: could not read your documents" when nothing tried to read them is M23 with
#: the blame merely moved — still a statement about an event that never happened.
_NO_FAILURE = ("ok", "no_documents", "not_attempted")

#: Why an extraction came back empty → what the customer should be told. Only
#: ``no_documents`` is a statement about their dossier (M23).
_DEGRADED: dict[str, str] = {
    "not_indexed": "Your documents could not be indexed, so this was not read. "
                   "Please fill it in manually and report the problem.",
    "no_context": "Nothing in your documents matched this field's search, so it "
                  "was never put to the agent. Please fill it in manually.",
    "llm_failed": "The extraction agent did not respond, so your documents were "
                  "not read. Please fill it in manually and try again later.",
    "unparsable_reply": "The extraction agent's reply could not be read, so this "
                        "value was lost in transit — not absent from your "
                        "documents. Please fill it in manually.",
}


def extraction_banner(status: str, missing_count: int) -> None:
    """Say once, at the top of the form, that extraction failed (M23).

    :param status: ``extraction_status`` from the :class:`DocExtractionResult`.
    :param missing_count: How many fields were left unfilled.
    """
    if status in _NO_FAILURE:
        return
    st.error(
        f"**The agent could not read your documents — {missing_count} field(s) were "
        f"not pre-filled.** {_DEGRADED.get(status, '')} This is a failure on our "
        f"side, not a gap in what you uploaded; the fields below are blank because "
        f"the extraction did not complete, and the completeness score reflects only "
        f"what you fill in by hand.")


def extraction_status() -> str:
    """The current extraction's status, read from session state.

    Read here rather than threaded through fifteen render call sites, each of
    which already forwards ``confidence``/``sources``/``missing`` from the same
    result object.

    :returns: ``extraction_status``, defaulting to ``ok`` for older results.
    """
    result = st.session_state.get("extraction_result") or {}
    return str(result.get("extraction_status") or "ok")


def field_caption(field: str, confidence: dict, sources: dict, missing: list,
                  status: str | None = None) -> None:
    """Show auto-fill provenance or a missing-field warning below a widget.

    ``missing`` used to be rendered as "Not found in uploaded documents" for
    every cause, including the four where the documents were never successfully
    read (M23). A customer told that acts on it — by going to find documents
    they had already supplied.

    :param field: Field name as used in the extraction result.
    :param confidence: Field → confidence score mapping.
    :param sources: Field → source document mapping.
    :param missing: Fields the agent did not fill.
    :param status: ``extraction_status`` from the extraction result.
    """
    status = status or extraction_status()
    if field in (st.session_state.get("intake_identity") or {}):
        st.caption("You told us this when you started — edit it if it is not right.")
    elif field in confidence:
        pct = int(confidence[field] * 100)
        src = sources.get(field, "document")
        st.caption(f"Auto-filled from {src} · {pct}% {confidence_label(confidence[field])}")
    elif field in missing:
        if status in _NO_FAILURE:
            st.warning("Not found in uploaded documents — please fill in manually.")
        else:
            st.caption("Not pre-filled — see the extraction notice above.")
