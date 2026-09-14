"""Shared minimal completed-but-HITL state for the deferred-HITL tests."""
from __future__ import annotations


def _critiques() -> dict:
    """Verifier critiques: T06 + T09 escalated, T08 + T14 admitted."""
    return {
        "T06_datasheet_for_datasets": {
            "verdict": "escalate_hitl",
            "issues": ["num_instances contradicts instances_type"],
            "article_citations": ["Art.10"],
            "scores": {"factual_accuracy": 1, "evidence_linkage": 2},
            "total_score": 7,
        },
        "T08_special_category_data_log": {
            "verdict": "accept_with_notes", "issues": [],
            "article_citations": ["Art.10"],
        },
        "T09_model_card": {
            "verdict": "escalate_hitl",
            "issues": ["performance fields empty"],
            "article_citations": ["Art.13", "Art.15"],
            "scores": {"factual_accuracy": 1},
            "total_score": 6,
        },
        "T14_governance_findings": {
            "verdict": "accept_with_notes", "issues": [],
            "article_citations": ["Art.9", "Art.17"],
        },
    }


_TEMPLATES = ("T06_datasheet_for_datasets", "T08_special_category_data_log",
              "T09_model_card", "T14_governance_findings")
_URIS = ("minio://e/p2/T06.json", "minio://e/p2/T08.json",
         "minio://e/p3/T09.json", "minio://e/p5/T14.json")


def hitl_state() -> dict:
    """Minimal completed-but-HITL state: T06 + T09 escalated, others admitted."""
    return {
        "engagement_id": "eng-test",
        "risk_tier": "high",
        "is_llm_or_agentic": False,
        "intake_completeness_score": 1.0,
        "client_submission": {"stage_a": {"provider_name": "Acme", "system_name": "X"}},
        "declared_annex_iii_sections": ["5"],
        "phase_status": {tid: "M" for tid in _TEMPLATES},
        "phase_artefacts": {tid: {"uri": uri} for tid, uri in zip(_TEMPLATES, _URIS)},
        "verifier_critiques": _critiques(),
        "article_evidence": {"Art.10": {"evidence_uris": ["minio://e/p2/T06.json"]},
                             "Art.13": {"evidence_uris": ["minio://e/p3/T09.json"]}},
        "compliance_matrix": {},
        "insufficient_evidence_articles": [],
        "blocking_findings": [],
        "hitl_required": True,
        "hitl_reason": "Phase 3 ModelValidator escalate_hitl",
    }
