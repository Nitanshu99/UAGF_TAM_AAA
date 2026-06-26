"""
GovernanceAgent — Tier-2 Phase 5 Governance Agent (§3.2 #8).

Receives a ``Dispatch`` from the Orchestrator and performs the following
workflow:

  1. Pull the S4 CGSA payload via ``cgsa_pull`` (HTTP or fixture).
  2. Validate + ingest the payload via ``cgsa_ingest``; hydrate the
     ``CGSAPayload`` §5.4 fields.
  3. Cross-check ``metadata.risk_tier`` against the Phase 1 verified
     ``risk_tier`` — mismatch ⇒ HITL trigger (§8.4).
  4. Decide Tier-3 spawns (Cyber, Privacy) per §3.3.
  5. Build T14 (governance findings) from the CGSA hand-off surface.
  6. Build T15 (monitoring & logging review) from the Annex IV dossier
     (Art. 12 / 17 / 72).
  7. Write T14, T15 to the Evidence Store.
  8. Emit ``Report`` whose ``declaration_verification_delta`` carries the
     full §5.4 state hydration, the two new artefact URIs, and any HITL
     trigger.

LLM path:
  - Production: Claude Opus via LiteLLM (``AAA_OFFLINE_MODE=false``).
  - Offline: deterministic rule-based path only.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.platform.evidence import EvidenceStore
from aaa.tools.cgsa_ingest import CGSAIngestError, IngestResult, cgsa_ingest
from aaa.tools.cgsa_pull import CGSAPullError, cgsa_pull
from aaa.tools.client_doc_ingest import client_doc_search
from aaa.tools.findings import make_finding

logger = logging.getLogger(__name__)

_OFFLINE = os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"
_PROMPT_NAME = "phase5_governance"

# Governance articles evidenced by the Phase 5 artefacts: T14 → Art.9 (risk
# management) / Art.17 (QMS); T15 → Art.12 (record-keeping) / Art.72 (post-market
# monitoring). When the CGSA self-assessment cannot be retrieved or validated, these
# are the articles the auditor can no longer conclude on — they become
# INSUFFICIENT_EVIDENCE (→ disclaimer), not a confirmed non-conformity.
_GOVERNANCE_INSUFFICIENT_ARTICLES = ["Art.9", "Art.12", "Art.17", "Art.72"]


class GovernanceAgentError(Exception):
    """Raised when a hard gate blocks Phase 5."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[GovernanceAgent] {reason}")


