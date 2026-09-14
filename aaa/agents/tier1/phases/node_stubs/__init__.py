"""aaa.agents.tier1.phases.node_stubs — Stub node functions for unimplemented phases.

These stubs are used when the real agents are not wired.  Each returns a
minimal artefact + verifier critique so downstream nodes can proceed.

Exported functions:
  - node_phase1_stub(state)
  - node_route(state)
  - node_parallel_phases_stub(state)
  - node_phase5_stub(state)
  - node_hitl_checkpoint(state)
  - node_phase6_stub(state)"""
from aaa.agents.tier1.phases.node_stubs.logger import (  # noqa: F401
    TEMPLATE_ARTICLES,
    _mark_stub_insufficient,
    _stub_artefact,
    _stub_critique,
    logger,
    node_phase1_stub,
)
from aaa.agents.tier1.phases.nodes.hitl_checkpoint import (  # noqa: F401
    node_hitl_checkpoint,
    node_phase6_stub,
)
from aaa.agents.tier1.phases.nodes.route import (  # noqa: F401
    node_parallel_phases_stub,
    node_phase5_stub,
    node_route,
)

__all__ = [
    'logger', 'TEMPLATE_ARTICLES', '_stub_artefact', '_stub_critique', '_mark_stub_insufficient',
    'node_phase1_stub', 'node_route', 'node_parallel_phases_stub', 'node_phase5_stub',
    'node_hitl_checkpoint', 'node_phase6_stub', '__all__',
]
