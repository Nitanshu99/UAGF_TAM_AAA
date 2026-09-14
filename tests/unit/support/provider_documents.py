"""Provider-document evidence shared by the artefact-grounding tests (T-20260913-100)."""
from __future__ import annotations

from typing import Any

from aaa.tools.cgsa_ingest.logger import IngestResult
from aaa.tools.document_evidence import DOSSIER, Evidence

NOW = "2026-09-13T00:00:00Z"
#: A CGSA payload with no domains, typed as the ingest result the builders take.
CGSA = IngestResult(payload={"domains": []}, state_delta={})
DOSSIER_B = {"monitoring_measures": "Plan PMM-7 defines nine signals.",
             "logging_capabilities": "Each request and decision is written to an audit trail.",
             "post_market_plan_uri": "minio://e/pmm.txt", "harmonised_standards": []}


def ev(quote: str, name: str = "post_market_monitoring_plan.txt") -> Evidence:
    """Evidence quoted from an uploaded document, or from a declared field (DOSSIER prefix)."""
    uri = name if name.startswith(DOSSIER) else f"minio://e/customer_uploads/{name}"
    return Evidence(quote, uri, uri.rsplit("/", 1)[-1])


def provider_found() -> dict[str, Any]:
    """Grounded answers a provider's documents give the T15 questions (synthetic)."""
    return {
        "metrics_operating": ev("Request latency from application metrics, alert above 900 ms: Live"),
        "errors_operating": ev("Exceptions tracked by error monitoring: Live"),
        "drift": ev("Feature drift — population stability index, weekly: planned"),
        "drift_absent": ev("No drift detection is in place yet.", "model_card.md"),
        "automatic_logging": ev("Each request and decision is written to an audit trail.",
                                 f"{DOSSIER}logging_capabilities"),
        "log_retention": ev("Retention: application logs 45 days;", "technical_documentation.txt"),
        "incident_reporting": ev("Report — serious incidents to the authority under Art. 73;"),
        "monitoring_gap": ev("Several planned signals are not yet built.",
                              f"{DOSSIER}monitoring_measures"),
        "logging_gap": ev("A signed decision log does not yet exist.",
                           "technical_documentation.txt"),
    }
