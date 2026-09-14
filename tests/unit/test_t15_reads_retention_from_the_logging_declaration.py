"""A retention period in the declared logging capabilities is log retention (T-20260914-041, case 03)."""
from __future__ import annotations

from aaa.agents.tier2.governance_agent.t15.questions import T15_QUESTIONS
from aaa.tools.document_evidence import Evidence, gather_evidence

_RETENTION = [q for q in T15_QUESTIONS if q.key == "log_retention"]


def _found(declared: dict, passages: list[dict] | None = None) -> Evidence | None:
    """Ground log_retention in *declared* fields and, when given, document *passages*."""
    def search(engagement_id: str, query: str, top_k: int = 8) -> list[dict]:
        del engagement_id, query, top_k
        return list(passages or [])

    return gather_evidence("eng-03" if passages else "", _RETENTION, declared=declared,
                           search=search)["log_retention"]


def test_the_declared_logging_field_answers_in_its_own_sentence() -> None:
    """Case 03: "Per-alert log: ... Retained 3 years." — the second sentence is the retention."""
    found = _found({"logging_capabilities": "Per-alert log: timestamp, crane_id, score. "
                                            "Retained 3 years. Logging system operational."})
    assert found is not None and found.quote == "Retained 3 years."


def test_a_document_sentence_must_still_be_about_logs() -> None:
    """Retention of other records in an uploaded document is not log retention."""
    passage = {"text": "Customer contracts are retained for 10 years.",
               "source_uri": "minio://eng-03/risk_management_file.txt", "score": 0.9}
    assert _found({}, [passage]) is None
