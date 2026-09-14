"""Finding F10 — a tool the model names either ran, or is said not to have.

At case 01 call #003 the DataAuditor's `tool_calls` asked for
`drift_test(training, evaluation)`. The pass-B payload carried no drift key, so
the assessment recorded the tool as "requested but not executed". It was worse
than that: `run_drift` **had** run — on every Phase 2 dispatch, Art. 10 §2(g) —
and its result reached nothing. Not the model's payload, not the T07 `drift`
block (hardcoded to nulls), not the Report's tool log. The model asked for the
one tool whose output the runtime was throwing away.

Two defects, pinned separately here: the discarded drift result, and the silent
divergence that hid it.
"""
from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

import pytest

from aaa.agents.tier2.data_auditor.report import assemble_report
from aaa.agents.tier2.data_auditor.t07 import build_t07
from aaa.agents.tier2.tools_run import PHASE_TOOLS, tools_run
from aaa.tools.evidence_retrieval.acompletion_json_react import acompletion_json_react
from aaa.tools.evidence_retrieval.tool_requests import check_tool_requests, requested_tools

_ROOT = Path(__file__).resolve().parents[2]

#: call #003's `tool_calls`, verbatim (URIs shortened).
CALL_003_TOOL_CALLS = [
    "data_profile(minio://eng-01/training_dataset.csv)",
    "missingness_scan(minio://eng-01/training_dataset.csv)",
    "class_balance(minio://eng-01/training_dataset.csv)",
    "pii_scan(minio://eng-01/training_dataset.csv)",
    "drift_test(minio://eng-01/training_dataset.csv, minio://eng-01/evaluation_dataset.csv)",
]

_DRIFT_RAN = {
    "computed": True, "reason": None,
    "features": [{"feature": "age", "psi": 0.31, "band": "major", "kind": "numeric"},
                 {"feature": "score", "psi": 0.04, "band": "none", "kind": "numeric"}],
    "max_psi": 0.31, "drifted_features": ["age"], "verdict": "FAIL",
}
_DRIFT_NOT_RUN = {
    "computed": False, "reason": "training or evaluation dataset unavailable",
    "features": [], "max_psi": None, "drifted_features": [], "verdict": "NOT_COMPUTED",
}


def _ctx(drift: dict[str, Any]) -> dict[str, Any]:
    """Minimal Phase 2 analysis context for report assembly."""
    return {
        "profile_result": {"num_rows": 1000, "num_columns": 20},
        "miss_result": {"overall_missingness_pct": 0.0},
        "balance_result": {"imbalance_detected": False},
        "pii_result": {"pii_detected": False, "entities_found": []},
        "drift_result": drift, "client_doc_hits": [], "findings": [],
        "evidence_uris": [],
        "verdict": "PASS", "insufficient": set(), "special_cat_delta": False,
        "effective_special_cat": False,
    }


class _Agent:
    """Replays one scripted reply and records the payload it was given."""

    name = "DataAuditor"

    def __init__(self, reply: dict[str, Any]) -> None:
        self._reply = reply
        self.payload: dict[str, Any] = {}

    async def acompletion_json(self, _prompt: str, payload: Any) -> dict[str, Any]:
        """Return the scripted reply, keeping the payload for inspection."""
        self.payload = payload
        return dict(self._reply)


# --------------------------------------------------------------------------- #
# the discarded tool result
# --------------------------------------------------------------------------- #

def test_t07_records_the_drift_the_tool_measured():
    """The block was nulls while `drift_test` returned PSI 0.31 on `age`."""
    t07 = build_t07("eng-01", {}, {}, {}, {}, "PASS", "2026-09-01T00:00:00Z",
                    drift_result=_DRIFT_RAN,
                    reference_uri="minio://eng-01/training_dataset.csv")
    assert t07["drift"] == {
        "reference_dataset_uri": "minio://eng-01/training_dataset.csv",
        "drift_detected": True, "drifted_columns": ["age"],
        "drift_share": 0.5, "test_method": "population_stability_index"}


