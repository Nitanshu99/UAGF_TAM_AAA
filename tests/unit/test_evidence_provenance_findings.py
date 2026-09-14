"""findings.collect_evidence_uris / backfill_finding_evidence helpers."""
from __future__ import annotations

from aaa.tools.findings import backfill_finding_evidence, collect_evidence_uris, make_finding


def test_collect_evidence_uris_dedups_and_reads_hit_dicts():
    pool = collect_evidence_uris(
        ["ev://intake"],
        [{"source_uri": "minio://a"}, {"locator": "euaiact://Art.9"}],
        ["minio://a", "minio://b"],
    )
    assert pool == ["ev://intake", "minio://a", "euaiact://Art.9", "minio://b"]


def test_backfill_fills_empty_but_keeps_specific():
    empty = make_finding(
        finding_id="A", description="d", materiality="possibly_material",
        articles=["Art.10"], source_phase="P2",
    )
    specific = make_finding(
        finding_id="B", description="d", materiality="material",
        articles=["Art.15"], source_phase="P3", evidence_uris=["minio://specific"],
    )
    backfill_finding_evidence([empty, specific], ["minio://pool"])
    assert empty["evidence_uris"] == ["minio://pool"]
    assert specific["evidence_uris"] == ["minio://specific"]