class GovernanceAgent(BaseAgent):
    """
    Phase 5 — Governance Agent.

    Ingests the upstream S4 CGSA payload, lifts the §5.4 hand-off surface
    into ``AuditState`` and emits T14 + T15 artefacts.  Phase 5 verdict is
    driven primarily by ``aaa_phase5_handoff.phase5_verdict``; CSP failure
    forces FAIL.
    """

    def __init__(
        self,
        evidence_store: EvidenceStore,
        model: str | None = None,
        service_tier: str | None = None,
    ):
        from aaa.platform.model_registry import resolve_model, resolve_service_tier
        super().__init__(
            name="GovernanceAgent",
            model=resolve_model("GovernanceAgent", model),
            service_tier=resolve_service_tier("GovernanceAgent", service_tier),
        )
        self.store = evidence_store

    # ------------------------------------------------------------------
    # BaseAgent protocol
    # ------------------------------------------------------------------

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """
        Run Phase 5 governance ingestion and return a Report.

        Parameters
        ----------
        message : Dispatch
            ``declaration_summary`` must include ``engagement_id``;
            should include ``risk_tier``, ``cgsa_assessment_id``,
            ``gdpr_overlap``, ``special_category_data``,
            ``annex_iii_sections``.  Optional: ``cgsa_payload`` to short-
            circuit the pull (used by Orchestrator when payload is
            already on AuditState), ``phase3_robustness_verdict``,
            ``phase4_fairness_verdict``.  ``evidence_uris`` should
            include T01a and T01b URIs.
        """
        decl = message.get("declaration_summary", {})
        engagement_id: str = decl.get("engagement_id") or message["phase_id"]

        # ── 1. Pull (or accept inline) CGSA payload ──────────────────────────
        payload = decl.get("cgsa_payload")
        if payload is None:
            assessment_id = decl.get("cgsa_assessment_id")
            try:
                payload = cgsa_pull(assessment_id=assessment_id or "")
            except CGSAPullError as exc:
                return self._escalate_report(
                    engagement_id,
                    reason=f"cgsa_pull failed: {exc.reason}",
                    details=exc.details,
                )

        # ── 2. Validate + ingest ─────────────────────────────────────────────
        try:
            result = cgsa_ingest(
                payload,
                phase1_risk_tier=decl.get("risk_tier"),
                strict=False,
            )
        except CGSAIngestError as exc:
            return self._escalate_report(
                engagement_id,
                reason=f"cgsa_ingest failed: {exc.reason}",
                details=exc.details,
            )

        if result.schema_errors:
            return self._escalate_report(
                engagement_id,
                reason="cgsa_ingest schema validation failed",
                details={"errors": result.schema_errors[:5]},
            )

        source_remediation = (
            payload.get("remediation_roadmap", [])
            if isinstance(payload, dict) else []
        )
        result.state_delta["remediation_roadmap"] = self._enrich_remediation_roadmap(
            result.state_delta.get("remediation_roadmap", []),
            decl.get("organisation_contacts", {}) or {},
            source_remediation,
        )
        result.state_delta["cgsa_domain_scores"] = self._domain_scores_for_chart(payload)

        # ── 3. Risk-tier cross-check ─────────────────────────────────────────
        risk_tier_mismatch = result.state_delta.get("cgsa_risk_tier_match") is False

        # ── 4. Tier-3 spawn decisions ────────────────────────────────────────
        spawn = self._decide_tier3_spawns(decl, result)

        # ── 5/6. Build T14 + T15 ─────────────────────────────────────────────
        t01a, t01b = self._load_intake(message.get("evidence_uris", []))
        now = datetime.now(timezone.utc).isoformat()
        client_doc_hits: list[dict[str, Any]] = []
        if decl.get("client_doc_collection"):
            client_doc_hits = client_doc_search(
                engagement_id,
                "monitoring logging post-market QMS risk management governance controls",
                top_k=3,
            )
        llm_payload: dict[str, Any] = {}
        llm_fallback_mode = _OFFLINE
        if not _OFFLINE:
            try:
                llm_payload = await self.acompletion_json(
                    _PROMPT_NAME,
                    {
                        "task": message.get("task_brief")
                        or "Execute Phase 5 governance review per the Phase 5 Protocol.",
                        "evidence_uris": message.get("evidence_uris", []),
                        "declaration_summary": decl,
                        "client_doc_hits": client_doc_hits,
                        "rerun_context": None,
                        "cgsa_payload": payload,
                        "ingest_state_delta": result.state_delta,
                        "spawn_recommendations": spawn,
                    },
                )
                llm_fallback_mode = False
            except Exception as exc:
                logger.warning("GovernanceAgent prompt runtime failed (%s); using deterministic fallback.", exc)
        prompt_note = self.prompt_note(_PROMPT_NAME, llm_fallback_mode)
        llm_summary = llm_payload.get("summary") or llm_payload.get("phase5_narrative_summary")
        t14 = self._build_t14(engagement_id, result, decl, spawn, risk_tier_mismatch, now)
        t15 = self._build_t15(engagement_id, t01b, result, now)
        t14["phase5_narrative_summary"] = f"{llm_summary or t14['phase5_narrative_summary']} {prompt_note}".strip()
        t15["observations"] = list(t15.get("observations", [])) + [prompt_note]

        # ── 7. Store artefacts ───────────────────────────────────────────────
        t14_uri = self.store.store_artefact(
            engagement_id, "phase_5", "T14_governance_findings", t14, self.name)
        t15_uri = self.store.store_artefact(
            engagement_id, "phase_5", "T15_monitoring_logging_review", t15, self.name)

        # ── 8. Emit Report ───────────────────────────────────────────────────
        phase5_verdict = result.state_delta.get("cgsa_phase5_verdict") or "PASS_WITH_OBSERVATIONS"
        low_conf_hitl = len(result.low_confidence_controls) > 0
        csp_fail = result.state_delta.get("cgsa_csp_satisfiable") is False
        hitl_required = (
            phase5_verdict == "FAIL"
            or csp_fail
            or risk_tier_mismatch
            or low_conf_hitl
            or t15.get("hitl_required", False)
            or self._has_blocking_followups(result)
        )
        confidence = 0.9 if not hitl_required else 0.65

        delta: dict[str, Any] = dict(result.state_delta)
        delta["phase_artefacts"] = {
            "T14_governance_findings": {
                "uri": t14_uri, "sha256": "", "template_id": "T14_governance_findings"},
            "T15_monitoring_logging_review": {
                "uri": t15_uri, "sha256": "", "template_id": "T15_monitoring_logging_review"},
        }

        # Treat the client's CGSA self-assessment as a claim to be tested, not as
        # evidence: reconcile its internal consistency and raise findings on gaps.
        recon_findings = self._reconcile_cgsa(payload)
        if recon_findings:
            delta["blocking_findings"] = recon_findings
            hitl_required = hitl_required or any(
                f.get("materiality") == "material" for f in recon_findings
            )
        if spawn["cyber_spawn"]:
            delta["spawn_cyber_subagent"] = True
            delta["cyber_spawn_rationale"] = spawn["cyber_rationale"]
        if spawn["privacy_spawn"]:
            delta["spawn_privacy_subagent"] = True
            delta["privacy_spawn_rationale"] = spawn["privacy_rationale"]
        if hitl_required:
            delta["hitl_required"] = True
            delta["hitl_reason"] = self._build_hitl_reason(
                phase5_verdict, csp_fail, risk_tier_mismatch,
                low_conf_hitl, t15, result,
            )

        return Report(
            phase_id="P5",
            artefact_uri=t14_uri,
            summary=(
                llm_summary
                or
                f"Phase 5 complete. cgsa_phase5_verdict={phase5_verdict}, "
                f"csp_satisfiable={result.state_delta.get('cgsa_csp_satisfiable')}, "
                f"blocking_findings={len(result.state_delta.get('cgsa_blocking_findings', []))}, "
                f"low_confidence_controls={len(result.low_confidence_controls)}, "
                f"cyber_spawn={spawn['cyber_spawn']}, privacy_spawn={spawn['privacy_spawn']}."
            ),
            confidence=confidence,
            tool_calls=[
                {"tool": "cgsa_pull",
                 "result": f"assessment_id={result.payload.get('metadata', {}).get('assessment_id', 'inline')}"},
                {"tool": "cgsa_ingest",
                 "result": (
                     f"schema_errors={len(result.schema_errors)}, "
                     f"phase5_verdict={phase5_verdict}, "
                     f"risk_tier_match={result.state_delta.get('cgsa_risk_tier_match')}"
                 )},
                {"tool": "client_doc_search", "result": f"hits={len(client_doc_hits)}"},
                {"tool": "prompt_runtime", "result": prompt_note},
            ],
            declaration_verification_delta=delta,
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
                continue
            if "declared_modality" in content or "provider_name" in content:
                t01a = content
            elif "general_description" in content or "model_type" in content:
                t01b = content
        return t01a, t01b

    def _reconcile_cgsa(self, payload: Any) -> list[dict[str, Any]]:
        """Reconcile the CGSA self-assessment's internal consistency.

        A real auditor does not accept a maturity scorecard at face value. We check
        that the headline control counts match the detailed control list and that any
        below-threshold control is actually identified — raising findings on gaps.
        """
        if not isinstance(payload, dict):
            return []
        findings: list[dict[str, Any]] = []
        scores = payload.get("overall_scores", {}) or {}
        domains = payload.get("domains", []) or []

        detailed = [
            c for d in domains for c in (d.get("controls", []) or [])
        ]
        n_detailed = len(detailed)
        assessed = scores.get("controls_assessed")
        meeting = scores.get("controls_meeting_threshold")
        if meeting is None:
            meeting = scores.get("controls_meeting")
        below = scores.get("controls_below_threshold")

        if isinstance(assessed, int) and assessed != n_detailed:
            findings.append(make_finding(
                finding_id="P5-CGSA-COUNT",
                description=(
                    f"CGSA self-assessment reports {assessed} controls assessed but only "
                    f"{n_detailed} are detailed in the domain breakdown; the remaining "
                    f"{assessed - n_detailed} are unverifiable."
                ),
                materiality="possibly_material",
                articles=["Art.17"],
                source_phase="P5",
                recommendation="Provide the full per-control evidence behind the headline counts.",
                declared=assessed,
                observed=n_detailed,
            ))

        # Identify below-threshold controls in the detail (score < hard-constraint
        # threshold, defaulting to maturity 3).
        def _below(ctrl: dict) -> bool:
            score = ctrl.get("maturity_score")
            thr = (ctrl.get("hard_constraint", {}) or {}).get("threshold_score") or 3
            return isinstance(score, (int, float)) and score < thr

        identified_below = [c for c in detailed if _below(c)]
        if isinstance(below, int) and below > 0 and len(identified_below) < below:
            findings.append(make_finding(
                finding_id="P5-CGSA-BELOW",
                description=(
                    f"CGSA reports {below} control(s) below threshold but the detailed "
                    f"breakdown identifies only {len(identified_below)}; the unidentified "
                    "below-threshold control(s) cannot be assessed."
                ),
                materiality="possibly_material",
                articles=["Art.17"],
                source_phase="P5",
                recommendation="Name each below-threshold control and its remediation plan.",
                declared=below,
                observed=len(identified_below),
            ))
        return findings

    def _decide_tier3_spawns(
        self,
        decl: dict[str, Any],
        result: IngestResult,
    ) -> dict[str, Any]:
        """
        Decide Tier-3 sub-agent spawns per §3.3.

        Cyber: risk_tier=high OR Art. 15 evidence missing/FAIL.
        Privacy: gdpr_overlap=true OR special_category_data=true OR
                 Annex III §1 (biometric).
        """
        risk_tier = (decl.get("risk_tier") or "").lower()
        art15_verdict = (decl.get("phase3_robustness_verdict") or "").upper()
        cyber_spawn = False
        cyber_rationale: str | None = None
        if risk_tier == "high":
            cyber_spawn = True
            cyber_rationale = "risk_tier=high → Cyber Sub-Agent per §3.3."
        elif art15_verdict in {"FAIL", "NOT_TESTED"}:
            cyber_spawn = True
            cyber_rationale = (
                f"Phase 3 robustness verdict={art15_verdict} — "
                "Art. 15 evidence missing/failed."
            )

        annex_iii_sections = decl.get("annex_iii_sections") or []
        if isinstance(annex_iii_sections, list):
            annex_iii_section_ids = {str(s) for s in annex_iii_sections}
        else:
            annex_iii_section_ids = set()

        privacy_spawn = False
        privacy_rationale: str | None = None
        if decl.get("gdpr_overlap"):
            privacy_spawn = True
            privacy_rationale = "gdpr_overlap=true → Privacy/DPO Sub-Agent per §3.3."
        elif decl.get("special_category_data"):
            privacy_spawn = True
            privacy_rationale = (
                "special_category_data=true → Privacy/DPO Sub-Agent per §3.3."
            )
        elif "1" in annex_iii_section_ids:
            privacy_spawn = True
            privacy_rationale = (
                "Annex III §1 biometric use case → Privacy/DPO Sub-Agent per §3.3."
            )

        return {
            "cyber_spawn": cyber_spawn,
            "cyber_rationale": cyber_rationale,
            "privacy_spawn": privacy_spawn,
            "privacy_rationale": privacy_rationale,
        }

    @staticmethod
    def _has_blocking_followups(result: IngestResult) -> bool:
        """True if any CGSA follow-up has urgency=required_before_report_completion."""
        for item in result.state_delta.get("cgsa_recommended_follow_up", []) or []:
            if item.get("urgency") == "required_before_report_completion":
                return True
        return False

    @staticmethod
    def _enrich_remediation_roadmap(
        items: list[dict[str, Any]],
        contacts: dict[str, Any],
        source_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Add owner, priority and deadline fields to CGSA remediation items."""
        domain_to_owner_field = {
            "D1": "technical_lead",
            "D2": "data_lead",
            "D3": "technical_lead",
            "D4": "compliance_lead",
            "D5": "compliance_lead",
            "D6": "dpo",
        }
        severity_map = {
            "critical": ("immediate", 4),
            "major": ("short_term", 12),
            "minor": ("medium_term", 26),
            "observation": ("long_term", 52),
        }
        enriched: list[dict[str, Any]] = []
        for idx, item in enumerate(items):
            source = source_items[idx] if idx < len(source_items) else {}
            domain_id = item.get("domain_id") or source.get("domain_id") or ""
            owner_field = domain_to_owner_field.get(domain_id, "technical_lead")
            severity = str(
                item.get("gap_severity") or source.get("gap_severity") or ""
            ).lower()
            priority_label, deadline_weeks = severity_map.get(severity, ("long_term", 52))
            enriched_item = dict(item)
            enriched_item["domain_id"] = domain_id
            enriched_item["assigned_owner"] = contacts.get(owner_field, "To be assigned")
            enriched_item["priority_label"] = priority_label
            enriched_item["deadline_weeks"] = deadline_weeks
            enriched.append(enriched_item)
        return enriched

    @staticmethod
    def _domain_scores_for_chart(payload: Any) -> dict[str, float]:
        """Extract {domain_label: score} from CGSA domains for the radar chart."""
        if not isinstance(payload, dict):
            return {}
        domain_scores: dict[str, float] = {}
        for domain in payload.get("domains", []) or []:
            domain_id = domain.get("domain_id", "")
            domain_name = domain.get("domain_name", domain_id)
            label = f"{domain_id} {domain_name}".strip()
            try:
                domain_scores[label] = float(domain.get("domain_score", 0.0))
            except (TypeError, ValueError):
                domain_scores[label] = 0.0
        return domain_scores

    @staticmethod
    def _build_hitl_reason(
        phase5_verdict: str,
        csp_fail: bool,
        risk_tier_mismatch: bool,
        low_conf: bool,
        t15: dict[str, Any],
        result: IngestResult,
    ) -> str:
        reasons: list[str] = []
        if phase5_verdict == "FAIL":
            reasons.append("Phase 5 verdict is FAIL.")
        if csp_fail:
            reasons.append("CGSA csp_satisfiable=false (hard-constraint violation).")
        if risk_tier_mismatch:
            reasons.append(
                "Phase 1 risk_tier disagrees with CGSA metadata.risk_tier."
            )
        if low_conf:
            reasons.append(
                f"{len(result.low_confidence_controls)} CGSA controls flagged "
                "low-confidence (<0.60)."
            )
        if t15.get("hitl_required"):
            reasons.append(t15.get("hitl_reason") or "Ops review escalation.")
        if not reasons:
            reasons.append("Phase 5 escalation.")
        return " ".join(reasons)

    def _escalate_report(
        self,
        engagement_id: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> Report:
        """Build a Report that flips Phase 5 into HITL escalation.

        A failure to *retrieve or validate* the CGSA self-assessment (pull failed,
        no fixture, service down, schema invalid) is an evidence-availability
        problem — it does **not** establish that governance is non-conformant.
        Conflating the two would let infrastructure flakiness issue a blanket
        adverse FAIL. So we mark the governance articles INSUFFICIENT_EVIDENCE
        (the compliance matrix downgrades the opinion to a disclaimer for them)
        instead of forcing ``cgsa_phase5_verdict="FAIL"``. A genuine FAIL is only
        ever raised from a CGSA payload that is present *and* reports
        ``phase5_verdict="FAIL"`` / ``csp_satisfiable=False`` (see ``cgsa_ingest``).
        """
        logger.warning("[GovernanceAgent] escalating: %s (%s)", reason, details)
        delta: dict[str, Any] = {
            "hitl_required": True,
            "hitl_reason": reason,
            "insufficient_evidence_articles": list(_GOVERNANCE_INSUFFICIENT_ARTICLES),
            "phase_artefacts": {},
        }
        if details:
            delta["cgsa_ingest_details"] = details
        return Report(
            phase_id="P5",
            artefact_uri="",
            summary=(
                f"Phase 5 escalated to HITL — {reason}. CGSA self-assessment "
                "unavailable; governance articles (Art.9/Art.12/Art.17/Art.72) "
                "marked INSUFFICIENT_EVIDENCE (disclaimer), not FAIL."
            ),
            confidence=0.2,
            tool_calls=[{"tool": "cgsa_pull_or_ingest", "result": reason}],
            declaration_verification_delta=delta,
        )

    # ── Artefact builders ──────────────────────────────────────────────────

    def _build_t14(
        self,
        engagement_id: str,
        result: IngestResult,
        decl: dict[str, Any],
        spawn: dict[str, Any],
        risk_tier_mismatch: bool,
        now: str,
    ) -> dict[str, Any]:
        """Build T14 Governance Findings from the §5.4 hand-off surface."""
        payload = result.payload
        metadata = payload.get("metadata", {}) or {}
        scores = payload.get("overall_scores", {}) or {}
        handoff = payload.get("aaa_phase5_handoff", {}) or {}
        hard = payload.get("hard_constraint_results", {}) or {}

        return {
            "engagement_id": engagement_id,
            "cgsa_schema_version": result.schema_version,
            "cgsa_metadata": {
                "assessment_id": metadata.get("assessment_id", ""),
                "organisation_name": metadata.get("organisation_name", ""),
                "system_under_audit": metadata.get("system_under_audit", ""),
                "cgsa_version": metadata.get("cgsa_version", ""),
                "assessment_timestamp": metadata.get("assessment_timestamp", ""),
                "risk_tier": metadata.get("risk_tier", ""),
                "document_sources": list(metadata.get("document_sources", []) or []),
                "uagf_gmm_version": metadata.get("uagf_gmm_version"),
            },
            "overall_scores": {
                "composite_maturity_score": scores.get("composite_maturity_score", 0.0),
                "composite_maturity_label": scores.get("composite_maturity_label", "absent"),
                "eu_ai_act_coverage_pct": scores.get("eu_ai_act_coverage_pct", 0.0),
                "csp_satisfiable": bool(scores.get("csp_satisfiable", False)),
                "governance_verdict": scores.get("governance_verdict", "non_compliant"),
                "controls_assessed": scores.get("controls_assessed"),
                "controls_meeting_threshold": scores.get("controls_meeting_threshold"),
                "controls_below_threshold": scores.get("controls_below_threshold"),
            },
            "phase5_verdict": result.state_delta.get("cgsa_phase5_verdict")
                or handoff.get("phase5_verdict") or "PASS_WITH_OBSERVATIONS",
            "phase5_narrative_summary": handoff.get("phase5_narrative_summary", ""),
            "blocking_findings_count": int(handoff.get("blocking_findings_count", 0) or 0),
            "blocking_findings": [
                {
                    "control_id": f.get("control_id", ""),
                    "control_name": f.get("control_name", ""),
                    "finding": f.get("finding", ""),
                    "eu_ai_act_article": f.get("eu_ai_act_article", ""),
                    "remediation_action": f.get("remediation_action", ""),
                    "gap_severity": f.get("gap_severity"),
                }
                for f in (handoff.get("blocking_findings", []) or [])
            ],
            "positive_findings": [
                {
                    "control_id": f.get("control_id", ""),
                    "control_name": f.get("control_name", ""),
                    "maturity_score": int(f.get("maturity_score", 0)),
                    "finding": f.get("finding", ""),
                }
                for f in (handoff.get("positive_findings", []) or [])
            ],
            "low_confidence_controls": [
                {
                    "control_id": c.get("control_id", ""),
                    "control_name": c.get("control_name", ""),
                    "confidence": float(c.get("confidence", 0.0)),
                    "flag_reason": c.get("flag_reason", ""),
                }
                for c in result.low_confidence_controls
            ],
            "domains": [
                {
                    "domain_id": d.get("domain_id", ""),
                    "domain_name": d.get("domain_name", ""),
                    "domain_score": float(d.get("domain_score", 0.0)),
                    "domain_eu_ai_act_articles": list(
                        d.get("domain_eu_ai_act_articles", []) or []
                    ),
                    "controls_count": (
                        len(d.get("controls", []) or [])
                        if d.get("controls") is not None else None
                    ),
                }
                for d in (payload.get("domains", []) or [])
            ],
            "hard_constraint_results": {
                "csp_satisfiable": bool(hard.get("csp_satisfiable", False)),
                "total_hard_constraints": hard.get("total_hard_constraints"),
                "violated_constraints": [
                    {
                        "control_id": v.get("control_id", ""),
                        "control_name": v.get("control_name", ""),
                        "required_score": int(v.get("required_score", 0)),
                        "actual_score": int(v.get("actual_score", 0)),
                        "score_delta": v.get("score_delta"),
                        "eu_ai_act_article": v.get("eu_ai_act_article", ""),
                        "violation_description": v.get("violation_description", ""),
                    }
                    for v in (hard.get("violated_constraints", []) or [])
                ],
            },
            "remediation_roadmap": [
                {
                    "rank": int(r.get("rank", idx + 1)),
                    "control_id": r.get("control_id", ""),
                    "control_name": r.get("control_name", ""),
                    "gap_severity": r.get("gap_severity", "medium"),
                    "recommended_action": r.get("recommended_action") or r.get("action", ""),
                    "assigned_owner": r.get("assigned_owner", "To be assigned"),
                    "priority_label": r.get("priority_label"),
                    "deadline_weeks": r.get("deadline_weeks"),
                    "domain_id": r.get("domain_id"),
                }
                for idx, r in enumerate(result.state_delta.get("remediation_roadmap", []) or [])
            ],
            "aaa_recommended_follow_up": [
                {
                    "recommendation": f.get("recommendation", ""),
                    "rationale": f.get("rationale", ""),
                    "urgency": f.get("urgency"),
                }
                for f in (handoff.get("aaa_recommended_follow_up", []) or [])
            ],
            "risk_tier_match": {
                "match": not risk_tier_mismatch
                    and result.state_delta.get("cgsa_risk_tier_match") is not False,
                "phase1_risk_tier": decl.get("risk_tier", ""),
                "cgsa_risk_tier": metadata.get("risk_tier", ""),
                "hitl_triggered": risk_tier_mismatch,
            },
            "tier3_spawn_recommendations": {
                "cyber_spawn": spawn["cyber_spawn"],
                "cyber_rationale": spawn["cyber_rationale"],
                "privacy_spawn": spawn["privacy_spawn"],
                "privacy_rationale": spawn["privacy_rationale"],
            },
            "cgsa_report_url": handoff.get("cgsa_report_url"),
            "hitl_required": False,
            "hitl_reason": None,
            "generated_at": now,
        }

    def _build_t15(
        self,
        engagement_id: str,
        t01b: dict[str, Any],
        result: IngestResult,
        now: str,
    ) -> dict[str, Any]:
        """Build T15 Monitoring & Logging Review from Annex IV §6/§7/§9."""
        monitoring_text = (t01b.get("monitoring_measures") or "").strip()
        logging_text = (t01b.get("logging_capabilities") or "").strip()
        post_market_uri = t01b.get("post_market_plan_uri")
        harmonised = list(t01b.get("harmonised_standards", []) or [])

        monitoring_documented = bool(monitoring_text)
        logging_documented = bool(logging_text)
        post_market_provided = bool(post_market_uri)

        art12_status = self._verdict_from_bool(logging_documented)
        art17_status = self._verdict_from_qms(harmonised, monitoring_documented)
        art72_status = self._verdict_from_bool(post_market_provided)

        statuses = [art12_status, art17_status, art72_status]
        if "FAIL" in statuses:
            overall = "FAIL"
        elif "PASS_WITH_OBSERVATIONS" in statuses:
            overall = "PASS_WITH_OBSERVATIONS"
        elif all(s == "PASS" for s in statuses):
            overall = "PASS"
        else:
            overall = "PASS_WITH_OBSERVATIONS"

        observations: list[str] = []
        if not monitoring_documented:
            observations.append("No monitoring measures documented in Annex IV §6.")
        if not logging_documented:
            observations.append("No logging capabilities documented in Annex IV §7.")
        if not post_market_provided:
            observations.append("No post-market monitoring plan URI in Annex IV §9.")

        hitl = overall == "FAIL"
        hitl_reason = (
            "Monitoring/logging evidence missing or non-compliant."
            if hitl else None
        )

        return {
            "engagement_id": engagement_id,
            "monitoring_evidence": {
                "monitoring_measures_documented": monitoring_documented,
                "monitoring_summary": monitoring_text or None,
                "monitoring_tools": [],
                "drift_detection_documented": None,
                "performance_dashboards_documented": None,
            },
            "logging_evidence": {
                "logging_capabilities_documented": logging_documented,
                "logging_summary": logging_text or None,
                "automatic_logging_enabled": None,
                "log_retention_period": None,
                "log_integrity_controls": None,
            },
            "post_market_monitoring": {
                "plan_provided": post_market_provided,
                "plan_uri": post_market_uri,
                "incident_reporting_documented": None,
                "serious_incident_threshold_defined": None,
            },
            "art12_record_keeping": {
                "status": art12_status,
                "rationale": (
                    "Annex IV §7 logging capabilities documented."
                    if logging_documented
                    else "No logging capabilities documented in Annex IV §7."
                ),
                "evidence_refs": [],
            },
            "art17_qms": {
                "status": art17_status,
                "rationale": (
                    "Harmonised standards applied and monitoring measures documented."
                    if art17_status == "PASS"
                    else "QMS evidence partial — see observations."
                ),
                "qms_standard_referenced": (harmonised[0] if harmonised else None),
                "evidence_refs": [],
            },
            "art72_post_market_plan": {
                "status": art72_status,
                "rationale": (
                    "Post-market monitoring plan URI provided."
                    if post_market_provided
                    else "No post-market monitoring plan URI provided."
                ),
                "evidence_refs": ([post_market_uri] if post_market_uri else []),
            },
            "cgsa_cross_references": self._cgsa_ops_xrefs(result),
            "observations": observations,
            "overall_ops_verdict": overall,
            "hitl_required": hitl,
            "hitl_reason": hitl_reason,
            "generated_at": now,
        }

    @staticmethod
    def _verdict_from_bool(flag: bool) -> str:
        return "PASS" if flag else "PASS_WITH_OBSERVATIONS"

    @staticmethod
    def _verdict_from_qms(harmonised: list[str], monitoring: bool) -> str:
        if harmonised and monitoring:
            return "PASS"
        if harmonised or monitoring:
            return "PASS_WITH_OBSERVATIONS"
        return "FAIL"

    @staticmethod
    def _cgsa_ops_xrefs(result: IngestResult) -> list[dict[str, Any]]:
        """Lift CGSA D6 (Monitoring & Incident Response) controls into T15 xrefs."""
        xrefs: list[dict[str, Any]] = []
        for dom in result.payload.get("domains", []) or []:
            if dom.get("domain_id") != "D6":
                continue
            for ctrl in dom.get("controls", []) or []:
                for article in ctrl.get("eu_ai_act_articles", []) or []:
                    xrefs.append({
                        "article": article,
                        "control_id": ctrl.get("control_id", ""),
                        "rationale": ctrl.get("evidence_summary"),
                    })
        return xrefs
