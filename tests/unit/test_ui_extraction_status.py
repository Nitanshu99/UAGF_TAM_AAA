"""Extraction failure must not be reported as document absence (M23).

The wizard rendered "Not found in uploaded documents — please fill in manually"
for every empty field, and `empty_result()` was returned for five different
causes. Only one of them is a statement about the customer's documents. On the
2026-09-10 UI run the extraction agent read all ten uploads, extracted every
field, mis-escaped the first value so the whole 9,327-character reply collapsed
into one key, and the customer was told their dossier was empty.
"""
from __future__ import annotations

from aaa.agents.doc_intelligence.parse import build_result
from aaa.agents.doc_intelligence.queries import FIELD_QUERIES, empty_result

_FIELDS = list(FIELD_QUERIES)
_CTX = {f: {"context": "…", "best_source": "doc.txt"} for f in _FIELDS}


def _entry(v="x", c=0.9):
    return {"value": v, "confidence": c}


def test_no_documents_is_the_only_honest_absence():
    assert empty_result("no_documents")["extraction_status"] == "no_documents"


def test_each_failure_keeps_its_own_name():
    for status in ("not_indexed", "no_context", "llm_failed", "unparsable_reply"):
        assert empty_result(status)["extraction_status"] == status


def test_default_status_is_the_absence_case():
    """The historical call had no argument; it meant 'no documents'."""
    assert empty_result()["extraction_status"] == "no_documents"


def test_a_full_extraction_is_ok():
    out = build_result({f: _entry() for f in _CTX}, _CTX)
    assert out["extraction_status"] == "ok"
    assert not out["missing_fields"]


def test_a_thin_but_real_dossier_is_still_ok():
    """A dossier really can be missing most of Annex IV — that is a finding,
    not a parse failure, and must not be labelled one."""
    keep = max(2, int(len(_FIELDS) * 0.25))
    out = build_result({f: _entry() for f in _FIELDS[:keep]}, _CTX)
    assert out["extraction_status"] == "ok"
    assert len(out["missing_fields"]) == len(_FIELDS) - keep


def test_the_collapsed_reply_is_caught():
    """One field recovered, with contexts found for every one of them."""
    out = build_result({_FIELDS[0]: _entry()}, _CTX)
    assert out["extraction_status"] == "unparsable_reply"


def test_an_empty_reply_is_caught():
    assert build_result({}, _CTX)["extraction_status"] == "unparsable_reply"


def test_low_confidence_values_do_not_count_as_yield():
    """Below the floor a value is discarded, so it cannot mask a broken reply."""
    out = build_result({f: _entry(c=0.05) for f in _CTX}, _CTX)
    assert out["extraction_status"] == "unparsable_reply"


def test_no_contexts_is_not_blamed_on_the_reply():
    assert build_result({}, {})["extraction_status"] == "ok"


# --- M24: what step 0 collects must survive a rerun and outlive its widgets ---
#
# M24 was about an "Engagement ID" text input whose default was a fresh uuid
# computed on every rerun, so anything the customer typed was replaced by a
# random id the next time any widget on the page changed. That input is gone:
# an engagement id is our filing reference, not something a customer should be
# asked to invent, and it is now derived from the company name on submit.
#
# The hazard it exposed is not gone, because step 0 still has text inputs whose
# values every later step depends on. These tests hold the same two properties
# against the two fields that replaced it.

def test_step0_fields_own_their_widget_keys():
    """Typing must survive a rerun, so each input owns a key of its own."""
    import inspect

    from aaa.ui.wizard import step0
    src = inspect.getsource(step0.render_step_0)
    assert 'key="step0_company"' in src
    assert 'key="step0_system"' in src


def test_what_step0_collects_is_copied_off_its_widget_keys_on_submit():
    """Streamlit drops a widget's key once the widget stops rendering, so the
    values later steps read cannot live on the widget keys themselves."""
    import inspect

    from aaa.ui.wizard import step0
    src = inspect.getsource(step0._begin)
    assert 'st.session_state["engagement_id"] =' in src
    assert 'st.session_state["intake_identity"] =' in src


def test_the_engagement_id_is_minted_once_rather_than_per_rerun():
    """A fresh uuid per rerun is what discarded the customer's work in M24."""
    import inspect

    from aaa.ui.wizard import step0
    # The only uuid call sits behind the submit handler, never in the render path.
    assert "uuid" not in inspect.getsource(step0.render_step_0)
    assert "new_engagement_id" in inspect.getsource(step0._begin)


def test_the_engagement_id_carries_the_company_it_belongs_to():
    """A reference a human has to quote back to us should be legible."""
    from aaa.ui.wizard.step0 import new_engagement_id

    generated = new_engagement_id("Mariposa-Edu GmbH")
    assert generated.startswith("eng-mariposa-edu-gmbh-")
    assert generated != new_engagement_id("Mariposa-Edu GmbH")  # unique per run
    assert new_engagement_id("   ").startswith("eng-")  # blank still yields one
    assert " " not in new_engagement_id("Ünïcødé & Co / Ltd.")


# --- M26: a conditional question inside st.form is unreachable ---------------

def test_the_special_category_question_is_always_rendered():
    """`st.form` does not rerun on widget change, so a question gated on another
    widget in the same form never appears — `special_category_data` could only
    ever be False from the wizard, and Art. 10 §5 turns on it."""
    import inspect

    from aaa.ui.wizard.step2 import form
    src = inspect.getsource(form.render_questions)
    marker = '**3a. Does it process special-category data?**'
    assert marker in src
    body = src.split(marker)[0]
    # The question must not sit behind `if gdpr_overlap:`.
    assert not body.rstrip().endswith("if gdpr_overlap:")
    # …and the answer still only counts when personal data is processed.
    assert "special_category_data and gdpr_overlap" in src