def test_t07_distinguishes_no_drift_from_not_measured():
    """"Measured, none found" and "could not measure" are different findings."""
    measured = build_t07("e", {}, {}, {}, {}, "PASS", "t",
                         drift_result={**_DRIFT_RAN, "drifted_features": [],
                                       "verdict": "PASS"})["drift"]
    not_run = build_t07("e", {}, {}, {}, {}, "PASS", "t",
                        drift_result=_DRIFT_NOT_RUN)["drift"]
    assert measured["drift_detected"] is False
    assert measured["test_method"] == "population_stability_index"
    assert not_run["drift_detected"] is None
    assert not_run["test_method"] is None


def test_t07_drift_block_still_matches_its_schema():
    """`additionalProperties: false` would reject an invented key at render."""
    import json

    schema = json.loads((
        _ROOT / "packages/uagf_tam_templates/src/uagf_tam_templates/schemas"
                "/T07_data_quality_report.json").read_text(encoding="utf-8"))
    allowed = set(schema["properties"]["drift"]["properties"])
    block = build_t07("e", {}, {}, {}, {}, "PASS", "t", drift_result=_DRIFT_RAN)["drift"]
    assert set(block) == allowed


def test_the_report_tool_log_names_the_drift_test():
    """Phase 2's log listed four tools while its runtime ran five."""
    report = assemble_report(_ctx(_DRIFT_RAN), {"T06_datasheet_for_datasets": "u"},
                             None, "note")
    entry = next(t for t in report["tool_calls"] if t["tool"] == "drift_test")
    assert "computed=True" in entry["result"] and "verdict=FAIL" in entry["result"]


def test_the_report_tool_log_covers_every_tool_the_phase_runs():
    """The omission that hid the drift step: a tool that ran and was not logged."""
    logged = {t["tool"] for t in assemble_report(
        _ctx(_DRIFT_NOT_RUN), {"T06_datasheet_for_datasets": "u"}, None, "n")["tool_calls"]}
    assert set(PHASE_TOOLS["P2"]) <= logged


# --------------------------------------------------------------------------- #
# the silent divergence
# --------------------------------------------------------------------------- #

def test_requested_tools_reads_the_call_expressions_the_model_writes():
    """Models emit `name(args)` strings, or `{"tool": name}` dicts."""
    assert requested_tools({"tool_calls": CALL_003_TOOL_CALLS}) == [
        "data_profile", "missingness_scan", "class_balance", "pii_scan", "drift_test"]
    assert requested_tools({"tool_calls": [{"tool": "metric_suite"}]}) == ["metric_suite"]
    assert not requested_tools({"summary": "no tools"})


def test_an_unexecuted_tool_is_named_in_the_log(caplog):
    """The assessed run's exact condition, had drift genuinely not run."""
    payload = {"tools_executed": ["data_profile", "missingness_scan",
                                  "class_balance", "pii_scan"]}
    with caplog.at_level(logging.WARNING):
        check_tool_requests({"tool_calls": CALL_003_TOOL_CALLS}, payload, "DataAuditor")
    assert "drift_test" in caplog.text
    assert "pii_scan" not in caplog.text.split("Tools that ran")[0]


def test_a_tool_that_ran_produces_no_warning(caplog):
    """Post-fix Phase 2: every tool #003 asked for is in `tools_executed`."""
    payload = {"tools_executed": tools_run("P2")}
    with caplog.at_level(logging.WARNING):
        check_tool_requests({"tool_calls": CALL_003_TOOL_CALLS}, payload, "DataAuditor")
    assert not caplog.text


def test_a_payload_declaring_nothing_still_reports_the_divergence(caplog):
    """A caller that declares no tools cannot make a model's request true."""
    with caplog.at_level(logging.WARNING):
        check_tool_requests({"tool_calls": ["drift_test()"]}, {}, "DataAuditor")
    assert "drift_test" in caplog.text and "none declared" in caplog.text


def test_the_field_is_stripped_from_the_reply():
    """A field the runtime does not honour must not travel as if it did (F15's rule)."""
    out = check_tool_requests(
        {"summary": "s", "confidence": 0.8, "tool_calls": CALL_003_TOOL_CALLS}, {}, "A")
    assert "tool_calls" not in out
    assert out == {"summary": "s", "confidence": 0.8}


