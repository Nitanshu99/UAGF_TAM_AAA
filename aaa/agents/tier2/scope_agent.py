"""
ScopeAgent — Tier-2 Phase 1 Declaration Verifier (§3.2 #4).

Receives a ``Dispatch`` from the Orchestrator containing T01a + T01b URIs
and performs the following workflow:

  1. Load the intake bundle (T01a, T01b) from the Evidence Store.
  2. Build a system description string for classifier and RAG queries.
  3. Call ``annex_iii_classify`` to verify declared Annex III sections.
  4. Cross-check classification via ``RegulatoryRAG`` search.
  5. Enforce the Art. 5 prohibition gate — HALT on any prohibited use case.
  6. Perform GPAI screening.
  7. Confirm / override ``is_llm_or_agentic`` based on verified modality.
  8. Call ``declaration_diff`` to build the ``declaration_verification`` map.
  9. Run ``art43_select`` (final mode) → T05.
  10. Determine ``verified_risk_tier``.
  11. Write T02, T03, T04, T05 to the Evidence Store.
  12. Emit a ``Report`` with ``declaration_verification_delta``.

Any ``"mismatch"`` in ``declaration_verification`` sets
``hitl_required=True`` in the returned state update.  The Orchestrator
raises this as a HITL trigger before running the final CSP plan (§8.4).

LLM path:
  - Production: Claude Sonnet via LiteLLM (``AAA_OFFLINE_MODE=false``).
  - Offline: deterministic rule-based verification only.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.platform.evidence import EvidenceStore
from aaa.platform.state import AnnexIIIEntry, AuditState
from aaa.tools.annex_iii_classify import annex_iii_classify
from aaa.tools.art43_select import art43_select_from_state
from aaa.tools.declaration_diff import declaration_diff, diff_annex_iii_sections

logger = logging.getLogger(__name__)

_OFFLINE = os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Art. 5 prohibited practice markers (simplified; full list in Annex to Act)
# ---------------------------------------------------------------------------
_ART5_MARKERS: list[str] = [
    "subliminal manipulation",
    "exploit vulnerability",
    "social scoring",
    "real-time remote biometric identification in public spaces",
    "real-time biometric identification in public space",
    "prohibited practice",
    "emotion inference in workplace",
    "untargeted facial image scraping",
    "predictive policing based solely on profiling",
]


class ScopeAgentError(Exception):
    """Raised when a hard gate (Art. 5 prohibition or schema failure) blocks Phase 1."""
    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[ScopeAgent] {reason}")


class ScopeAgent(BaseAgent):
    """
    Phase 1 — Scope and Risk Classifier.

    Verifies the client's declared values from Stage A, emits
    declaration_verification, and writes T02–T05 to the Evidence Store.
    """

    def __init__(
        self,
        evidence_store: EvidenceStore,
        regulatory_rag: Any | None = None,
        model: str = "claude-sonnet-4-5",
    ):
        super().__init__(name="ScopeAgent", model=model)
        self.store = evidence_store
        self.rag = regulatory_rag  # RegulatoryRAG instance or None

    # ------------------------------------------------------------------
    # BaseAgent protocol
    # ------------------------------------------------------------------

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """
        Run Phase 1 verification and return a Report.

        Parameters
        ----------
        message : Dispatch
            Must include ``evidence_uris`` with at minimum the T01a and T01b
            URIs, and ``declaration_summary`` populated from ``AuditState``
            declared_* fields.

        Returns
        -------
        Report
            Contains ``artefact_uri`` pointing to T02 (system card),
            ``declaration_verification_delta``, and confidence score.

        Raises
        ------
        ScopeAgentError
            When Art. 5 prohibition is detected (hard halt) or when an
            artefact cannot be loaded.
        """
        decl = message.get("declaration_summary", {})
        engagement_id = decl.get("engagement_id") or message["phase_id"]

        # ── 1. Load intake bundle ─────────────────────────────────────────────
        t01a, t01b = self._load_intake(message["evidence_uris"])

        # ── 2. Build system description string ───────────────────────────────
        system_desc = self._build_description(t01a, t01b)

        # ── 3. Classify Annex III sections ────────────────────────────────────
        declared_sections = t01a.get("declared_annex_iii_sections", [])
        rag_fn = self.rag.search if self.rag is not None else None
        annex_entries: list[AnnexIIIEntry] = annex_iii_classify(
            declared_sections=declared_sections,
            system_description=system_desc,
            rag_search_fn=rag_fn,
        )

        # ── 4. Art. 5 prohibition gate ────────────────────────────────────────
        art5_prohibited, art5_basis = self._check_art5(system_desc)
        if art5_prohibited:
            raise ScopeAgentError(
                reason=f"Art. 5 prohibited practice detected: {art5_basis}",
                details={"art5_basis": art5_basis, "system_description_excerpt": system_desc[:300]},
            )

        # ── 5. GPAI screening ─────────────────────────────────────────────────
        gpai_result = self._gpai_screen(t01a, system_desc)

        # ── 6. Determine verified modality + is_llm_or_agentic ───────────────
        verified_modality = self._verify_modality(t01a, t01b)
        is_llm_or_agentic = verified_modality in {"llm", "agentic", "gpai"}

        # ── 7. Determine verified risk tier ───────────────────────────────────
        verified_sections = [
            e["annex_iii_section"] for e in annex_entries
            if e["provenance"] in {"client_declared", "phase1_verified", "phase1_corrected"}
        ]
        verified_risk_tier = self._determine_risk_tier(
            t01a.get("declared_risk_tier", "minimal"),
            verified_sections,
            is_llm_or_agentic,
        )

        # ── 8. declaration_diff ───────────────────────────────────────────────
        declared_vals = {
            "modality": t01a.get("declared_modality", ""),
            "risk_tier": t01a.get("declared_risk_tier", ""),
            "deployment_context": t01a.get("deployment_context", ""),
            "is_llm_or_agentic": t01a.get("declared_modality", "") in {"llm", "agentic", "gpai"},
            "provider_elects_third_party": t01a.get("provider_elects_third_party", False),
            "gdpr_overlap": t01a.get("gdpr_overlap", False),
            "special_category_data": t01a.get("special_category_data", False),
            "gpai_general_purpose": t01a.get("gpai_general_purpose", False),
        }
        verified_vals = {
            "modality": verified_modality,
            "risk_tier": verified_risk_tier,
            "deployment_context": t01a.get("deployment_context", ""),
            "is_llm_or_agentic": is_llm_or_agentic,
            "provider_elects_third_party": t01a.get("provider_elects_third_party", False),
            "gdpr_overlap": t01a.get("gdpr_overlap", False),
            "special_category_data": t01a.get("special_category_data", False),
            "gpai_general_purpose": t01a.get("gpai_general_purpose", False),
        }
        verification_map = declaration_diff(declared_vals, verified_vals)
        annex_diff = diff_annex_iii_sections(declared_sections, verified_sections)
        verification_map.update(annex_diff)

        # Preserve Stage C not_verifiable if set
        if decl.get("live_system_access") == "not_verifiable":
            verification_map["live_system_access"] = "not_verifiable"

        # ── 9. art43_select (final mode) ──────────────────────────────────────
        pseudo_state: dict[str, Any] = {
            "risk_tier": verified_risk_tier,
            "annex_iii_mapping": [
                {"annex_iii_section": e["annex_iii_section"]} for e in annex_entries
                if e["provenance"] != "phase1_rejected"
            ],
            "harmonised_standards_applied": False,  # set by Phase 5
            "provider_elects_third_party": t01a.get("provider_elects_third_party", False),
        }
        art43 = art43_select_from_state(pseudo_state, use_declared=False)
        preview_procedure = t01a.get("art43_preview")
        delta = (preview_procedure is not None and preview_procedure != art43["procedure"])

        # ── 10. Write artefacts ───────────────────────────────────────────────
        now = datetime.now(timezone.utc).isoformat()

        t02 = self._build_t02(engagement_id, t01a, verified_modality, is_llm_or_agentic,
                               verification_map, gpai_result, art5_prohibited, now)
        t03 = self._build_t03(engagement_id, annex_entries, verified_risk_tier,
                               art5_prohibited, now)
        t04 = self._build_t04(engagement_id, t01a.get("declared_risk_tier", "minimal"),
                               verified_risk_tier, art5_prohibited, verified_sections, now)
        t05 = self._build_t05(engagement_id, art43, preview_procedure, delta,
                               pseudo_state, now)

        t02_uri = self.store.store_artefact(engagement_id, "phase_1", "T02_system_card", t02, self.name)
        t03_uri = self.store.store_artefact(engagement_id, "phase_1", "T03_annex_iii_mapping", t03, self.name)
        t04_uri = self.store.store_artefact(engagement_id, "phase_1", "T04_risk_tier_decision", t04, self.name)
        t05_uri = self.store.store_artefact(engagement_id, "phase_1", "T05_art43_decision", t05, self.name)

        # ── 11. Emit Report ───────────────────────────────────────────────────
        mismatches = [f for f, v in verification_map.items() if v == "mismatch"]
        confidence = 0.9 if not mismatches else 0.65

        return Report(
            phase_id="P1",
            artefact_uri=t02_uri,
            summary=(
                f"Phase 1 complete. verified_risk_tier={verified_risk_tier}, "
                f"verified_modality={verified_modality}, "
                f"art43_procedure={art43['procedure']}, "
                f"mismatches={mismatches or 'none'}."
            ),
            confidence=confidence,
            tool_calls=[
                {"tool": "annex_iii_classify", "result": f"{len(annex_entries)} entries"},
                {"tool": "declaration_diff", "result": verification_map},
                {"tool": "art43_select", "result": art43["procedure"]},
            ],
            declaration_verification_delta={
                "declaration_verification": verification_map,
                "verified_modality": verified_modality,
                "verified_risk_tier": verified_risk_tier,
                "annex_iii_mapping": [dict(e) for e in annex_entries],
                "is_llm_or_agentic": is_llm_or_agentic,
                "art43_decision": dict(art43),
                "art43_delta": delta,
                "hitl_required": bool(mismatches),
                "hitl_reason": (
                    f"Declaration mismatch on fields: {mismatches}" if mismatches else None
                ),
                "phase_artefacts": {
                    "T02_system_card": {"uri": t02_uri, "sha256": "", "template_id": "T02_system_card"},
                    "T03_annex_iii_mapping": {"uri": t03_uri, "sha256": "", "template_id": "T03_annex_iii_mapping"},
                    "T04_risk_tier_decision": {"uri": t04_uri, "sha256": "", "template_id": "T04_risk_tier_decision"},
                    "T05_art43_decision": {"uri": t05_uri, "sha256": "", "template_id": "T05_art43_decision"},
                },
            },
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_intake(self, evidence_uris: list[str]) -> tuple[dict, dict]:
        """Load T01a and T01b from the Evidence Store."""
        t01a: dict[str, Any] = {}
        t01b: dict[str, Any] = {}
        for uri in evidence_uris:
            content = self.store.get_artefact(uri)
            if content is None:
                logger.warning("ScopeAgent: artefact not found at URI %s", uri)
                continue
            if "declared_modality" in content or "provider_name" in content:
                t01a = content
            elif "general_description" in content or "model_type" in content:
                t01b = content
        return t01a, t01b

    def _build_description(self, t01a: dict, t01b: dict) -> str:
        """Concatenate key text fields for classifier / RAG queries."""
        parts = [
            t01a.get("intended_purpose", ""),
            t01b.get("general_description", ""),
            t01b.get("training_data_description", ""),
            t01b.get("design_process", ""),
        ]
        return " ".join(p for p in parts if p).lower()

    def _check_art5(self, description: str) -> tuple[bool, str]:
        """Check for Art. 5 prohibited practice markers in the description."""
        for marker in _ART5_MARKERS:
            if marker in description.lower():
                return True, marker
        return False, ""

    def _gpai_screen(self, t01a: dict, description: str) -> str | None:
        """Return a GPAI screening note if applicable, else None."""
        if t01a.get("gpai_general_purpose") or "general purpose" in description:
            return (
                "System declared as / detected to be a GPAI model. "
                "Arts. 51–55 obligations apply. "
                "UAGF-TAM-L branch activated."
            )
        return None

    def _verify_modality(self, t01a: dict, t01b: dict) -> str:
        """
        Verify the declared modality against Stage B evidence.

        In offline mode: deterministic rule based on declared_modality.
        In production: would use LLM analysis of model_type and description.
        """
        declared = t01a.get("declared_modality", "tabular")
        model_type = t01b.get("model_type", "").lower()

        # Simple offline heuristic — production LLM path omitted
        if "llm" in model_type or "language model" in model_type or "gpt" in model_type:
            return "llm"
        if "agentic" in model_type or "agent" in model_type:
            return "agentic"
        if "image" in model_type or "vision" in model_type or "cnn" in model_type:
            return "cv"
        if "time series" in model_type or "forecasting" in model_type:
            return "time_series"
        if "nlp" in model_type or "bert" in model_type or "text" in model_type:
            return "nlp"
        return declared

    def _determine_risk_tier(
        self,
        declared_risk_tier: str,
        verified_sections: list[str],
        is_llm_or_agentic: bool,
    ) -> str:
        """
        Determine verified risk tier.

        Rule: any confirmed Annex III section (without derogation) → high.
        GPAI modality without Annex III section → gpai tier.
        Otherwise: use declared tier.
        """
        if verified_sections:
            return "high"
        if is_llm_or_agentic and declared_risk_tier == "gpai":
            return "gpai"
        return declared_risk_tier

    # ── Artefact builders ──────────────────────────────────────────────────

    def _build_t02(self, engagement_id: str, t01a: dict, verified_modality: str,
                   is_llm: bool, verification_map: dict, gpai_result: str | None,
                   art5: bool, now: str) -> dict:
        return {
            "engagement_id": engagement_id,
            "provider_name": t01a.get("provider_name", ""),
            "deployer_name": t01a.get("deployer_name"),
            "system_name": t01a.get("system_name", ""),
            "version": t01a.get("version", ""),
            "intended_purpose": t01a.get("intended_purpose", ""),
            "declared_modality": t01a.get("declared_modality", ""),
            "verified_modality": verified_modality,
            "deployment_context": t01a.get("deployment_context", ""),
            "is_llm_or_agentic": is_llm,
            "provider_elects_third_party": t01a.get("provider_elects_third_party", False),
            "gdpr_overlap": t01a.get("gdpr_overlap", False),
            "special_category_data": t01a.get("special_category_data", False),
            "declaration_verification": verification_map,
            "phase1_summary": (
                f"Phase 1 verified modality as '{verified_modality}'. "
                f"Mismatches: {[f for f,v in verification_map.items() if v == 'mismatch'] or 'none'}."
            ),
            "art5_prohibited": art5,
            "gpai_screening_result": gpai_result,
            "generated_at": now,
        }

    def _build_t03(self, engagement_id: str, entries: list[AnnexIIIEntry],
                   verified_risk_tier: str, art5: bool, now: str) -> dict:
        return {
            "engagement_id": engagement_id,
            "entries": [dict(e) for e in entries],
            "verified_risk_tier": verified_risk_tier,
            "art5_prohibited": art5,
            "classification_narrative": (
                f"{len(entries)} Annex III section(s) identified. "
                f"Verified risk tier: {verified_risk_tier}."
            ),
            "generated_at": now,
        }

    def _build_t04(self, engagement_id: str, declared_tier: str, verified_tier: str,
                   art5: bool, verified_sections: list[str], now: str) -> dict:
        return {
            "engagement_id": engagement_id,
            "declared_risk_tier": declared_tier,
            "verified_risk_tier": verified_tier,
            "risk_tier_rationale": (
                f"Declared tier: {declared_tier}. "
                f"Verified tier: {verified_tier} based on confirmed Annex III sections: "
                f"{verified_sections or 'none'}."
            ),
            "art5_prohibited": art5,
            "art5_prohibition_basis": None,
            "art6_derogation_claimed": False,
            "art6_derogation_rationale": None,
            "art6_derogation_accepted": None,
            "annex_iii_sections_verified": verified_sections,
            "regulatory_rag_citations": ["EU AI Act Art. 6", "EU AI Act Annex III"],
            "generated_at": now,
        }

    def _build_t05(self, engagement_id: str, art43: dict, preview: str | None,
                   delta: bool, inputs: dict, now: str) -> dict:
        section_1_applies = any(
            e.get("annex_iii_section") == "1"
            for e in inputs.get("annex_iii_mapping", [])
        )
        return {
            "engagement_id": engagement_id,
            "procedure": art43["procedure"],
            "rationale": art43["rationale"],
            "binding_statement": (
                f"The conformity assessment procedure for this engagement is: "
                f"{art43['procedure'].replace('_', ' ').title()}. "
                f"{art43['rationale']}"
            ),
            "preview_procedure": preview,
            "delta_from_preview": delta,
            "inputs": {
                "risk_tier": inputs.get("risk_tier", ""),
                "annex_iii_section_1_applies": section_1_applies,
                "harmonised_standards_applied": inputs.get("harmonised_standards_applied", False),
                "provider_elects_third_party": inputs.get("provider_elects_third_party", False),
            },
            "generated_at": now,
        }
