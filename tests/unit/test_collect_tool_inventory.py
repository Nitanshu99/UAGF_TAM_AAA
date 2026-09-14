"""collect_stage_b() must parse the new tool_inventory text input into a list.

Regression test for the sibling dead-field bug: tool_inventory is declared in
AnnexIVDossier and read by t16.py for trajectory_audit's permitted_tools
check, but no wizard widget ever let a user populate it.
"""
from __future__ import annotations

import streamlit as st

from aaa.ui.wizard.collect.stage.b import collect_stage_b


def test_tool_inventory_parses_comma_separated_input(monkeypatch):
    """A comma-separated tool_inventory input becomes a stripped list."""
    monkeypatch.setattr(st, "session_state", {
        "s3_b_tool_inventory_raw": "web_search, code_executor,  send_email ",
    })
    assert collect_stage_b()["tool_inventory"] == ["web_search", "code_executor", "send_email"]


def test_tool_inventory_defaults_to_empty_list(monkeypatch):
    """No tool_inventory input at all → an empty list, not a missing key."""
    monkeypatch.setattr(st, "session_state", {})
    assert collect_stage_b()["tool_inventory"] == []
