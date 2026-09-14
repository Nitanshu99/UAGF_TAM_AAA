"""The monitoring tools T15 asks the provider's documents about.

A monitoring plan names signals. Most plans describe monitoring that runs; some say
of themselves that they are a specification, with most signals still to be built. So each tool is asked twice: named at all, and named as operating. Where
the provider declares its monitoring unbuilt (``monitoring_gap``), only the
operating answers count (:mod:`.evidence`). A sentence that denies a tool is
never evidence for it, and "No drift detection … is in place" is evidence against.
"""
from __future__ import annotations

from aaa.tools.document_evidence import DENIALS, NEGATIONS, Question

OPERATING = ("live", "operating", "in place", "captured by", "in production", "running",
              "enabled", "active", "deployed", "automated")
#: Denial words for a tool's absence; "not" alone is too loose ("weekly, not monthly").
ABSENT = ("no",) + NEGATIONS

#: Each monitoring tool: key, retrieval query, the terms that name it.
TOOLS = (
    ("metrics", "performance metrics latency monitoring KPI",
     ("latency", "application metrics", "performance metric*", "performance degradation",
      "key performance indicator*", "kpi*")),
    ("errors", "error monitoring alerting error rate",
     ("error monitoring", "error-monitoring", "errors and exceptions", "error rate",
      "error-rate")),
    # "drift" alone names a risk as readily as a control ("R-002 Distribution shift …").
    ("drift", "drift detection distribution shift monitoring",
     ("drift monitor*", "drift detection", "shift detection", "population stability", "psi",
      "drift test*", "drift alert*")),
    ("complaints", "complaints contestations support channel",
     ("complaint*", "contestation*", "support channel")),
    ("dashboards", "monitoring dashboard", ("dashboard*",)),
)


def tool_questions() -> tuple[Question, ...]:
    """Each tool asked as named, and as operating, plus the drift denial."""
    asked: list[Question] = []
    for key, query, names in TOOLS:
        asked.append(Question(key, query, (names,), DENIALS))
        asked.append(Question(f"{key}_operating", f"{query} operating live", (names, OPERATING),
                              DENIALS))
    asked.append(Question("drift_absent", "no drift detection in place", (("drift",), ABSENT)))
    return tuple(asked)


#: How T15 names each tool in ``monitoring_tools``.
TOOL_NAMES = {"metrics": "performance metrics", "errors": "error monitoring",
              "drift": "drift monitoring", "complaints": "complaints and contestations channel",
              "dashboards": "monitoring dashboards"}

__all__ = ["ABSENT", "OPERATING", "TOOLS", "TOOL_NAMES", "tool_questions"]
