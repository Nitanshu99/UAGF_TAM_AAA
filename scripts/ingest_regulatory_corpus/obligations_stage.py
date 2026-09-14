"""Embed-and-upsert stage for obligation questions (Step 6)."""
from __future__ import annotations

from typing import Any

from scripts.ingest_regulatory_corpus.checker import CheckerLookup
from scripts.ingest_regulatory_corpus.collections import ensure_obligations_collection
from scripts.ingest_regulatory_corpus.console import ok
from scripts.ingest_regulatory_corpus.embed import dense_embed
from scripts.ingest_regulatory_corpus.existing import fetch_existing_ids, filter_new_questions
from scripts.ingest_regulatory_corpus.upsert import upsert_obligation_questions


def ingest_obligations(args: Any, client: Any, checker: CheckerLookup) -> None:
    """Embed and upsert obligation questions, skipping already-present ones.

    :param args: Parsed CLI namespace.
    :param client: Qdrant client.
    :param checker: Compliance-checker lookup with the question records.
    """
    ensure_obligations_collection(client, args.obligations_collection, reset=args.reset)
    if args.force_reembed:
        new_questions = checker.questions
    else:
        existing_q_ids = fetch_existing_ids(client, args.obligations_collection)
        new_questions = filter_new_questions(checker.questions, existing_q_ids)
        if len(new_questions) < len(checker.questions):
            ok(f"skip {len(checker.questions) - len(new_questions)} obligation "
               "questions already in Qdrant")
    q_dense: list[list[float]] = []
    if new_questions:
        q_texts = [f"{q['question_id']} ({q['source']}): {q['text']}"
                   for q in new_questions]
        q_dense = dense_embed(q_texts)
    n_q = upsert_obligation_questions(client, args.obligations_collection,
                                      new_questions, q_dense)
    ok(f"upserted {n_q} obligation-question points into '{args.obligations_collection}'")
