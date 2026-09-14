"""Part 3 of the former ``findings`` module (auto-split)."""
from __future__ import annotations

import re
from typing import Any, Iterable

from aaa.tools.findings.make_positive_finding import (  # noqa: F401
    collect_evidence_uris,
    make_positive_finding,
)
from aaa.tools.findings.materiality import (  # noqa: F401
    BLOCKING_MATERIALITY,
    Materiality,
    make_finding,
)


def backfill_finding_evidence(
    findings: Iterable[dict[str, Any]], evidence_uris: list[str]
) -> None:
    """Fill any finding lacking ``evidence_uris`` with the engagement evidence pool.

    Mutates in place. Findings that already cite specific evidence (e.g. a model
    artefact URI) are left untouched, so claim-specific provenance is preserved.
    """
    for finding in findings:
        if isinstance(finding, dict) and not finding.get("evidence_uris"):
            finding["evidence_uris"] = list(evidence_uris)


def is_blocking(finding: dict[str, Any]) -> bool:
    """True if the finding's materiality should force a FAIL on its articles."""
    return finding.get("materiality") == BLOCKING_MATERIALITY


#: ``Article 9`` / ``Annex III`` as the CGSA schema spells them, against
#: ``Art.9`` / ``Annex_III`` as ``ARTICLE_SET`` spells them.
_ARTICLE_RE = re.compile(r"^\s*Article\s+(\d+)\s*(§\s*\d+.*)?$", re.IGNORECASE)
_ANNEX_RE = re.compile(r"^\s*Annex\s+([IVXLC]+)\s*$", re.IGNORECASE)


def normalise_article(ref: Any) -> str:
    """Render an article reference in the spelling ``ARTICLE_SET`` uses.

    The CGSA schema requires ``eu_ai_act_article`` and spells its values
    ``"Article 9"``; every internal article set spells the same obligation
    ``"Art.9"``. Left untranslated, a CGSA blocking finding indexes under a key
    no article row ever looks up, so an explicitly non-compliant governance
    assessment yields "no findings raised" on the articles it fails.

    :param ref: An article reference in either spelling.
    :returns: The internal spelling, or the input stripped when unrecognised.
    :rtype: str
    """
    text = str(ref).strip()
    article = _ARTICLE_RE.match(text)
    if article:
        return f"Art.{article.group(1)}{(article.group(2) or '').replace(' ', '')}"
    annex = _ANNEX_RE.match(text)
    if annex:
        return f"Annex_{annex.group(1).upper()}"
    return text


def articles_for(finding: dict[str, Any]) -> list[str]:
    """Return the EU AI Act articles a finding maps to (tolerant of legacy shapes)."""
    arts = finding.get("eu_ai_act_articles")
    if not arts:
        # The CGSA hand-off names it in the singular — its schema requires
        # ``eu_ai_act_article`` on every blocking finding and roadmap entry.
        single = finding.get("eu_ai_act_article") or finding.get("article")
        arts = [single] if single else []
    return [normalise_article(a) for a in arts if a]


__all__ = [
    "Materiality",
    "make_finding",
    "make_positive_finding",
    "collect_evidence_uris",
    "backfill_finding_evidence",
    "is_blocking",
    "articles_for",
    "normalise_article",
]
