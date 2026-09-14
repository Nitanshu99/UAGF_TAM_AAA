"""Where the brief sits in the run, and what happens when it is not there.

The brief is the last thing a run does and the first thing the customer reads.
Both halves of that need holding: it must actually be reached and registered on
a normal run, and its absence must cost the customer a document and nothing else
— never the audit, the report, or the evidence chain.
"""
from __future__ import annotations

import pytest

from aaa.agents.tier1.agent_initializer import _AGENT_SPECS
from aaa.agents.tier1.phases.phase_runners.client_brief_step import brief_timeout, run_client_brief
from aaa.agents.tier2.client_brief import TEMPLATE_ID
from aaa.data.writer.customer import _write_client_brief

_STATE: dict = {
    "engagement_id": "eng-test",
    "compliance_matrix": {"Art.10": "FAIL", "Art.5": "PASS"},
    "phase_artefacts": {"T18_audit_report": {"uri": "minio://x", "sha256": "abc"}},
}


class _Agent:
    """A ClientBriefAgent stand-in that reports one stored brief."""

    name = "ClientBrief"

    async def process(self, message):
        """Return a Report registering the brief, as the real agent does."""
        assert message["declaration_summary"] is not None
        return {"phase_id": "P6", "artefact_uri": "minio://eng-test/phase_6/brief.json",
                "summary": "written", "confidence": 1.0, "tool_calls": [],
                "declaration_verification_delta": {
                    "phase_artefacts": {TEMPLATE_ID: {
                        "uri": "minio://eng-test/phase_6/brief.json",
                        "sha256": "deadbeef", "template_id": TEMPLATE_ID}}}}


class _Store:
    """An evidence store holding one markdown brief."""

    def __init__(self, body: str | None = "# Brief\n"):
        self._body = body

    def get_artefact(self, _uri):
        """Return the stored markdown payload, or ``None`` when there is none."""
        return {"format": "markdown", "body": self._body} if self._body else None


def test_the_agent_is_registered_for_construction():
    """The Orchestrator can build the agent, or it reports it unwired."""
    assert any(attr == "client_brief" for attr, _, _ in _AGENT_SPECS)


@pytest.mark.asyncio
async def test_a_written_brief_is_registered_as_an_artefact():
    """A written brief reaches the state, so the customer writer can find it."""
    state = await run_client_brief(_Agent(), {**_STATE, "phase_artefacts": {}})
    assert state["phase_artefacts"][TEMPLATE_ID]["uri"].endswith("brief.json")


@pytest.mark.asyncio
async def test_an_unwired_agent_leaves_the_audit_untouched():
    """No brief agent costs a document; the report and its evidence are unaffected."""
    state = await run_client_brief(None, dict(_STATE))
    assert TEMPLATE_ID not in state["phase_artefacts"]
    assert state["phase_artefacts"]["T18_audit_report"]["uri"] == "minio://x"


@pytest.mark.asyncio
async def test_a_failing_agent_leaves_the_audit_untouched():
    """A brief that raises costs a document and nothing else."""
    class _Broken(_Agent):
        async def process(self, message):
            raise RuntimeError("provider down")

    state = await run_client_brief(_Broken(), dict(_STATE))
    assert TEMPLATE_ID not in state["phase_artefacts"]
    assert state["phase_artefacts"]["T18_audit_report"]["uri"] == "minio://x"


def test_the_agent_carries_a_ceiling_above_its_slowest_measured_call():
    """The 120 s default cost the first run two written sections; 420 s clears 385.8 s."""
    from aaa.agents.tier2.client_brief import ClientBriefAgent
    agent = ClientBriefAgent(evidence_store=None)
    assert agent.timeout is not None and agent.timeout > 385.8
    assert agent._litellm_kwargs()["timeout"] == agent.timeout


def test_the_budget_scales_with_the_number_of_requirements():
    """One call per requirement means the budget cannot be a constant."""
    small = brief_timeout(_STATE)
    large = brief_timeout({**_STATE, "compliance_matrix": {
        f"Art.{n}": "PASS" for n in range(20)}})
    assert large > small > 0


# --------------------------------------------------------------------------
# The deliverable folder
# --------------------------------------------------------------------------
def test_the_brief_is_written_beside_the_pdf(tmp_path):
    """The customer's folder carries the brief next to the formal report."""
    _write_client_brief(tmp_path, "eng-test",
                        {TEMPLATE_ID: {"uri": "minio://x"}}, _Store())
    assert (tmp_path / "eng-test_client_report.md").read_text() == "# Brief\n"


def test_a_missing_brief_writes_no_empty_file(tmp_path):
    """An absent or empty brief leaves no misleading stub in the folder."""
    _write_client_brief(tmp_path, "eng-test", {}, _Store())
    _write_client_brief(tmp_path, "eng-test", {TEMPLATE_ID: {"uri": "minio://x"}},
                        _Store(body=None))
    assert not list(tmp_path.iterdir())