@pytest.mark.asyncio
async def test_the_react_loop_applies_the_check_to_the_final_reply(caplog):
    """End to end: the loop every phase agent shares, not just the helper."""
    agent = _Agent({"summary": "Phase 2 complete.",
                    "tool_calls": ["drift_test(a, b)"]})
    with caplog.at_level(logging.WARNING):
        result = await acompletion_json_react(
            agent, "phase2_data",
            {"tool_outputs": {}, "tools_executed": ["data_profile"]}, rounds=1)
    assert "tool_calls" not in result
    assert "drift_test" in caplog.text


# --------------------------------------------------------------------------- #
# what the model is told
# --------------------------------------------------------------------------- #

def test_every_phase_declares_the_tools_it_ran():
    """`tool_outputs` keys are not tool names — the model had to guess.

    Searched across each agent's package rather than in one file: a phase may build
    its prompt payload in its own module, and what matters is that the payload it
    sends declares the tools that ran.
    """
    import re

    for phase, module in (("P1", "scope_agent"), ("P2", "data_auditor"),
                          ("P3", "model_validator"), ("P4", "output_fairness"),
                          ("P5", "governance_agent"), ("P6", "report_architect")):
        pkg = _ROOT / "aaa/agents/tier2" / module
        source = "\n".join(f.read_text(encoding="utf-8") for f in sorted(pkg.rglob("*.py")))
        assert re.search(rf'"tools_executed": tools_run\("{phase}"', source), module


def test_phase_3_offers_the_explainability_tool_it_actually_ran():
    """`techniques` are recorded as `shap`; the prompt lists `shap_explain`."""
    assert tools_run("P3", techniques=["shap"]) == [
        "metric_suite", "robustness_probe", "shap_explain"]
    assert "lime_explain" not in tools_run("P3", techniques=["shap"])


def test_client_doc_search_is_declared_only_when_it_ran():
    """It is guarded on the engagement having an ingested document collection."""
    assert "client_doc_search" in tools_run("P2", client_docs=True)
    assert "client_doc_search" not in tools_run("P2")


def test_every_declared_tool_is_a_tool_this_repo_has():
    """A name the model is offered must resolve to something that can run."""
    available = {p.name for p in (_ROOT / "aaa/tools").iterdir()
                 if p.is_dir() and not p.name.startswith("__")}
    available |= {p.stem for p in (_ROOT / "aaa/tools").glob("*.py")}
    declared = {name for names in PHASE_TOOLS.values() for name in names}
    declared |= {"shap_explain", "lime_explain", "gradcam_explain", "text_explain",
                 "client_doc_search"}
    assert declared - available <= {"client_doc_search"}, declared - available


def test_no_phase_prompt_still_invites_a_tool_call():
    """The skeleton showed `tool_calls` while the same section said not to emit one."""
    from aaa.platform.prompt_registry import load_prompt

    for name in ("phase1_scope", "phase2_data", "phase3_model", "phase4_output",
                 "phase5_governance", "phase6_report"):
        prompt = load_prompt(name)
        assert '"tool_calls"' not in prompt, name
        assert "tools_executed" in prompt, name
        assert "You cannot request a tool" in prompt, name


def test_the_report_contract_marks_the_field_runtime_derived():
    """§4.2 is the contract; it showed a bare `tool_calls: []` for the model to fill."""
    source = (_ROOT / "PROMPT.md").read_text(encoding="utf-8")
    contract = source.split("### 4.2 Report", 1)[1].split("###", 1)[0]
    assert "derived by the runtime" in contract


def test_the_tool_log_lists_only_tools_the_phase_declares():
    """Report tool logs and `PHASE_TOOLS` are one statement, kept in step."""
    infra = {"prompt_runtime", "client_doc_search", "explainability",
             "template_render", "report_render"}
    for phase, module in (("P1", "scope_agent"), ("P2", "data_auditor"),
                          ("P3", "model_validator"), ("P4", "output_fairness"),
                          ("P5", "governance_agent"), ("P6", "report_architect")):
        tree = ast.parse((_ROOT / f"aaa/agents/tier2/{module}/report.py")
                         .read_text(encoding="utf-8"))
        logged = {node.values[i].value
                  for node in ast.walk(tree) if isinstance(node, ast.Dict)
                  for i, key in enumerate(node.keys)
                  if isinstance(key, ast.Constant) and key.value == "tool"
                  and isinstance(node.values[i], ast.Constant)}
        assert logged - infra == set(PHASE_TOOLS[phase]) - infra, module
