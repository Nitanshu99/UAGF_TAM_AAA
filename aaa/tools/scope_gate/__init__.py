"""scope_gate — deterministic MCP-style tool (§4.5).

Pre-Stage-A scoping gate derived from the Future of Life Institute
"EU AI Act Compliance Checker" (v1.0, 2025-07-28; CC-BY-SA, source:
https://artificialintelligenceact.eu/assessment/eu-ai-act-compliance-checker/).

Runs over the optional FLI-derived fields on a Stage A (T01a) payload
and returns a single verdict plus a list of reasoning strings each
citing the controlling Article. Designed to fail fast before the
IntakeValidator triggers Phase 1.

Verdict semantics:
  in_scope     – continue to Stage B / Phase 1 (default safe verdict).
  prohibited   – Art. 5 practice declared; engagement halts immediately.
  excluded     – Art. 2 full exclusion (military / third-country LEA).
  out_of_scope – no Art. 2 territorial nexus to the Union.

Derived flags (always populated, used by the Orchestrator / T17):
  become_provider_under_art25 – any Art. 25 §§1–2 status change declared.
  triggers_fria               – public body / public service + high risk.
  triggers_art50_transparency – any Art. 50 trigger declared.
  is_gpai_systemic            – GPAI model meeting Art. 51 §2 threshold."""
from aaa.tools.scope_gate.core import scope_gate  # noqa: F401
from aaa.tools.scope_gate.halt_gates import _halt_gates  # noqa: F401
from aaa.tools.scope_gate.scopeverdict import (  # noqa: F401
    _ART25_TRIGGERS,
    _FULL_EXCLUSIONS,
    _TERRITORIAL_NEXUS,
    ScopeGateResult,
    ScopeVerdict,
    _art25_flag,
    _art50_flag,
)

__all__ = [
    'ScopeVerdict', '_FULL_EXCLUSIONS', '_TERRITORIAL_NEXUS', '_ART25_TRIGGERS', 'ScopeGateResult',
    '_art25_flag', '_art50_flag', '_halt_gates', 'scope_gate',
]
