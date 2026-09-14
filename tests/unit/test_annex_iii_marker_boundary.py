"""Unit tests for word-boundary keyword matching (fix F14, finding S22)."""
from __future__ import annotations

import pytest

from aaa.tools.annex_iii_classify import _extract_marker, _keyword_score
from aaa.tools.annex_iii_classify.logger import _SECTIONS_1_TO_4
from aaa.tools.annex_iii_classify.sections_5_to_8 import NO_KEYWORD_EVIDENCE, keyword_present

_BIOMETRIC_KEYWORDS = _SECTIONS_1_TO_4["1"]["keywords"]

#: The text that caused it: RetailIQ's grocery demand forecaster, whose
#: documents name a HuggingFace foundation model.
_FORECASTER = ("weekly demand forecasting for grocery and fmcg categories. "
               "deployed a huggingface chronos-t5-tiny foundation model.")


def test_face_does_not_match_inside_huggingface() -> None:
    """The substring hit that filed a grocery forecaster under Biometrics."""
    assert "face" in "huggingface"          # the old test, still true of substrings
    assert not keyword_present("face", "huggingface")


def test_forecaster_scores_zero_for_biometrics() -> None:
    """A demand forecaster has no biometric keyword evidence at all."""
    assert _keyword_score(_BIOMETRIC_KEYWORDS, _FORECASTER) == 0.0


def test_forecaster_marker_is_not_fabricated() -> None:
    """With nothing matching, the marker says so rather than naming a keyword.

    ``use_case_marker`` is contractually the evidence supporting a
    classification; ``keywords[0]`` is a keyword that is not in the document.
    """
    assert _extract_marker(_BIOMETRIC_KEYWORDS, _FORECASTER) == NO_KEYWORD_EVIDENCE


def test_a_genuine_biometric_system_still_matches() -> None:
    """The fix must not cost a true positive."""
    text = "remote biometric identification using facial recognition at border control"
    # The sub-point catalogue (T-20260913-043) lists the specific phrase before the
    # generic word, so the evidence named is the more precise one.
    assert _extract_marker(_BIOMETRIC_KEYWORDS, text) == "remote biometric identification"
    assert _keyword_score(_BIOMETRIC_KEYWORDS, text) > 0.0


@pytest.mark.parametrize("keyword,text,expected", [
    ("credit", "(credit) decisions", True),        # punctuation is a boundary
    ("credit", "credit scoring model", True),      # plain word
    ("credit", "subcredit facility", False),       # prefixed word is not a match
    ("credit", "creditworthiness", False),         # suffixed word is not a match
    ("credit", "credit-scoring", False),           # hyphen binds: this is one token
    ("credit scoring", "credit-scoring model", True),   # …and the phrase matches it
    ("law enforcement", "law/enforcement tooling", True),
    ("law enforcement", "law_enforcement tooling", True),
    ("face", "huggingface", False),                # the finding itself
    ("face", "face recognition", True),
])
def test_boundaries_behave_as_a_reader_expects(keyword, text, expected) -> None:
    """Separators join a phrase; adjacent letters and hyphens do not split a word."""
    assert keyword_present(keyword, text) is expected


def test_multi_word_keywords_match_on_their_own_boundaries() -> None:
    """Phrases like "facial recognition" are matched whole, not per token."""
    assert keyword_present("facial recognition", "uses facial recognition software")
    assert not keyword_present("facial recognition", "facial recognitions")


def test_score_and_marker_use_one_rule() -> None:
    """A section cannot score on a hit whose evidence the marker cannot find."""
    text = "huggingface deployment"
    assert _keyword_score(_BIOMETRIC_KEYWORDS, text) == 0.0
    assert _extract_marker(_BIOMETRIC_KEYWORDS, text) == NO_KEYWORD_EVIDENCE
