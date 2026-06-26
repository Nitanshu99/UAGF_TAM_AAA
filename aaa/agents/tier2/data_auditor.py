"""
DataAuditor — Tier-2 Phase 2 Data Governance Auditor (§3.2 #5).

Receives a ``Dispatch`` from the Orchestrator containing intake artefact URIs
and performs the following workflow:

  1. Load dataset reference from the Annex IV dossier (T01b) — URI or in-memory.
  2. Call ``data_profile`` → dataset_summary.
  3. Call ``missingness_scan`` → per-column missingness rates.
  4. Call ``class_balance`` → class distribution + imbalance flag.
  5. Call ``pii_scan`` → PII entities + special-category detection.
  6. Build T06 datasheet from declaration_summary + Annex IV §2 fields.
  7. Determine overall quality verdict.
  8. Build T08 if special_category_data detected or declared.
  9. Write T06, T07, T08 to the Evidence Store.
  10. Emit ``Report`` with ``declaration_verification_delta`` updating
      ``special_category_data`` if PII scan overrides declaration.

LLM path:
  - Production: Claude Sonnet via LiteLLM (``AAA_OFFLINE_MODE=false``).
  - Offline: deterministic rule-based path only.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from aaa.agents.base import BaseAgent, Dispatch, Report
from aaa.platform.artifact_loader import ArtifactUnavailable, load_artifact_from_uri
from aaa.platform.evidence import EvidenceStore
from aaa.tools.class_balance import class_balance
from aaa.tools.client_doc_ingest import client_doc_search
from aaa.tools.data_dictionary import resolve_data_dictionary
from aaa.tools.data_profile import data_profile
from aaa.tools.findings import make_finding
from aaa.tools.missingness_scan import missingness_scan
from aaa.tools.pii_scan import pii_scan

logger = logging.getLogger(__name__)

_OFFLINE = os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"
_PROMPT_NAME = "phase2_data"


class DataAuditorError(Exception):
    """Raised when a hard gate blocks Phase 2."""

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(f"[DataAuditor] {reason}")


class DataAuditor(BaseAgent):
    """
    Phase 2 — Data Governance Auditor.

    Verifies data quality, completeness, and special-category-data handling
    against EU AI Act Art. 10 requirements.  Emits T06, T07, T08 artefacts.
    """

    def __init__(
        self,
        evidence_store: EvidenceStore,
        model: str | None = None,
        service_tier: str | None = None,
    ):
        from aaa.platform.model_registry import resolve_model, resolve_service_tier
        super().__init__(
            name="DataAuditor",
            model=resolve_model("DataAuditor", model),
            service_tier=resolve_service_tier("DataAuditor", service_tier),
        )
        self.store = evidence_store

    # ------------------------------------------------------------------
    # BaseAgent protocol
    # ------------------------------------------------------------------

    async def process(self, message: Dispatch) -> Report:  # type: ignore[override]
        """
        Run Phase 2 data governance audit and return a Report.

        Parameters
        ----------
        message : Dispatch
            Must include ``declaration_summary`` with at minimum
            ``engagement_id``, ``modality``, ``special_category_data``.
            ``evidence_uris`` should include T01a and T01b URIs.

        Returns
        -------
        Report
            ``artefact_uri`` points to T06 (datasheet).
            ``declaration_verification_delta`` carries updated
            ``special_category_data`` if PII scan found undeclared
            special categories.
        """
        decl = message.get("declaration_summary", {})
        engagement_id: str = decl.get("engagement_id") or message["phase_id"]
        declared_special_cat: bool = bool(decl.get("special_category_data", False))
        target_col: str | None = decl.get("target_column")
        stage_b: dict[str, Any] = decl.get("stage_b") or {}

        findings: list[dict[str, Any]] = []
        insufficient: set[str] = set()

        # ── 1. Load intake bundle + the REAL dataset ─────────────────────────
        t01a, t01b = self._load_intake(message.get("evidence_uris", []))
        df, dataset_finding = self._load_dataset(t01b, decl)
        if dataset_finding:
            findings.append(dataset_finding)

        data_available = df is not None and len(df) > 0
        if data_available and not target_col:
            # Resolve target silently; Phase 3 owns the data-dictionary findings.
            target_col = resolve_data_dictionary(
                stage_b or t01b, list(df.columns)
            ).target_column

        df_for_tools = df if df is not None else self._empty_frame()

        # ── 2–5. Run analysis tools on the real data ─────────────────────────
        profile_result = data_profile(df_for_tools, target_column=target_col)
        miss_result = missingness_scan(df_for_tools)
        balance_result = class_balance(df_for_tools, target_column=target_col)
        pii_result = pii_scan(df_for_tools)

        # ── 6. Detect special-category override ───────────────────────────────
        pii_special_cat = pii_result.get("special_category_data_detected", False)
        effective_special_cat = declared_special_cat or pii_special_cat
        special_cat_delta = pii_special_cat and not declared_special_cat  # undeclared!

        # ── 7. Determine overall quality verdict (grounded in real data) ─────
        if not data_available:
            verdict = "INSUFFICIENT_EVIDENCE"
            insufficient.update({"Art.10", "Art.10§2(f)"})
        else:
            verdict = self._quality_verdict(miss_result, balance_result, pii_result)
            findings.extend(self._verdict_findings(verdict, miss_result, balance_result, pii_result))
            findings.extend(self._diff_declared_data(stage_b or t01b, profile_result))
        if special_cat_delta:
            findings.append(make_finding(
                finding_id="P2-SPECIAL-CAT",
                description="PII scan detected undeclared special-category data in the dataset.",
                materiality="material",
                articles=["Art.10"],
                source_phase="P2",
                recommendation="Declare special-category data and document the Art. 10 §5 lawful basis.",
            ))

        # ── 8. Build artefacts ────────────────────────────────────────────────
        now = datetime.now(timezone.utc).isoformat()
        client_doc_hits: list[dict[str, Any]] = []
        if decl.get("client_doc_collection"):
            client_doc_hits = client_doc_search(
                engagement_id,
                "data governance training data quality missingness class balance PII policy",
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
                        or "Execute Phase 2 data governance audit per the Phase 2 Protocol.",
                        "evidence_uris": message.get("evidence_uris", []),
                        "declaration_summary": decl,
                        "client_doc_hits": client_doc_hits,
                        "rerun_context": None,
                        "tool_outputs": {
                            "profile_result": profile_result,
                            "missingness": miss_result,
                            "class_balance": balance_result,
                            "pii_scan": pii_result,
                            "overall_quality_verdict": verdict,
                        },
                    },
                )
                llm_fallback_mode = False
            except Exception as exc:
                logger.warning("DataAuditor prompt runtime failed (%s); using deterministic fallback.", exc)
        prompt_note = self.prompt_note(_PROMPT_NAME, llm_fallback_mode)
        llm_summary = llm_payload.get("summary") or llm_payload.get("rationale_summary")

        t06 = self._build_t06(engagement_id, t01a, t01b, decl, now)
        t07 = self._build_t07(engagement_id, profile_result, miss_result,
                              balance_result, pii_result, verdict, now)
        t08 = self._build_t08(engagement_id, effective_special_cat,
                              pii_result, special_cat_delta, now)
        t06["art10_compliance_notes"] = f"{t06['art10_compliance_notes']} {prompt_note}".strip()
        t07["quality_narrative"] = f"{llm_summary or t07['quality_narrative']} {prompt_note}".strip()
        t08["compliance_narrative"] = f"{t08['compliance_narrative']} {prompt_note}".strip()

        # ── 9. Store artefacts ────────────────────────────────────────────────
        t06_uri = self.store.store_artefact(
            engagement_id, "phase_2", "T06_datasheet_for_datasets", t06, self.name)
        t07_uri = self.store.store_artefact(
            engagement_id, "phase_2", "T07_data_quality_report", t07, self.name)
        t08_uri = self.store.store_artefact(
            engagement_id, "phase_2", "T08_special_category_data_log", t08, self.name)

        # ── 10. Emit Report ───────────────────────────────────────────────────
        material = any(f.get("materiality") == "material" for f in findings)
        confidence = 0.85 if not (special_cat_delta or material or insufficient) else 0.6

        delta: dict[str, Any] = {
            "phase_artefacts": {
                "T06_datasheet_for_datasets": {
                    "uri": t06_uri, "sha256": "", "template_id": "T06_datasheet_for_datasets"},
                "T07_data_quality_report": {
                    "uri": t07_uri, "sha256": "", "template_id": "T07_data_quality_report"},
                "T08_special_category_data_log": {
                    "uri": t08_uri, "sha256": "", "template_id": "T08_special_category_data_log"},
            },
        }
        if findings:
            delta["blocking_findings"] = findings
        if insufficient:
            delta["insufficient_evidence_articles"] = sorted(insufficient)
        if special_cat_delta:
            delta["special_category_data"] = True
            delta["privacy_tier3_triggered"] = True
        if special_cat_delta or material or insufficient:
            reasons = []
            if special_cat_delta:
                reasons.append("undeclared special-category data detected (Privacy Tier-3 spawn)")
            if material:
                reasons.append("material data-governance finding(s) raised")
            if insufficient:
                reasons.append("dataset could not be independently verified: " + ", ".join(sorted(insufficient)))
            delta["hitl_required"] = True
            delta["hitl_reason"] = "Phase 2 — " + "; ".join(reasons) + "."

        return Report(
            phase_id="P2",
            artefact_uri=t06_uri,
            summary=(
                llm_summary
                or
                f"Phase 2 complete. quality_verdict={verdict}, "
                f"pii_detected={pii_result['pii_detected']}, "
                f"special_category_data={effective_special_cat}, "
                f"imbalance={balance_result['imbalance_detected']}."
            ),
            confidence=confidence,
            tool_calls=[
                {"tool": "data_profile",
                 "result": f"rows={profile_result['num_rows']}, cols={profile_result['num_columns']}"},
                {"tool": "missingness_scan",
                 "result": f"overall={miss_result['overall_missingness_pct']:.1f}%"},
                {"tool": "class_balance",
                 "result": f"imbalance={balance_result['imbalance_detected']}"},
                {"tool": "pii_scan",
                 "result": f"entities={len(pii_result['entities_found'])}"},
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

    def _load_dataset(
        self, t01b: dict, decl: dict
    ) -> tuple[Any, dict[str, Any] | None]:
        """Load the real training/evaluation dataset for independent analysis.

        Returns ``(dataframe_or_None, finding_or_None)``. Unlike the previous
        implementation, a missing/unreadable dataset returns ``None`` plus a
        finding — never a silent empty frame that would let the data-governance
        checks pass on no evidence.
        """
        stage_b = decl.get("stage_b") or t01b or {}
        dataset_uri = (
            t01b.get("training_dataset_uri")
            or stage_b.get("training_dataset_uri")
            or t01b.get("evaluation_dataset_uri")
            or stage_b.get("evaluation_dataset_uri")
            or decl.get("dataset_uri")
        )
        if not dataset_uri:
            return None, make_finding(
                finding_id="P2-DATA-MISSING",
                description="No training/evaluation dataset URI supplied; data quality and "
                            "governance could not be independently verified.",
                materiality="possibly_material",
                articles=["Art.10"],
                source_phase="P2",
                recommendation="Supply a dataset URI in the Annex IV dossier.",
            )
        try:
            kind = "parquet" if dataset_uri.lower().endswith(".parquet") else "csv"
            df = load_artifact_from_uri(dataset_uri, self.store, kind)
            return df, None
        except ArtifactUnavailable as exc:
            return None, make_finding(
                finding_id="P2-DATA-LOAD",
                description=f"Training/evaluation dataset could not be loaded for "
                            f"independent verification: {exc.reason}.",
                materiality="possibly_material",
                articles=["Art.10"],
                source_phase="P2",
                recommendation="Provide a machine-readable dataset (CSV/Parquet).",
            )

    def _quality_verdict(
        self,
        miss_result: dict,
        balance_result: dict,
        pii_result: dict,
    ) -> str:
        """Derive overall quality verdict from tool results."""
        issues = []
        if miss_result.get("high_missingness_columns"):
            issues.append("high_missingness")
        if balance_result.get("imbalance_severity") in {"moderate", "severe"}:
            issues.append("class_imbalance")
        if pii_result.get("entities_found"):
            severities = {e["severity"] for e in pii_result["entities_found"]}
            if "critical" in severities:
                return "FAIL"
            if "high" in severities:
                issues.append("pii_high_severity")

        if not issues:
            return "PASS"
        return "PASS_WITH_OBSERVATIONS"

    @staticmethod
    def _empty_frame() -> Any:
        """Return an empty DataFrame (or duck-typed stub) for tool calls."""
        try:
            import pandas as pd  # type: ignore
            return pd.DataFrame()
        except ImportError:
            return _EmptyDataFrame()

    def _verdict_findings(
        self,
        verdict: str,
        miss_result: dict,
        balance_result: dict,
        pii_result: dict,
    ) -> list[dict[str, Any]]:
        """Translate the quality verdict into Art. 10 findings."""
        if verdict == "FAIL":
            return [make_finding(
                finding_id="P2-DQ-FAIL",
                description="Critical data-quality / PII issue detected in the training data.",
                materiality="material",
                articles=["Art.10"],
                source_phase="P2",
                recommendation="Remediate the dataset before the system can be considered compliant.",
            )]
        if verdict == "PASS_WITH_OBSERVATIONS":
            issues = []
            if miss_result.get("high_missingness_columns"):
                issues.append("high missingness columns")
            if balance_result.get("imbalance_severity") in {"moderate", "severe"}:
                issues.append(f"class imbalance ({balance_result.get('imbalance_severity')})")
            if any(e.get("severity") == "high" for e in pii_result.get("entities_found", [])):
                issues.append("high-severity PII present")
            return [make_finding(
                finding_id="P2-DQ-OBS",
                description="Data-quality observations: " + (", ".join(issues) or "minor issues") + ".",
                materiality="possibly_material",
                articles=["Art.10"],
                source_phase="P2",
                recommendation="Address the noted data-quality observations.",
            )]
        return []

    def _diff_declared_data(
        self,
        dossier: dict,
        profile_result: dict,
    ) -> list[dict[str, Any]]:
        """Light-touch diff of declared dataset description vs the real data.

        Conservative on purpose: only the feature-count check, which is stable
        across train/eval splits, to avoid false positives from row-count
        differences between the training and evaluation partitions.
        """
        import re
        desc = str(dossier.get("training_data_description") or "")
        findings: list[dict[str, Any]] = []
        num_cols = profile_result.get("num_columns")
        m = re.search(r"(\d+)\s*attribute", desc, re.IGNORECASE)
        if m and isinstance(num_cols, int) and num_cols > 0:
            declared_attrs = int(m.group(1))
            # The dataset includes the target column; features = columns - 1.
            actual_features = max(num_cols - 1, 0)
            if abs(declared_attrs - actual_features) > 1:
                findings.append(make_finding(
                    finding_id="P2-DATA-DIFF-ATTRS",
                    description=(
                        f"Declared {declared_attrs} attributes but the supplied dataset has "
                        f"{actual_features} feature columns."
                    ),
                    materiality="possibly_material",
                    articles=["Art.10", "Art.11"],
                    source_phase="P2",
                    recommendation="Reconcile the Annex IV dataset description with the supplied data.",
                    declared=declared_attrs,
                    observed=actual_features,
                ))
        return findings

    # ── Artefact builders ──────────────────────────────────────────────────

    def _build_t06(
        self,
        engagement_id: str,
        t01a: dict,
        t01b: dict,
        decl: dict,
        now: str,
    ) -> dict:
        """Build T06 Datasheet for Datasets from available dossier fields."""
        provider = t01a.get("provider_name", decl.get("provider_name", "Unknown"))
        training_desc = t01b.get("training_data_description", "Not provided.")
        preprocessing_desc = t01b.get("preprocessing_description")
        num_instances = t01b.get("training_dataset_size")

        return {
            "engagement_id": engagement_id,
            "motivation": {
                "purpose": t01b.get("intended_purpose", t01a.get("intended_purpose",
                    "AI system training dataset — purpose inherited from system card.")),
                "creators": provider,
                "funding_sources": t01b.get("funding_sources", "Not disclosed."),
                "gap_filled": None,
            },
            "composition": {
                "instances_type": training_desc,
                "num_instances": int(num_instances) if num_instances else 0,
                "num_features": None,
                "has_labels": True,
                "label_description": t01b.get("label_description"),
                "sensitive_features": [],
                "missing_data_present": False,
                "missing_data_description": None,
                "confidential_data": bool(t01a.get("special_category_data", False)),
                "relationships_to_other_datasets": None,
            },
            "collection_process": {
                "acquisition_method": t01b.get("data_acquisition_method",
                    "Not documented — see Annex IV §2."),
                "collection_timeframe": t01b.get("collection_timeframe"),
                "consent_obtained": bool(t01a.get("gdpr_overlap", False)),
                "consent_mechanism": t01b.get("consent_mechanism"),
                "notification_given": None,
                "third_party_sources": t01b.get("third_party_data_sources"),
                "collection_ethical_review": None,
            },
            "preprocessing_cleaning_labelling": {
                "preprocessing_performed": preprocessing_desc is not None,
                "preprocessing_description": preprocessing_desc,
                "labelling_performed": t01b.get("labelling_performed", False),
                "labelling_description": t01b.get("labelling_description"),
                "label_validation": None,
                "raw_data_available": None,
                "software_used": None,
            },
            "uses": {
                "intended_tasks": t01a.get("intended_purpose",
                    "High-risk AI system training — see system card."),
                "prior_publications": None,
                "prohibited_tasks": (
                    "Must not be used for purposes outside the declared intended purpose "
                    "or in violation of EU AI Act Art. 5 prohibitions."
                ),
                "impact_on_subpopulations": None,
                "other_known_uses": None,
            },
            "distribution": {
                "distribution_method": "Internal — not publicly distributed.",
                "access_url": None,
                "licence": t01b.get("data_licence", "Not disclosed."),
                "ip_restrictions": None,
                "regulatory_restrictions": (
                    "GDPR applies." if t01a.get("gdpr_overlap") else None
                ),
                "export_controls": None,
            },
            "maintenance": {
                "maintainer": provider,
                "contact": None,
                "update_plan": "Not documented — to be addressed in remediation.",
                "errata_process": None,
                "retention_period": None,
                "version": t01a.get("version"),
            },
            "art10_compliance_notes": (
                "Datasheet populated from Annex IV dossier fields. "
                "Phase 2 DataAuditor — Art. 10 §2–§3."
            ),
            "generated_at": now,
        }

    def _build_t07(
        self,
        engagement_id: str,
        profile_result: dict,
        miss_result: dict,
        balance_result: dict,
        pii_result: dict,
        verdict: str,
        now: str,
    ) -> dict:
        """Build T07 Data Quality Report from tool outputs."""
        return {
            "engagement_id": engagement_id,
            "dataset_summary": profile_result,
            "missingness": miss_result,
            "class_balance": balance_result,
            "drift": {
                "reference_dataset_uri": None,
                "drift_detected": None,
                "drifted_columns": [],
                "drift_share": None,
                "test_method": None,
            },
            "pii_scan": pii_result,
            "overall_quality_verdict": verdict,
            "quality_narrative": (
                f"Data quality assessed via automated tools. "
                f"Missingness overall: {miss_result.get('overall_missingness_pct', 0):.1f}%. "
                f"Class imbalance: {balance_result.get('imbalance_severity', 'none')}. "
                f"PII detected: {pii_result.get('pii_detected', False)}. "
                f"Overall verdict: {verdict}."
            ),
            "generated_at": now,
        }

    def _build_t08(
        self,
        engagement_id: str,
        special_cat_present: bool,
        pii_result: dict,
        undeclared_special_cat: bool,
        now: str,
    ) -> dict:
        """Build T08 Special Category Data Log."""
        categories = pii_result.get("special_categories_found", [])
        hitl_required = undeclared_special_cat

        entries = []
        for cat in categories:
            entries.append(
                {
                    "special_category": cat,
                    "lawful_basis": "ai_act_art10_5_statistical_correction",
                    "basis_reference": "EU AI Act Art. 10 §5 — bias correction.",
                    "dpa_consultation_required": True,
                    "dpia_conducted": None,
                    "dpia_reference": None,
                    "data_minimisation_confirmed": None,
                    "retention_period": None,
                }
            )

        return {
            "engagement_id": engagement_id,
            "special_category_data_present": special_cat_present,
            "special_categories_detected": categories,
            "lawful_basis_entries": entries,
            "art10_5_statistical_correction_applies": len(entries) > 0,
            "statistical_correction_rationale": (
                "Special-category data retained under Art. 10 §5 for bias correction."
                if entries else None
            ),
            "privacy_tier3_triggered": special_cat_present,
            "hitl_review_required": hitl_required,
            "hitl_review_reason": (
                "Undeclared special-category data detected by PII scan. "
                "Human review required before processing continues."
                if hitl_required else None
            ),
            "compliance_narrative": (
                f"Special-category data {'present' if special_cat_present else 'absent'}. "
                f"Categories: {categories or 'none'}. "
                f"Art. 10 §5 / GDPR Art. 9 review {'required' if entries else 'not applicable'}."
            ),
            "generated_at": now,
        }


# ---------------------------------------------------------------------------
# Minimal duck-typed empty DataFrame for no-pandas environments
# ---------------------------------------------------------------------------

class _EmptyDataFrame:
    """Ultra-minimal DataFrame stub for environments without pandas."""

    def __init__(self) -> None:
        self.columns: list[str] = []
        self.shape: tuple[int, int] = (0, 0)

    def __len__(self) -> int:
        return 0

    def head(self, n: int) -> "_EmptyDataFrame":
        return self

    def memory_usage(self, deep: bool = False) -> Any:
        return _ZeroSeries()

    def duplicated(self) -> Any:
        return _ZeroSeries()


class _ZeroSeries:
    def sum(self) -> int:
        return 0