# --- M27: the run gate must not pass a blank required Stage A field ----------

#: The three Stage A selects, declared — T-20260914-021 made them required too.
_DECLARED = {"declared_modality": "tabular", "declared_risk_tier": "high",
             "deployment_context": "b2b"}


def test_required_stage_a_fields_block_the_run(monkeypatch):
    from aaa.ui.wizard.step3 import required_fields
    monkeypatch.setattr(required_fields, "collect_stage_a", lambda: {
        "provider_name": "", "system_name": "S", "version": "1", "intended_purpose": "P",
        **_DECLARED})
    assert required_fields._required_stage_a_blanks() == ["Legal provider name"]


def test_a_complete_stage_a_blocks_nothing(monkeypatch):
    from aaa.ui.wizard.step3 import required_fields
    monkeypatch.setattr(required_fields, "collect_stage_a", lambda: {
        "provider_name": "Mariposa-Edu GmbH", "system_name": "Mariposa",
        "version": "1.0.0", "intended_purpose": "Matching", **_DECLARED})
    assert required_fields._required_stage_a_blanks() == []


def test_whitespace_is_not_a_value(monkeypatch):
    from aaa.ui.wizard.step3 import required_fields
    monkeypatch.setattr(required_fields, "collect_stage_a", lambda: {
        "provider_name": "   ", "system_name": "S", "version": "1", "intended_purpose": "P",
        **_DECLARED})
    assert required_fields._required_stage_a_blanks() == ["Legal provider name"]


# --- M28: step 3 must survive a trip to the results screen and back ----------

def test_step3_state_is_reseeded_on_every_entry():
    """Streamlit drops the `s3_*` widget keys when step 3 stops rendering, so an
    early return on `step3_initialized` left the form blank on the way back —
    95 % completeness became 35 % with the auto-fill captions still showing."""
    import inspect

    from aaa.ui.wizard.step3 import state
    src = inspect.getsource(state.initialise_step3_state)
    assert 'if st.session_state.get("step3_initialized"):\n        return' not in src
    # What the customer last confirmed outranks the extraction it started from.
    assert 'st.session_state.get("step4_stage_a")' in src
    assert "**confirmed_a" in src


# --- M29: the run gate must cover the modality-conditional Stage B set -------

def _nav(monkeypatch, modality, stage_b):
    """Point the blockers module at a declaration and hand it back."""
    from aaa.ui.wizard.step3 import required_fields
    monkeypatch.setattr(required_fields, "collect_stage_a", lambda: {"declared_modality": modality})
    monkeypatch.setattr(required_fields, "collect_stage_b", lambda: stage_b)
    return required_fields


_LLM_COMPLETE = {"system_prompt_uri": "minio://a", "rag_manifest_uri": "minio://b",
                 "guardrail_config_uri": "minio://c", "golden_set_uri": "minio://d"}


def test_a_tabular_system_has_no_conditional_requirements(monkeypatch):
    required_fields = _nav(monkeypatch, "tabular", {})
    assert required_fields._conditional_stage_b_blanks() == []


def test_an_llm_system_missing_its_documents_is_blocked(monkeypatch):
    required_fields = _nav(monkeypatch, "llm", {"rag_manifest_uri": "minio://b"})
    assert required_fields._conditional_stage_b_blanks() == [
        "System prompt", "Guardrail configuration", "Golden evaluation set"]


def test_a_complete_llm_dossier_is_not_blocked(monkeypatch):
    required_fields = _nav(monkeypatch, "llm", dict(_LLM_COMPLETE))
    assert required_fields._conditional_stage_b_blanks() == []


def test_tool_inventory_is_required_only_for_agentic(monkeypatch):
    required_fields = _nav(monkeypatch, "llm", dict(_LLM_COMPLETE))
    assert "Tool inventory" not in required_fields._conditional_stage_b_blanks()
    required_fields = _nav(monkeypatch, "agentic", dict(_LLM_COMPLETE))
    assert required_fields._conditional_stage_b_blanks() == ["Tool inventory"]


# --- M30: a UI run must leave the same durable record as the API path --------

def test_the_ui_run_persists_its_deliverables():
    """The wizard calls run_pipeline directly and so never reached
    record_completion — the only caller of save_result. A UI run rendered its
    results and wrote nothing: no data/results, no customer deliverables, no
    entry in the run archive."""
    import inspect

    from aaa.ui.wizard.step4 import persist, run
    src = inspect.getsource(persist)
    assert "save_result(eid, final)" in src
    assert "save_customer_artefacts(eid, final, store)" in src
    # …and it is called on the success path, after the pipeline returns.
    assert "_persist(eid, final, store)" in inspect.getsource(run.execute_pipeline)


def test_a_persistence_failure_does_not_cost_the_results(monkeypatch):
    """The customer is looking at a valid audit; a disk problem must not raise."""
    from aaa.ui.wizard.step4 import persist
    monkeypatch.setattr(persist, "save_result", lambda *a: (_ for _ in ()).throw(OSError("disk full")))
    monkeypatch.setattr(persist, "save_customer_artefacts", lambda *a: None)
    warned = []
    monkeypatch.setattr(persist.st, "warning", lambda m: warned.append(m))
    persist._persist("eng-x", {}, object())
    assert warned and "not archived" in warned[0]
