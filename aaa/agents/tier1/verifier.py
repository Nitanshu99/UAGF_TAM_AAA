"""
Verifier — Tier-1 cross-cutting agent (§3.1 #2, §8.1).

Implements the independent critique loop that gates every phase artefact before
it is admitted to the Evidence Store.

Verdict codes:
  accept              – artefact passes all rubric checks; no changes needed.
  accept_with_notes   – minor issues noted; artefact admitted but annotations
                        appended to the verifier_critique record.
  rerun               – significant issues; Orchestrator re-dispatches the phase
                        agent (max MAX_RERUNS before escalation).
  escalate_hitl       – artefact cannot be admitted automatically; human-in-the-
                        loop review required.

Rubric checks (four dimensions per §8.1):
  1. factual_accuracy      – claims are grounded in admitted evidence URIs.
  2. completeness          – all required sections are present and non-empty.
  3. evidence_linkage      – every assertion references at least one artefact URI.
  4. citation_correctness  – every regulatory citation is well-formed and in scope.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Literal

from aaa.agents.base import BaseAgent
from aaa.platform.model_registry import resolve_model, resolve_service_tier
from aaa.platform.prompt_registry import load_prompt
from aaa.platform.token_guard import (
    BudgetExceededError,
    compute_budget,
    ensure_within_budget,
)
from aaa.tools.evidence_truncate import truncate_payload

logger = logging.getLogger(__name__)

MAX_RERUNS = 2

VerifierVerdict = Literal["accept", "accept_with_notes", "rerun", "escalate_hitl"]


class VerifierError(Exception):
    """Raised when the Verifier encounters an unrecoverable configuration error."""


class Verifier(BaseAgent):
    """
    Independent Verifier agent.

    Parameters
    ----------
    model:
        LLM model string passed to LiteLLM / Anthropic.  Defaults to
        Claude Opus for maximum critique rigour.
    """

    def __init__(self, model: str | None = None, service_tier: str | None = None):
        super().__init__(
            name="Verifier",
            model=resolve_model("Verifier", model),
            service_tier=resolve_service_tier("Verifier", service_tier),
        )
        self._offline: bool = (
            os.environ.get("AAA_OFFLINE_MODE", "false").lower() == "true"
        )

    # ------------------------------------------------------------------
    # BaseAgent protocol
    # ------------------------------------------------------------------

    async def process(self, message: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        """
        Critique a single phase artefact.

        Parameters
        ----------
        message : dict with keys:
            phase_id    – e.g. "P1", "P2", …
            template_id – e.g. "T02_system_card"
            content     – the artefact payload (dict or str)
            evidence_uris – list[str] of previously admitted artefact URIs
            rerun_count – int; number of times this artefact has been rerun

        Returns
        -------
        dict (VerifierCritique) with keys:
            phase_id, template_id, verdict, issues, notes,
            article_citations, rerun_required
        """
        phase_id: str = message.get("phase_id", "")
        template_id: str = message.get("template_id", "")
        content: Any = message.get("content", {})
        evidence_uris: list[str] = message.get("evidence_uris", [])
        rerun_count: int = int(message.get("rerun_count", 0))

        if self._offline:
            return self._offline_critique(
                phase_id, template_id, content, evidence_uris, rerun_count
            )

        return await self._llm_critique(
            phase_id, template_id, content, evidence_uris, rerun_count
        )

    # ------------------------------------------------------------------
    # Offline / deterministic critique (CI + demo)
    # ------------------------------------------------------------------

    def _offline_critique(
        self,
        phase_id: str,
        template_id: str,
        content: Any,
        evidence_uris: list[str],
        rerun_count: int,
    ) -> dict[str, Any]:
        """
        Deterministic rubric checks that run without an LLM.

        Applied checks:
          - content is non-empty
          - content is a dict (schema-valid JSON object)
          - at least one evidence URI is referenced
        """
        issues: list[str] = []
        notes: list[str] = []

        if not content:
            issues.append("Artefact content is empty.")
        if isinstance(content, dict) and len(content) == 0:
            issues.append("Artefact payload is an empty dict.")
        if not evidence_uris:
            notes.append("No evidence URIs provided; linkage cannot be verified offline.")

        verdict = self._decide_verdict(issues, notes, rerun_count)
        return {
            "phase_id": phase_id,
            "template_id": template_id,
            "verdict": verdict,
            "issues": issues,
            "notes": notes,
            "article_citations": [],
            "scores": {},
            "total_score": None,
            "materiality_assessments": [],
            "declaration_mismatches": [],
            "llm_fallback_mode": True,
            "prompt_metadata": self.prompt_metadata("verifier", True),
            "rerun_required": verdict == "rerun",
        }

    # ------------------------------------------------------------------
    # LLM-backed critique
    # ------------------------------------------------------------------

    async def _llm_critique(
        self,
        phase_id: str,
        template_id: str,
        content: Any,
        evidence_uris: list[str],
        rerun_count: int,
    ) -> dict[str, Any]:  # pragma: no cover
        """Call the LLM for a structured four-dimension critique."""
        try:
            content_str = (
                json.dumps(content, indent=2)
                if isinstance(content, dict)
                else str(content)
            )
            messages = _build_critique_messages(
                phase_id, template_id, content_str, evidence_uris
            )
            try:
                ensure_within_budget(self.model, messages=messages)
            except BudgetExceededError as exc:
                logger.warning(
                    "Prompt for %s/%s exceeds budget (%d > %d); truncating evidence.",
                    phase_id, template_id, exc.prompt_tokens, exc.budget,
                )
                content_str, messages = self._truncate_for_budget(
                    phase_id, template_id, content, evidence_uris
                )
                ensure_within_budget(self.model, messages=messages)
            resp = await self.acompletion(
                messages=messages,
                response_format={"type": "json_object"},
            )
            raw = json.loads(resp.choices[0].message.content)
            issues = _normalise_issues(raw.get("issues", []))
            notes = raw.get("notes", [])
            article_citations = raw.get("article_citations", [])
            materiality_assessments = raw.get("materiality_assessments", [])
            declaration_mismatches = raw.get("declaration_mismatches", [])
            scores = raw.get("scores", {})
            total_score = raw.get("total_score")
            verdict = _map_llm_verdict(raw.get("verdict"), issues, notes, rerun_count)
        except Exception as exc:
            logger.warning("LLM critique failed (%s); applying offline fallback.", exc)
            return self._offline_critique(
                phase_id, template_id, content, evidence_uris, rerun_count
            )

        return {
            "phase_id": phase_id,
            "template_id": template_id,
            "verdict": verdict,
            "issues": issues,
            "notes": notes,
            "article_citations": article_citations,
            "scores": scores,
            "total_score": total_score,
            "materiality_assessments": materiality_assessments,
            "declaration_mismatches": declaration_mismatches,
            "llm_fallback_mode": False,
            "prompt_metadata": self.prompt_metadata("verifier", False),
            "rerun_required": verdict == "rerun",
        }

    # ------------------------------------------------------------------
    # Evidence truncation (oversized-prompt recovery)
    # ------------------------------------------------------------------

    def _truncate_for_budget(
        self,
        phase_id: str,
        template_id: str,
        content: Any,
        evidence_uris: list[str],
    ) -> tuple[str, list[dict[str, str]]]:
        """Compress *content* with :func:`truncate_payload` and rebuild messages."""
        if not isinstance(content, dict):
            content_str = str(content)
            return content_str, _build_critique_messages(
                phase_id, template_id, content_str, evidence_uris
            )
        budget = compute_budget(self.model)
        # Estimate overhead from the system message + fixed user-message framing
        overhead_msgs = _build_critique_messages(phase_id, template_id, "", evidence_uris)
        from aaa.platform.token_guard import count_tokens  # local to avoid circular
        overhead_tokens = count_tokens(self.model, messages=overhead_msgs)
        payload_budget = max(1, budget - overhead_tokens)
        result = truncate_payload(
            content,
            query=f"{phase_id} {template_id}",
            model=self.model,
            max_tokens=payload_budget,
            preserve_keys=("engagement_id", "generated_at"),
        )
        content_str = json.dumps(result.to_dict(), indent=2)
        messages = _build_critique_messages(
            phase_id, template_id, content_str, evidence_uris
        )
        return content_str, messages

    # ------------------------------------------------------------------
    # Verdict logic
    # ------------------------------------------------------------------

    @staticmethod
    def _decide_verdict(
        issues: list[str],
        notes: list[str],
        rerun_count: int,
    ) -> VerifierVerdict:
        """
        Translate rubric findings into a verdict code.

        Rules
        -----
        - No issues, no notes          → accept
        - No issues, notes present     → accept_with_notes
        - Issues present, reruns left  → rerun
        - Issues present, reruns spent → escalate_hitl
        """
        if not issues:
            return "accept_with_notes" if notes else "accept"
        if rerun_count < MAX_RERUNS:
            return "rerun"
        return "escalate_hitl"


# ---------------------------------------------------------------------------
# Prompt builder (used by LLM path only)
# ---------------------------------------------------------------------------
#
# The static rubric, reasoning procedure, security policy and output contract
# live in ``_SYSTEM_PROMPT`` so that the prefix is byte-identical across every
# Verifier call.  This (a) lets the model server reuse cached key/value state
# (OpenAI auto-prefix-cache ≥ 1024 tokens, Anthropic ``cache_control``) and
# (b) keeps untrusted artefact content out of the instruction surface, where
# it could otherwise be mistaken for a directive.
#
# Per-call variability (phase, template, evidence list, artefact body) is
# placed in the *user* message inside XML tags that the system prompt
# explicitly designates as DATA, not instructions.


_SYSTEM_PROMPT = load_prompt("verifier")


def _normalise_issues(raw_issues: Any) -> list[str]:
    if not isinstance(raw_issues, list):
        return []
    issues: list[str] = []
    for item in raw_issues:
        if isinstance(item, str):
            issues.append(item)
        elif isinstance(item, dict):
            description = item.get("description") or item.get("issue") or item.get("field")
            if description:
                issues.append(str(description))
        elif item is not None:
            issues.append(str(item))
    return issues


def _map_llm_verdict(
    raw_verdict: Any,
    issues: list[str],
    notes: list[str],
    rerun_count: int,
) -> VerifierVerdict:
    if isinstance(raw_verdict, str):
        verdict = raw_verdict.strip().upper()
        if verdict == "ACCEPT":
            return "accept"
        if verdict == "ACCEPT_WITH_OBSERVATIONS":
            return "accept_with_notes"
        if verdict == "RERUN":
            return "rerun" if rerun_count < MAX_RERUNS else "escalate_hitl"
        if verdict == "ESCALATE_HITL":
            return "escalate_hitl"
    return Verifier._decide_verdict(issues, notes, rerun_count)


def _build_critique_messages(
    phase_id: str,
    template_id: str,
    content_str: str,
    evidence_uris: list[str],
) -> list[dict[str, str]]:
    """Return a ``[system, user]`` message pair for ``litellm.acompletion``."""
    try:
        artefact_payload: Any = json.loads(content_str)
    except Exception:
        artefact_payload = content_str
    user_content = json.dumps(
        {
            "review_request": {
                "phase_id": phase_id,
                "template_id": template_id,
                "artefact_uri": "",
                "artefact_payload": artefact_payload,
                "declaration_summary": {},
                "prior_critique": None,
                "evidence_uris": evidence_uris,
            }
        },
        indent=2,
        default=str,
    )
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
