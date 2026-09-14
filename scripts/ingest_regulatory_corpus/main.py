"""End-to-end ingestion entry point: load → chunk → embed → upsert."""
from __future__ import annotations

from scripts.ingest_regulatory_corpus.checker.build import build_checker_lookup
from scripts.ingest_regulatory_corpus.chunker import chunk_units
from scripts.ingest_regulatory_corpus.cli import parse_args
from scripts.ingest_regulatory_corpus.collections import qdrant_client
from scripts.ingest_regulatory_corpus.console import err, ok, setup_logging, step, warn
from scripts.ingest_regulatory_corpus.corpus_stage import ingest_corpus
from scripts.ingest_regulatory_corpus.obligations_stage import ingest_obligations
from scripts.ingest_regulatory_corpus.probes import run_coverage_probes
from scripts.ingest_regulatory_corpus.stages import load_all_units, summarise
from scripts.ingest_regulatory_corpus.warmup import warm_imports


def main(argv: list[str] | None = None) -> int:
    """Run the full ingestion pipeline.

    :param argv: Optional argument list (defaults to ``sys.argv[1:]``).
    :returns: Process exit code.
    """
    args = parse_args(argv)
    setup_logging(args.verbose)
    total_steps = 6
    warm_imports(args.dry_run)

    step(1, total_steps, "Building compliance-checker lookup")
    checker = build_checker_lookup(args.checker)
    ok(f"indexed {len(checker.by_article)} refs · "
       f"{len(checker.obligations_catalogue)} obligations · "
       f"{len(checker.questions)} questions")

    step(2, total_steps, f"Loading corpus from {args.corpus}")
    units = load_all_units(args.corpus)
    if not units:
        err("no units parsed — aborting")
        return 1

    step(3, total_steps, "Chunking units (per-unit SentenceSplitter)")
    chunks = chunk_units(units, checker,
                         chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    for key, n in sorted(summarise(chunks).items()):
        ok(f"{key:40s} → {n} chunks")
    ok(f"total chunks: {len(chunks)}")

    if args.dry_run:
        warn("--dry-run: skipping embeddings and Qdrant writes")
        return 0

    client = qdrant_client()
    step(4, total_steps, "Computing dense + sparse embeddings (skipping existing)")
    step(5, total_steps, "Upserting corpus chunks into Qdrant")
    ingest_corpus(args, client, chunks)

    if args.skip_obligations:
        warn("--skip-obligations: skipping obligations_index collection")
        return 0

    step(6, total_steps, "Upserting obligations_index from compliance-checker")
    ingest_obligations(args, client, checker)
    run_coverage_probes(client, args.collection)
    return 0
