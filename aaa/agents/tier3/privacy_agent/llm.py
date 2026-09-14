"""LLM synthesis for the PrivacyDPOAgent (Agent 12 prompt over pii_scan output).

``pii_scan`` stays the deterministic tool; the model reasons over detected
categories — Art. 10 §5 lawful-basis interpretation and DPIA cross-reference
narrative — merged into the T08 extension. Failures label the fallback.

Since fix 28 the call goes through
:func:`~aaa.agents.tier3.narrative.run_narrative_synthesis`, which closes
retrieval explicitly and refuses a plan in the answer position (Q4).
"""
from __future__ import annotations

from typing import Any

from aaa.agents.tier3.narrative import run_narrative_synthesis, with_narrative  # noqa: F401

_PROMPT_NAME = "privacy"

#: Reply keys the Agent 12 prompt may return its narrative under.
_NARRATIVE_KEYS = ("privacy_narrative", "summary")

#: The dossier question this spawn actually asks. At call #066 it named the
#: privacy notice, the terms of business and the retention schedule as the
#: documents it could not judge the Art. 10 §5 lawful basis without (M13).
_DOC_QUERY = ("privacy notice, data protection declaration, terms of business, "
              "retention schedule, DPIA, lawful basis for special-category data, "
              "consent and age verification")


async def run_llm_synthesis(agent: Any, decl: dict[str, Any],
                            pii_results: dict[str, Any],
                            merged_categories: list[Any]) -> tuple[str | None, str]:
    """Interpret PII-scan results with the Agent 12 prompt.

    :param agent: The :class:`PrivacyDPOAgent` instance.
    :param decl: Dispatch declaration summary.
    :param pii_results: Output of ``pii_scan`` on the evaluation set.
    :param merged_categories: Special categories after the T08 merge.
    :returns: ``(narrative or None, prompt_note)``.
    """
    return await run_narrative_synthesis(
        agent, _PROMPT_NAME,
        {"declaration_summary": decl, "pii_scan_results": pii_results,
         "special_categories_detected": merged_categories},
        keys=_NARRATIVE_KEYS,
        engagement_id=str(decl.get("engagement_id") or ""),
        client_doc_query=_DOC_QUERY)
