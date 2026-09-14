"""Question indexing for the compliance-checker lookup."""
from __future__ import annotations

from typing import Any

from scripts.ingest_regulatory_corpus.refs import parse_refs, walk_answer


def index_sections(
    raw: dict[str, Any],
    by_article: dict[str, dict[str, set[str]]],
) -> list[dict[str, Any]]:
    """Index every questionnaire section into *by_article*; return the questions.

    :param raw: Parsed checker JSON.
    :param by_article: ref → enrichment sets, mutated in place.
    :returns: Flat question records for the obligations_index collection.
    """
    questions: list[dict[str, Any]] = []
    for section in raw.get("sections", []):
        section_id = section.get("id", "")
        section_title = section.get("title", "")
        for q in section.get("questions", []):
            q_refs = parse_refs(q.get("source"))
            q_obligations: set[str] = set()
            q_entities: set[str] = set()
            q_status: set[str] = set()
            for ans in q.get("answers", []):
                o, e, s = walk_answer(ans)
                q_obligations |= o
                q_entities |= e
                q_status |= s
            for ref in q_refs:
                bucket = by_article.setdefault(
                    ref, {"obligations": set(), "entity_types": set(), "risk_classes": set()})
                bucket["obligations"] |= q_obligations
                bucket["entity_types"] |= q_entities
                bucket["risk_classes"] |= q_status
            questions.append({
                "section_id": section_id,
                "section_title": section_title,
                "question_id": q.get("id", ""),
                "text": q.get("text", ""),
                "hint": q.get("hint", ""),
                "source": q.get("source", ""),
                "refs": q_refs,
                "obligations": sorted(q_obligations),
                "entity_types": sorted(q_entities),
                "risk_classes": sorted(q_status),
            })
    return questions
