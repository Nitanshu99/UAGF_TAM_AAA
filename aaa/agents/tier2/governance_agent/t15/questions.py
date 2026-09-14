"""What T15 asks of the provider's documents (Art. 12, 17 and 72); the tools are in :mod:`.tools`."""
from __future__ import annotations

from aaa.agents.tier2.governance_agent.t15.grading.elements import element_questions
from aaa.agents.tier2.governance_agent.t15.tools import TOOL_NAMES, TOOLS, tool_questions
from aaa.tools.document_evidence import DENIALS, NEGATIONS, PERIODS, Question

T15_QUESTIONS = tool_questions() + element_questions() + (
    Question("automatic_logging", "automatic logging audit trail events recorded",
             # "Per-prediction log", "per-alert log", "per-screening log" record every event.
             (("log*", "audit trail", "recorded", "written"), ("automatic*", "every", "each", "per-*")),
             DENIALS),
    # "Retained 3 years." is its own sentence of the declared logging_capabilities, which is
    # about logs by its name; a document sentence must still name the logs (case 03).
    Question("log_retention", "log retention period days",
             (("retention", "retain*"), PERIODS), DENIALS,
             subject=("log*",), subject_fields=("logging_capabilities",)),
    Question("log_integrity", "tamper-evident log integrity controls",
             (("tamper*", "integrity", "immutable", "append-only", "worm"), ("log*",)), DENIALS),
    Question("incident_reporting", "serious incident reporting Article 73 authority deadline",
             (("incident*",), ("report*",), ("art. 73", "article 73", "authorit*", "deadline"))
             , DENIALS),
    Question("incident_threshold", "serious incident criteria threshold trigger",
             (("serious incident*",), ("threshold*", "criteria", "defined as", "definition",
                                       "trigger*")), DENIALS),
    Question("qms", "quality management system", (("quality management",),), DENIALS),
    Question("monitoring_gap", "monitoring signals not yet built status",
             (NEGATIONS, ("monitor*", "signal*"))),
    Question("logging_gap", "logging gap does not yet exist",
             (NEGATIONS, ("log", "logs", "logging"))),
)

__all__ = ["T15_QUESTIONS", "TOOLS", "TOOL_NAMES"]
