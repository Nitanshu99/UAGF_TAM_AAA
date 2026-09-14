"""T08 quotes a declared Art. 10(5) reliance and says whether it covers anything (T-20260914-039)."""
from __future__ import annotations

from aaa.agents.tier2.data_auditor.t08 import build_t08
from aaa.agents.tier2.data_auditor.t08.art10_5 import QUESTION
from aaa.tools.document_evidence import gather_evidence
from aaa.tools.template_render.logger import _load_schema, _validate_payload

_FINCLEAR = ("FinClear proprietary credit dataset -- 1000 instances. Age variable retained under "
             "Art. 10 para 5 derogation for fairness monitoring only.")


def _t08(description: str, present: bool = False) -> dict:
    found = gather_evidence("", [QUESTION], declared={"training_data_description": description})
    return build_t08("eng-01", present, {"special_categories_found": []}, False,
                     "2026-09-14T00:00:00Z", found=found)


def test_a_reliance_with_nothing_to_cover_is_recorded_as_not_applying() -> None:
    """Case 01: age is not an Art. 9(1) category, so the derogation invoked covers nothing."""
    t08 = _t08(_FINCLEAR)
    assert t08["art10_5_statistical_correction_applies"] is False
    assert "Age variable retained under Art. 10 para 5" in t08["statistical_correction_rationale"]
    assert "has nothing to apply to" in t08["compliance_narrative"]
    assert not _validate_payload(t08, _load_schema("T08_special_category_data_log"),
                                 "T08_special_category_data_log")


def test_no_declaration_stays_unknown() -> None:
    """Whether Art. 10(5) is relied on is the provider's to declare."""
    t08 = _t08("FinClear proprietary credit dataset -- 1000 instances.")
    assert (t08["art10_5_statistical_correction_applies"],
            t08["statistical_correction_rationale"]) == (None, None)


def test_a_reliance_beside_special_category_data_is_recorded_as_declared() -> None:
    """With special-category data present, the declaration is recorded, not verified."""
    t08 = _t08("Ethnic origin is processed under Article 10(5) for bias detection.", present=True)
    assert t08["art10_5_statistical_correction_applies"] is True
    assert "not verified" in t08["statistical_correction_rationale"]
