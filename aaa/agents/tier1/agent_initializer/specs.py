"""Which phase agents exist, where each class lives, and how it is constructed."""
from __future__ import annotations

import importlib
from typing import Any

#: ``(attr_name, module_path.ClassName, extra_kwargs)`` for every phase agent.
_AGENT_SPECS: list[tuple[str, str, dict[str, Any]]] = [
    ("scope_agent",       "aaa.agents.tier2.scope_agent.ScopeAgent",         {"regulatory_rag": None}),
    ("data_auditor",      "aaa.agents.tier2.data_auditor.DataAuditor",        {"regulatory_rag": None}),
    ("model_validator",   "aaa.agents.tier2.model_validator.ModelValidator",  {"regulatory_rag": None}),
    ("output_fairness",   "aaa.agents.tier2.output_fairness.OutputFairnessTester", {"regulatory_rag": None}),
    ("governance_agent",  "aaa.agents.tier2.governance_agent.GovernanceAgent", {"regulatory_rag": None}),
    ("report_architect",  "aaa.agents.tier2.report_architect.ReportArchitect", {}),
    ("client_brief",      "aaa.agents.tier2.client_brief.ClientBriefAgent",    {"regulatory_rag": None}),
    ("uagf_tam_l",        "aaa.agents.tier3.uagf_tam_l.UagfTamLBranch",       {}),
    ("cyber_agent",       "aaa.agents.tier3.cyber_agent.CyberSecurityAgent",  {}),
    ("privacy_agent",     "aaa.agents.tier3.privacy_agent.PrivacyDPOAgent",   {}),
]


def import_class(dotted_path: str):
    """Import and return a class from a dotted ``module.ClassName`` path.

    :param dotted_path: e.g. ``"aaa.agents.tier2.scope_agent.ScopeAgent"``.
    :returns: The class object.
    """
    module_path, class_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


__all__ = ["_AGENT_SPECS", "import_class"]
