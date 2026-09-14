"""The markup of the four dashboard statistics.

A statistic the audit did not produce is shown as a dash with the reason, never
as a number. A minimal-risk system bound by no article has no conformity score
and no requirements to meet: ``0/100`` and ``0/0`` there read as a system that
met none of its obligations (T-094). An intake score that was never computed is
likewise "not measured", not ``0%``.
"""
from __future__ import annotations

from aaa.ui.styles import stat_tile
from aaa.ui.wizard.step4.header import article_score

_DASH = "—"


def _tone(fraction: float) -> str:
    """Bar colour for a 0–1 proportion, worst below two thirds."""
    return "is-ok" if fraction >= 0.95 else "is-warn" if fraction >= 0.66 else "is-bad"


def _score_tiles(final: dict, counts: dict[str, int]) -> list[str]:
    """The conformity-score and requirements-met tiles."""
    score = article_score(final.get("compliance_matrix") or {})
    if score is None or not counts["total"]:
        return [stat_tile("Conformity score", _DASH, "",
                          "No EU AI Act article applies to your system.", None, "", 0),
                stat_tile("Requirements met", _DASH, "",
                          "None apply at your system's risk tier.", None, "", 1)]
    met = counts["met"] / counts["total"]
    return [stat_tile("Conformity score", f"{score:.0f}", "/100",
                      "Weighted across every article that applies to you.",
                      score / 100.0, _tone(score / 100.0), 0),
            stat_tile("Requirements met", str(counts["met"]), f"/{counts['total']}",
                      f"{counts['unknown']} could not be checked."
                      if counts["unknown"] else "Assessed against your documents.",
                      met, _tone(met), 1)]


def _docs_tile(final: dict) -> str:
    """The documentation-supplied tile; an uncomputed intake score is not zero."""
    docs = final.get("intake_completeness_score")
    if docs is None:
        return stat_tile("Documentation supplied", _DASH, "",
                         "Not measured for this engagement.", None, "", 3)
    return stat_tile("Documentation supplied", f"{float(docs) * 100:.0f}", "%",
                     "How complete your Annex IV dossier was.",
                     float(docs), _tone(float(docs)), 3)


def kpi_tiles(final: dict, counts: dict[str, int]) -> list[str]:
    """Return the markup for the four dashboard statistics, in order.

    :param final: Final ``AuditState`` dictionary.
    :param counts: :func:`aaa.ui.wizard.step4.kpis.matrix_counts` of its matrix.
    :returns: Four tile markups.
    """
    open_items = counts["unmet"] + counts["attention"]
    return [*_score_tiles(final, counts),
            stat_tile("Needs your attention", str(open_items), "",
                      f"{counts['unmet']} not met · {counts['attention']} with observations",
                      None, "", 2),
            _docs_tile(final)]
