"""Bounded plan-then-retrieve (ReAct-style) helper for phase agents.

Phase agents call the LLM once via ``BaseAgent.acompletion_json``. With this
helper, if the model decides it needs more evidence it returns a
``retrieval_plan`` naming additional regulatory and/or client-document queries.
The helper executes those queries against the Regulatory RAG and the engagement's
client-document collection, appends the new hits to the payload, and re-invokes
the model — bounded to a small number of rounds — so agents make ReAct-style
retrieval decisions without a full tool-calling loop.

Accumulated hits are de-duplicated, re-ranked by score and capped
(:mod:`~aaa.tools.evidence_retrieval.dedup`, F6), and the final round is
declared terminal so a plan can no longer be filed as an answer
(:mod:`~aaa.tools.evidence_retrieval.terminal_round`, F15).

Safe by construction: if no ``retrieval_plan`` is emitted (e.g. the prompt has not
yet been updated, or the model is satisfied) this behaves exactly like a single
``acompletion_json`` call."""
from aaa.tools.evidence_retrieval.acompletion_json_react import acompletion_json_react  # noqa: F401
from aaa.tools.evidence_retrieval.dedup import MAX_HITS_PER_KIND, hit_keys, merge_hits  # noqa: F401
from aaa.tools.evidence_retrieval.engagement import engagement_query, engagement_terms  # noqa: F401
from aaa.tools.evidence_retrieval.logger import (  # noqa: F401
    _MAX_QUERIES_PER_KIND,
    _TOP_K,
    _clean_queries,
    _run_plan_queries,
    logger,
)
from aaa.tools.evidence_retrieval.refs import cited_references  # noqa: F401
from aaa.tools.evidence_retrieval.rounds import (  # noqa: F401
    MAX_ROUNDS,
    learned_something,
    round_fits,
)
from aaa.tools.evidence_retrieval.seed import (  # noqa: F401
    LOOKUP_TOP_K,
    MAX_ANCHOR_REFS,
    seed_client_doc_hits,
    seed_regulatory_hits,
)
from aaa.tools.evidence_retrieval.terminal_round import (  # noqa: F401
    TERMINAL_NOTICE,
    OutputContractNotMetError,
    RetrievalPlanNotAnsweredError,
    close_retrieval,
    terminal_block,
)

__all__ = [
    'logger', '_MAX_QUERIES_PER_KIND', '_TOP_K', 'seed_regulatory_hits', '_clean_queries',
    '_run_plan_queries', 'acompletion_json_react', 'MAX_HITS_PER_KIND', 'merge_hits',
    'TERMINAL_NOTICE', 'RetrievalPlanNotAnsweredError', 'OutputContractNotMetError', 'close_retrieval', 'terminal_block',
    'seed_client_doc_hits', 'engagement_query', 'engagement_terms', 'cited_references',
    'MAX_ANCHOR_REFS', 'LOOKUP_TOP_K', 'MAX_ROUNDS', 'round_fits',
    'learned_something', 'hit_keys', '__all__',
]
