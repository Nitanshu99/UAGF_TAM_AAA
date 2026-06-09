"""
aaa.agents.tier1.agent_initializer — Lazy agent instantiation for the Orchestrator.

Provides ``initialise_agents(evidence_store, regulatory_rag)`` which attempts
to import and construct every phase agent, logging a warning on failure so that
the Orchestrator always starts (falling back to stubs).
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_AGENT_SPECS: list[tuple[str, str, dict[str, Any]]] = [
    # (attr_name, module_path.ClassName, extra_kwargs)
    ("scope_agent",       "aaa.agents.tier2.scope_agent.ScopeAgent",         {"regulatory_rag": None}),
    ("data_auditor",      "aaa.agents.tier2.data_auditor.DataAuditor",        {}),
    ("model_validator",   "aaa.agents.tier2.model_validator.ModelValidator",  {}),
    ("output_fairness",   "aaa.agents.tier2.output_fairness.OutputFairnessTester", {}),
    ("governance_agent",  "aaa.agents.tier2.governance_agent.GovernanceAgent", {}),
    ("report_architect",  "aaa.agents.tier2.report_architect.ReportArchitect", {}),
    ("uagf_tam_l",        "aaa.agents.tier3.uagf_tam_l.UagfTamLBranch",       {}),
    ("cyber_agent",       "aaa.agents.tier3.cyber_agent.CyberSecurityAgent",  {}),
    ("privacy_agent",     "aaa.agents.tier3.privacy_agent.PrivacyDPOAgent",   {}),
]


def _import_class(dotted_path: str):
    """Import and return a class from a dotted module.ClassName path."""
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def initialise_agents(
    evidence_store: Any,
    regulatory_rag: Any = None,
) -> dict[str, Any]:
    """Attempt to construct all phase agents.  Returns attr_name → agent dict."""
    agents: dict[str, Any] = {attr: None for attr, _, _ in _AGENT_SPECS}

    if evidence_store is None:
        return agents

    for attr_name, class_path, extra in _AGENT_SPECS:
        try:
            cls = _import_class(class_path)
            kwargs: dict[str, Any] = {"evidence_store": evidence_store}
            if "regulatory_rag" in extra:
                kwargs["regulatory_rag"] = regulatory_rag
            agents[attr_name] = cls(**kwargs)
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "Could not instantiate %s: %s; stub will be used.", class_path, exc
            )

    return agents


__all__ = ["initialise_agents"]
