"""
IntakeValidator — Stage 0 A/B/C Orchestrator (§6 Stage 0).

Owns the three mandatory pre-audit sub-stages:

  0A · Stage A — Triage
       Validates the ~20-question triage form via triage_render.
       Runs art43_select in *preview* mode → writes art43_preview to T01a.
       Writes T01a to the Evidence Store.

  0B · Stage B — Annex IV Dossier Upload
       Validates the dossier via annex_iv_validator.
       Runs intake_completeness_calculator.
       Writes T01b + T01c to the Evidence Store.
       Gate: intake_completeness_score >= 0.80 required to proceed.

  0C · Stage C — Scoped Access (optional)
       Stores only the credential reference (never the secret itself).
       Absent in offline/demo mode → marks live-system evidence as
       "not_verifiable" in the declaration_verification map.

Returns the fully-populated AuditState ready for Phase 1.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from src.agents.base import BaseAgent, IntakeDispatch
from src.platform.state import (
    AuditState,
    ClientSubmission,
    StageATriage,
    AnnexIVDossier,
    StageCAccess,
    Art43Decision,
)
from src.platform.evidence import EvidenceStore
from src.tools.triage_render import triage_render
from src.tools.annex_iv_validator import annex_iv_validator
from src.tools.intake_completeness_calculator import intake_completeness_calculator
from src.tools.art43_select import art43_select_from_state

# Threshold defined in §9.1 and §6.2 constraint 7.
COMPLETENESS_GATE = 0.80


class IntakeValidatorError(Exception):
    """Raised when a Stage 0 gate blocks further processing."""
    def __init__(self, stage: str, reason: str, details: dict[str, Any] | None = None):
        self.stage = stage
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[Stage {stage}] {reason}")


class IntakeValidator(BaseAgent):
    """
    Orchestrates Stage 0 A / B / C.

    The Orchestrator instantiates this agent once at the start of each
    engagement and calls `process(message)` with an IntakeDispatch.
    """

    def __init__(self, evidence_store: EvidenceStore, model: str = "claude-3-haiku-20240307"):
        super().__init__(name="IntakeValidator", model=model)
        self.store = evidence_store

    async def process(self, message: IntakeDispatch) -> AuditState:  # type: ignore[override]
        """
        Run Stage 0 A/B/C and return a populated AuditState.

        Args:
            message: IntakeDispatch from the Orchestrator.

        Returns:
            AuditState with client_submission, intake_completeness_score,
            declared_* fields, and phase_artefacts for T01a/T01b/T01c.

        Raises:
            IntakeValidatorError on any gate failure.
        """
        engagement_id = message["engagement_id"]

        # ── Stage A ──────────────────────────────────────────────────────────
        stage_a_payload: dict[str, Any] = self._load(message["stage_a_uri"])
        triage_result = triage_render(stage_a_payload)
        if not triage_result.is_valid:
            raise IntakeValidatorError(
                stage="A",
                reason="Triage form failed schema validation.",
                details={"schema_errors": triage_result.schema_errors},
            )

        # Compute preview Art. 43 decision from declared values.
        art43_preview = self._preview_art43(stage_a_payload)
        art43_preview_procedure = art43_preview["procedure"]
        stage_a_payload["art43_preview"] = art43_preview_procedure
        triage_result.rendered["art43_preview"] = art43_preview_procedure  # type: ignore[index]

        t01a_uri = self.store.store_artefact(
            engagement_id=engagement_id,
            phase="stage_a",
            artefact_type="T01a_stage_a_triage",
            content=triage_result.rendered,
            agent_name=self.name,
        )

        # ── Stage B ──────────────────────────────────────────────────────────
        stage_b_payload: dict[str, Any] = self._load(message["stage_b_uri"])
        declared_modality: str = stage_a_payload["declared_modality"]

        validation = annex_iv_validator(stage_b_payload, declared_modality)
        if not validation.is_valid:
            raise IntakeValidatorError(
                stage="B",
                reason="Annex IV dossier failed schema/conditional validation.",
                details=validation.to_dict(),
            )

        t01b_uri = self.store.store_artefact(
            engagement_id=engagement_id,
            phase="stage_b",
            artefact_type="T01b_annex_iv_dossier",
            content=stage_b_payload,
            agent_name=self.name,
        )

        # Build ClientSubmission for the calculator.
        submission: ClientSubmission = {
            "stage_a": stage_a_payload,  # type: ignore[typeddict-item]
            "stage_b": stage_b_payload,  # type: ignore[typeddict-item]
            "stage_c": None,
            "intake_completeness_score": 0.0,
        }

        completeness_report = intake_completeness_calculator(
            submission=submission,
            declared_modality=declared_modality,
            engagement_id=engagement_id,
        )
        submission["intake_completeness_score"] = completeness_report.score

        t01c_content = {
            **completeness_report.to_dict(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "art43_preview_procedure": art43_preview_procedure,
            "art43_final_procedure": None,
            "art43_delta": None,
        }
        t01c_uri = self.store.store_artefact(
            engagement_id=engagement_id,
            phase="stage_b",
            artefact_type="T01c_intake_completeness_report",
            content=t01c_content,
            agent_name=self.name,
        )

        if not completeness_report.gate_passed:
            raise IntakeValidatorError(
                stage="B",
                reason=(
                    f"intake_completeness_score={completeness_report.score:.2f} "
                    f"< {COMPLETENESS_GATE}. Remediate the listed fields before Phase 1 can start."
                ),
                details=completeness_report.to_dict(),
            )

        # ── Stage C (optional) ────────────────────────────────────────────────
        stage_c_payload: dict[str, Any] | None = None
        if message.get("stage_c_uri"):
            stage_c_payload = self._load(message["stage_c_uri"])
            submission["stage_c"] = stage_c_payload  # type: ignore[typeddict-item]

        # ── Assemble initial AuditState ───────────────────────────────────────
        state: AuditState = {
            "engagement_id": engagement_id,
            "client_submission": submission,
            "declared_modality": declared_modality,
            "declared_risk_tier": stage_a_payload["declared_risk_tier"],
            "declared_annex_iii_sections": stage_a_payload.get("declared_annex_iii_sections", []),
            # Verified values — will be populated by Phase 1.
            "risk_tier": stage_a_payload["declared_risk_tier"],  # type: ignore[typeddict-item]
            "annex_iii_mapping": [],
            "modality": declared_modality,  # type: ignore[typeddict-item]
            "deployment_context": stage_a_payload["deployment_context"],  # type: ignore[typeddict-item]
            "is_llm_or_agentic": declared_modality in {"llm", "agentic", "gpai"},
            "provider_elects_third_party": stage_a_payload.get("provider_elects_third_party", False),
            "harmonised_standards_applied": False,
            "declaration_verification": {},
            "art43_decision": None,
            "phase_artefacts": {
                "T01a_stage_a_triage": {"uri": t01a_uri, "sha256": "", "template_id": "T01a_stage_a_triage"},
                "T01b_annex_iv_dossier": {"uri": t01b_uri, "sha256": "", "template_id": "T01b_annex_iv_dossier"},
                "T01c_intake_completeness_report": {"uri": t01c_uri, "sha256": "", "template_id": "T01c_intake_completeness_report"},
            },
            "cgsa_payload": None,
            "cgsa_schema_version": None,
            "cgsa_composite_maturity_score": None,
            "cgsa_composite_maturity_label": None,
            "cgsa_eu_ai_act_coverage_pct": None,
            "cgsa_csp_satisfiable": None,
            "cgsa_governance_verdict": None,
            "cgsa_phase5_verdict": None,
            "cgsa_phase5_narrative": None,
            "cgsa_blocking_findings": [],
            "cgsa_positive_findings": [],
            "cgsa_low_confidence_controls": [],
            "cgsa_recommended_follow_up": [],
            "cgsa_report_url": None,
            "cgsa_risk_tier_match": None,
            "compliance_matrix": {},
            "blocking_findings": [],
            "positive_findings": [],
            "remediation_roadmap": [],
            "verifier_critiques": {},
            "intake_completeness_score": completeness_report.score,
            "completeness_score": None,
            "regulatory_coverage_pct": None,
            "final_verdict": None,
        }

        # Mark live-system evidence as not_verifiable if Stage C absent.
        if stage_c_payload is None:
            state["declaration_verification"]["live_system_access"] = "not_verifiable"

        return state

    # ── helpers ───────────────────────────────────────────────────────────────

    def _load(self, uri: str) -> dict[str, Any]:
        """Load an artefact from the Evidence Store by URI (or treat as raw dict)."""
        if uri.startswith("minio://"):
            content = self.store.get_artefact(uri)
            if content is None:
                raise IntakeValidatorError("A/B/C", f"Artefact not found: {uri}")
            return content  # type: ignore[return-value]
        # Convenience for tests: treat non-URI as passthrough (already a dict).
        raise ValueError(f"Unsupported URI scheme: {uri!r}")

    def _preview_art43(self, stage_a: dict[str, Any]) -> Art43Decision:
        """Compute the preview Art. 43 decision from declared Stage A values."""
        pseudo_state = {
            "declared_risk_tier": stage_a.get("declared_risk_tier", "minimal"),
            "declared_annex_iii_sections": stage_a.get("declared_annex_iii_sections", []),
            "provider_elects_third_party": stage_a.get("provider_elects_third_party", False),
            "risk_tier": stage_a.get("declared_risk_tier", "minimal"),
            "annex_iii_mapping": [],
            "harmonised_standards_applied": False,
        }
        return art43_select_from_state(pseudo_state, use_declared=True)
