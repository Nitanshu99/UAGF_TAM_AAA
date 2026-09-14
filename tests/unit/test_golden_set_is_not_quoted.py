"""A golden evaluation set is data the audit measures, never quoted as the provider's account."""
from __future__ import annotations

from aaa.tools.document_evidence import Question, Search, gather_evidence

_CONSENT = Question("consent", "consent lawful basis data processing",
                    (("consent*",), ("data", "gdpr", "lawful basis", "processing")), ())


def _search(passages: list[dict]) -> Search:
    """A client_doc_search stand-in returning *passages* for every query."""
    return lambda engagement_id, query, top_k=8: list(passages)


def test_a_golden_set_passage_does_not_answer_a_datasheet_question() -> None:
    """Case 04: a GDPR Art. 6(1) excerpt in golden_eval_set.json became the consent mechanism."""
    golden = {"text": "Processing shall be lawful only if the data subject has given consent "
                      "to the processing of personal data (GDPR Art. 6(1)).",
              "source_uri": "minio://eng-04/stage_b/golden_eval_set.json",
              "document_role": "golden_set", "score": 0.9}
    found = gather_evidence("eng-04", [_CONSENT], search=_search([golden]))
    assert found["consent"] is None


def test_a_provider_document_still_answers_it() -> None:
    """The same sentence in the provider's own risk file is the provider's account."""
    document = {"text": "Applicants give consent to the processing of their data under GDPR "
                        "Art. 6(1)(a) when they upload a CV.",
                "source_uri": "minio://eng-04/stage_b/risk_management_file.txt",
                "document_role": "risk_management_file", "score": 0.9}
    found = gather_evidence("eng-04", [_CONSENT], search=_search([document]))
    assert found["consent"] is not None
