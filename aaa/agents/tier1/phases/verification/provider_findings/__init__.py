"""Option A, matrix side: what an admitted artefact records about the provider reaches the verdict.

The Verifier no longer rejects an artefact for accurately recording a gap in the
provider's evidence or a provider non-conformity (T-20260914-015). Those issues must
still decide the article, or an admitted T06 stating that nothing about data
collection was documented would let Art. 10 read PASS (T-20260914-016). Like the
unadmitted gate, this rewrites — never appends to — the phase's own records, so a
re-dispatch that clears an issue also releases what it held.
"""
from __future__ import annotations

from aaa.agents.tier1.phases.verification.provider_findings.collect import _collect
from aaa.agents.tier1.phases.verification.provider_findings.graded import Load
from aaa.agents.tier1.phases.verification.unadmitted.release import _release


def record_provider_findings(state: dict, tid_articles: dict[str, list[str]], *,
                             phase_id: str, phase_label: str, load: Load | None = None) -> None:
    """Rewrite this phase's Verifier provider findings and evidence-gap insufficiencies.

    :param state: The mutable AuditState dict.
    :param tid_articles: Template ids this phase emitted, mapped to their articles.
    :param phase_id: Dispatch phase id (``P2``, ``P5``, …).
    :param phase_label: Human-readable phase label used in the logs.
    :param load: Reads a stored artefact by URI, for templates that grade articles themselves.
    """
    findings, gaps = _collect(state, tid_articles, phase_id, phase_label, load)
    prefix = f"{phase_id or 'P?'}-VER-"
    kept = [f for f in state.get("blocking_findings") or []
            if not str(f.get("finding_id", "")).startswith(prefix)]
    if findings or len(kept) != len(state.get("blocking_findings") or []):
        state["blocking_findings"] = kept + findings
    before = state.get("evidence_gap_records") or []
    mine = [e for e in before if e.get("phase_id") == phase_id and e.get("template_id") in tid_articles]
    if not gaps and not mine:
        return
    entries = [e for e in before if e not in mine] + gaps
    state["evidence_gap_records"] = entries
    recorded: list[str] = state.setdefault("insufficient_evidence_articles", [])
    recorded.extend(a for a in {a for g in gaps for a in g["articles"]} if a not in recorded)
    superseded = {a for e in mine for a in e["articles"]} - {a for g in gaps for a in g["articles"]}
    _release(state, superseded, entries + list(state.get("unadmitted_artefacts") or []))


__all__ = ["record_provider_findings"]
