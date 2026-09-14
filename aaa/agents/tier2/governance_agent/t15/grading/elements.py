"""The essential elements of a post-market monitoring system, and how documents name them.

Art. 72(1)–(2) require a system that actively and systematically collects, documents
and analyses data on the AI system's performance throughout its lifetime, allows
continuous evaluation against Chapter III Section 2 (Art. 10 bias and Art. 15
accuracy among them), and draws on data provided by deployers or other sources;
Art. 73 adds serious-incident reporting. Each element is asked as named, as
operating, and as absent, so the grade rests on what the provider's own documents say.
"""
from __future__ import annotations

from aaa.agents.tier2.governance_agent.t15.tools import ABSENT, OPERATING
from aaa.tools.document_evidence import DENIALS, Question

#: Element key, retrieval query, and the term groups that name it (every group must match).
ELEMENTS: tuple[tuple[str, str, tuple[tuple[str, ...], ...]], ...] = (
    ("accuracy", "accuracy performance monitoring in production",
     (("accuracy", "precision@*", "ndcg*", "auc*", "f1", "model performance",
       "performance degradation", "false negative rate", "false positive rate", "wape", "mase",
       "rmse"),)),
    ("fairness", "fairness non-discrimination monitoring in production",
     (("fairness", "non-discrimination", "disparate impact", "demographic parity",
       "bias monitor*"),)),
    ("field_data", "deployer feedback complaints user reports",
     (("deployer feedback", "deployer report*", "feedback from deployers", "from deployer*",
       "per deployer", "deployer site*", "complaint*", "contestation*", "support channel",
       "user feedback"),)),
    ("incidents", "serious incident response reporting process runbook",
     (("incident*",), ("report*", "respons*", "criteria", "trigger*", "notif*", "runbook",
                       "procedure", "process", "escalat*"))),
)

#: How an element reads in a rationale.
ELEMENT_NAMES = {
    "performance": "performance monitoring (accuracy or drift, Art. 72(1), Art. 15)",
    "fairness": "non-discrimination monitoring (Art. 72(2), Art. 10(2)(f))",
    "field_data": "data from deployers and affected persons (Art. 72(2))",
    "incidents": "serious-incident reporting process (Art. 73)",
}


def element_questions() -> tuple[Question, ...]:
    """Each element asked as named, as operating, and as absent."""
    asked: list[Question] = []
    for key, query, groups in ELEMENTS:
        asked += [Question(key, query, groups, DENIALS),
                  Question(f"{key}_operating", f"{query} operating live", (*groups, OPERATING),
                           DENIALS),
                  Question(f"{key}_absent", f"no {query} in place", (groups[0], ABSENT))]
    return tuple(asked)


__all__ = ["ELEMENTS", "ELEMENT_NAMES", "element_questions"]
