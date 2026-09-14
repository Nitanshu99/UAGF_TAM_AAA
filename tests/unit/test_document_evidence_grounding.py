"""A document passage becomes artefact evidence only when it says what was asked.

Builders left datasheet, model-card and monitoring fields null or hardcoded while
the provider's own documents answered them (T-20260913-041). The fix must not
swing the other way and read a declared gap, a plan or a risk as a capability:
these cases are the shapes provider documents actually take.
"""
from __future__ import annotations

from aaa.tools.document_evidence import (
    DATE_RANGE,
    DENIALS,
    NEGATIONS,
    PERIODS,
    Question,
    gather_evidence,
    ground,
)
from aaa.tools.document_evidence.ground import units
from aaa.tools.term_match import match_term

_INTEGRITY = Question("log_integrity", "tamper-evident log",
                      (("tamper*", "integrity"), ("log*",)), DENIALS)


def _doc(text: str, name: str = "tech_doc.txt", score: float = 0.5) -> dict:
    return {"text": text, "source_uri": f"minio://bucket/customer_uploads/{name}", "score": score}


def test_a_declared_gap_is_not_evidence_of_the_capability() -> None:
    """ "A tamper-evident log does not yet exist" must not fill log_integrity_controls."""
    passage = _doc("Declared gap: a unified, tamper-evident decision log\n"
                   "does not yet exist.")
    assert ground([passage], _INTEGRITY) is None


def test_the_same_capability_stated_plainly_is_quoted_with_its_source() -> None:
    evidence = ground([_doc("Logs are written to append-only, tamper-evident storage.")],
                      _INTEGRITY)
    assert evidence is not None
    assert evidence.quote == "Logs are written to append-only, tamper-evident storage."
    assert evidence.document == "tech_doc.txt"
    assert evidence.cite().startswith("Provider statement (tech_doc.txt):")


def test_every_term_group_must_be_present() -> None:
    assert ground([_doc("Integrity of the payment ledger is reviewed yearly.")], _INTEGRITY) is None


def test_a_gap_question_finds_the_gap() -> None:
    gap = Question("logging_gap", "gap", (NEGATIONS, ("log", "logging")))
    evidence = ground([_doc("Declared gap: a unified, tamper-evident decision log (which\n"
                            "records were shown) does not yet exist.")], gap)
    assert evidence is not None and evidence.quote.endswith("does not yet exist.")


def test_a_wrapped_line_is_rejoined_but_not_across_table_rows() -> None:
    """One continuation line only: three lines would give the complaints row a Live status."""
    table = ("Exceptions and faults Error monitoring tool Continuous Error rate above 2% of Live\n"
             "calls\n"
             "User complaints and Help desk Continuous Any complaint raising Partial")
    operating = Question("complaints_operating", "q", (("complaint*",), ("live",)), DENIALS)
    assert ground([_doc(table)], operating) is None


def test_nothing_is_joined_across_a_full_stop() -> None:
    joined = units("Retention rules are defined for server logs; 30-day account deletion.")
    retention = Question("log_retention", "q", (("retention",), ("log*",), PERIODS), DENIALS)
    assert not any("30-day" in u and "logs" in u for u in joined)
    assert ground([_doc("Retention rules are defined for server logs; 30-day account deletion.")],
                  retention) is None


def test_an_article_reference_does_not_end_the_sentence() -> None:
    assert units("Serious incidents are reported under Art. 73 within the deadline.") == [
        "Serious incidents are reported under Art. 73 within the deadline."]


def test_a_short_heading_is_not_a_statement() -> None:
    acquisition = Question("acquisition", "q", (("collected",), ("data",)), DENIALS)
    assert ground([_doc("2. DATA COLLECTED\n\n")], acquisition) is None


def test_a_limit_quotes_distinct_rows_in_document_order() -> None:
    rows = _doc("Customer profiles Self-supplied at sign-up 8,100 records\n"
                "Order records Supplied by partners 2,040 records\n"
                "Evaluation set 400 labelled rows")
    evidence = ground([rows], Question("acquisition", "q", (("self-supplied", "supplied"), ("records",)),
                                       DENIALS, limit=3))
    assert evidence is not None
    assert evidence.quote.split(" | ") == [
        "Customer profiles Self-supplied at sign-up 8,100 records",
        "Order records Supplied by partners 2,040 records"]


def test_a_pattern_must_also_match() -> None:
    timeframe = Question("timeframe", "q", (("evaluation set",),), DENIALS, pattern=DATE_RANGE)
    assert ground([_doc("The evaluation set is pseudonymised.")], timeframe) is None
    found = ground([_doc("Evaluation set drawn 2026-01-01 to 2026-08-31.")], timeframe)
    assert found is not None


def test_declared_dossier_fields_are_searched_first_and_cited_as_declared() -> None:
    def search(_engagement: str, _query: str, top_k: int = 8) -> list[dict]:
        assert top_k == 8
        return [_doc("Audit logs are retained for 30 days.")]

    retention = Question("log_retention", "q", (("retain*", "retention"), ("log*",), PERIODS))
    found = gather_evidence("eng-1", [retention],
                            declared={"logging_capabilities": "Logs are retained 10 years."},
                            search=search)
    evidence = found["log_retention"]
    assert evidence is not None and evidence.quote == "Logs are retained 10 years."
    assert evidence.cite().startswith("Provider statement (Annex IV dossier, logging_capabilities)")


def test_no_engagement_means_no_document_search() -> None:
    def search(*_args, **_kwargs) -> list[dict]:
        raise AssertionError("searched without an ingested collection")

    found = gather_evidence("", [_INTEGRITY], declared=None, search=search)
    assert found == {"log_integrity": None}


def test_term_match_leading_wildcard_reaches_into_a_compound() -> None:
    assert match_term("*dimensional", "128-dimensional vectors") == "128-dimensional"
    assert match_term("dimensional", "128-dimensional vectors") is None
    assert match_term("*-day", "a 30-day grace period") == "30-day"
    assert match_term("recruit*", "recruiters") == "recruiters"


def test_a_stored_upload_is_cited_by_its_own_file_name() -> None:
    from aaa.tools.document_evidence.select import document_name

    assert document_name("minio://eng/customer_uploads/post_market_plan_uri_1a2b3c4d_pmm.txt") == "pmm.txt"
    assert document_name("minio://bucket/customer_uploads/tech_doc.txt") == "tech_doc.txt"


def test_a_flattened_pdf_table_is_not_a_statement() -> None:
    """PDF extraction joins a table into one run; a tool and a status from different rows."""
    blob = ("Monitored signals Signal Source Frequency Threshold Status Feature drift profile "
            + "and Live traffic Daily Population stability Planned request mix index "
            * 6 + "Latency p95 Service telemetry Continuous Above 900 ms Live")
    drift = Question("drift_operating", "q", (("population stability",), ("live",)), DENIALS)
    assert ground([_doc(blob, "pmm.pdf")], drift) is None
