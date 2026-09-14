"""The IntakeValidator class — Stage 0 A/B/C coordinator."""
from __future__ import annotations

from typing import Any

from aaa.agents.base import BaseAgent, IntakeDispatch
from aaa.agents.intake_validator.assemble import assemble_state
from aaa.agents.intake_validator.docs_ingest import ingest_client_docs
from aaa.agents.intake_validator.errors import IntakeValidatorError
from aaa.agents.intake_validator.stage.a import run_stage_a
from aaa.agents.intake_validator.stage.b import run_stage_b
from aaa.platform.evidence import EvidenceStore
from aaa.platform.state import AuditState


class IntakeValidator(BaseAgent):
    """Orchestrates Stage 0 A / B / C.

    The Orchestrator instantiates this agent once at the start of each
    engagement and calls ``process(message)`` with an IntakeDispatch.
    """

    def __init__(self, evidence_store: EvidenceStore, model: str = "claude-3-haiku-20240307"):
        super().__init__(name="IntakeValidator", model=model)
        self.store = evidence_store

    def _load(self, uri: str) -> dict[str, Any]:
        """Load an artefact from the Evidence Store by URI.

        :raises IntakeValidatorError: When the URI cannot be resolved.
        :raises ValueError: For unsupported URI schemes.
        """
        if uri.startswith("minio://"):
            content = self.store.get_artefact(uri)
            if content is None:
                raise IntakeValidatorError("A/B/C", f"Artefact not found: {uri}")
            return content  # type: ignore[return-value]
        raise ValueError(f"Unsupported URI scheme: {uri!r}")

    async def process(self, message: IntakeDispatch) -> AuditState:  # type: ignore[override]
        """Run Stage 0 A/B/C and return a populated AuditState.

        :param message: IntakeDispatch from the Orchestrator.
        :returns: AuditState with the client submission, completeness score,
            declared fields, and phase artefacts for T01a/T01b/T01c.
        :raises IntakeValidatorError: On any gate failure.
        """
        engagement_id = message["engagement_id"]

        stage_a_payload = self._load(message["stage_a_uri"])
        gate, art43_preview, t01a_uri = run_stage_a(self, engagement_id, stage_a_payload)

        stage_b_payload = self._load(message["stage_b_uri"])
        declared_modality: str = stage_a_payload["declared_modality"]
        submission, report, t01c_content, t01b_uri, t01c_uri = run_stage_b(
            self, engagement_id, stage_a_payload, stage_b_payload,
            declared_modality, art43_preview)

        client_doc_collection = ingest_client_docs(
            self, engagement_id, stage_b_payload, t01c_content)

        stage_c_present = bool(message.get("stage_c_uri"))
        if stage_c_present:
            submission["stage_c"] = self._load(message["stage_c_uri"])  # type: ignore[typeddict-item]

        return assemble_state(
            engagement_id, submission, stage_a_payload, gate, report.score,
            client_doc_collection,
            artefact_uris={
                "T01a_stage_a_triage": t01a_uri,
                "T01b_annex_iv_dossier": t01b_uri,
                "T01c_intake_completeness_report": t01c_uri,
            },
            stage_c_present=stage_c_present,
        )
