"""Building the compliance-checker lookup from the JSON file."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.ingest_regulatory_corpus.checker import CheckerLookup
from scripts.ingest_regulatory_corpus.checker.questions import index_sections
from scripts.ingest_regulatory_corpus.config import DEFAULT_CHECKER_PATH, REPO_ROOT
from scripts.ingest_regulatory_corpus.refs import parse_refs


def build_checker_lookup(path: Path) -> CheckerLookup:
    """Parse the compliance-checker JSON into the article→obligations index.

    :param path: Path (possibly relative) to the checker JSON.
    :returns: Populated :class:`CheckerLookup`.
    :raises FileNotFoundError: When no candidate checker path exists.
    """
    candidate_paths = [path]
    if not path.is_absolute():
        candidate_paths.append(REPO_ROOT / path)
    if path.name == DEFAULT_CHECKER_PATH.name:
        candidate_paths.append(DEFAULT_CHECKER_PATH)
    checker_path = next((p for p in candidate_paths if p.exists()), None)
    if checker_path is None:
        tried = ", ".join(str(p) for p in dict.fromkeys(candidate_paths))
        raise FileNotFoundError(
            f"checker JSON not found; tried: {tried}. "
            f"Use '{DEFAULT_CHECKER_PATH.relative_to(REPO_ROOT)}'.")

    raw = json.loads(checker_path.read_text(encoding="utf-8"))
    by_article: dict[str, dict[str, set[str]]] = {}
    questions = index_sections(raw, by_article)

    # Fold the top-level "obligations" catalogue into the per-article index too.
    catalogue = raw.get("obligations", {}) or {}
    for name, meta in catalogue.items():
        for ref in parse_refs(meta.get("source")):
            bucket = by_article.setdefault(
                ref, {"obligations": set(), "entity_types": set(), "risk_classes": set()})
            bucket["obligations"].add(name)
            for ent in meta.get("applies_to", []) or []:
                bucket["entity_types"].add(ent)

    return CheckerLookup(
        by_article={ref: {k: sorted(v) for k, v in payload.items()}
                    for ref, payload in by_article.items()},
        obligations_catalogue=catalogue,
        questions=questions,
    )
