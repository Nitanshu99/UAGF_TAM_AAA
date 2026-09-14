"""End-to-end proof of the agreed S6/S7 contract: full audit-state echo.

Complements test_postprocess.py (unit tests on the extraction function in
isolation) by exercising the real ExternalXAIProvider.evaluate() call path
against a mocked S6 that behaves per the agreed contract — echoing the full
state back with only its own section populated.
"""
from __future__ import annotations

import httpx
import respx

from aaa.integrations.xai import ExternalXAIProvider

_STATE = {"engagement_id": "eng-x", "client_submission": {"stage_a": {}},
         "final_verdict": "FAIL"}


@respx.mock
def test_full_state_echo_extracts_only_its_own_section() -> None:
    """A partner attempt to upgrade the verdict inside the echo never applies."""
    echo = {**_STATE, "final_verdict": "PASS",  # attempted verdict upgrade
           "xai_evidence": {"shap": {"top": ["income"]}}}
    respx.post("http://s6.example/api/v1/evaluate").mock(
        return_value=httpx.Response(200, json=echo))
    evidence = ExternalXAIProvider("http://s6.example").evaluate(_STATE)
    assert evidence == {"shap": {"top": ["income"]}, "evidence_source": "external"}
    assert _STATE["final_verdict"] == "FAIL"  # untouched — the echo's copy was discarded
