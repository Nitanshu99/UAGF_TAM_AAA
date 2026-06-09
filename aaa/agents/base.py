import json
import time
from typing import TypedDict, Any, Literal, Optional
from abc import ABC, abstractmethod

import structlog

_logger = structlog.get_logger(__name__)

class IntakeDispatch(TypedDict):
    engagement_id: str
    stage_a_uri: str
    stage_b_uri: str
    stage_c_uri: str
    annex_iv_schema_version: str

class Dispatch(TypedDict):
    phase_id: str
    task_brief: str
    evidence_uris: list[str]
    output_contract: str
    declaration_summary: dict[str, Any]

class Report(TypedDict):
    phase_id: str
    artefact_uri: str
    summary: str
    confidence: float
    tool_calls: list[dict[str, Any]]
    declaration_verification_delta: dict[str, Any]

class Critique(TypedDict):
    phase_id: str
    verdict: Literal["PASS", "FAIL", "NEEDS_REVISION"]
    issues: list[str]
    rerun_required: bool

class BaseAgent(ABC):
    def __init__(self, name: str, model: str, service_tier: Optional[str] = None):
        self.name = name
        self.model = model
        self.service_tier = service_tier

    def _litellm_kwargs(self) -> dict:
        """Return ``model`` (and ``service_tier`` if set) as litellm kwargs."""
        kw: dict = {"model": self.model}
        if self.service_tier is not None:
            kw["service_tier"] = self.service_tier
        return kw

    async def acompletion(self, **kwargs) -> Any:
        """Async LiteLLM call with Flex-aware retry, standard-tier fallback, and full audit logging.

        Merges ``self._litellm_kwargs()`` with any extra *kwargs*, delegates
        to :func:`aaa.platform.flex_retry.flex_acompletion`, and records the
        full request/response/cost to the LLM audit trail.
        """
        from aaa.platform.flex_retry import flex_acompletion
        from aaa.observability.metrics import (
            LLM_CALL_COUNTER,
            LLM_LATENCY_HISTOGRAM,
            LLM_TOKEN_COUNTER,
            LLM_COST_COUNTER,
        )
        import uuid, json as _json
        from pathlib import Path

        call_kwargs = {**self._litellm_kwargs(), **kwargs}
        model = call_kwargs.get("model", self.model)
        messages = call_kwargs.get("messages", [])
        call_id = str(uuid.uuid4())
        t0 = time.perf_counter()

        # ── Write audit record ────────────────────────────────────────────
        def _write_audit(response: Any = None, error: BaseException | None = None) -> None:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
            record: dict[str, Any] = {
                "call_id": call_id,
                "agent": self.name,
                "model": model,
                "messages": messages,
                "latency_ms": elapsed_ms,
                "status": "ok" if error is None else "error",
            }
            if response is not None:
                try:
                    record["response_text"] = response.choices[0].message.content or ""
                    u = response.usage
                    record["prompt_tokens"] = getattr(u, "prompt_tokens", 0) or 0
                    record["completion_tokens"] = getattr(u, "completion_tokens", 0) or 0
                    record["total_tokens"] = getattr(u, "total_tokens", 0) or 0
                except Exception:
                    pass
                try:
                    import litellm as _ll  # type: ignore
                    record["estimated_cost_usd"] = _ll.completion_cost(completion_response=response)
                except Exception:
                    record["estimated_cost_usd"] = None
            if error is not None:
                record["error"] = repr(error)

            audit_path = Path("logs/audit/llm_audit.jsonl")
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            with audit_path.open("a", encoding="utf-8") as fh:
                fh.write(_json.dumps(record, default=str) + "\n")

            status = "ok" if error is None else "error"
            LLM_CALL_COUNTER.labels(agent=self.name, model=model, status=status).inc()
            LLM_LATENCY_HISTOGRAM.labels(agent=self.name, model=model).observe(
                (time.perf_counter() - t0)
            )
            if response is not None:
                for tok_type in ("prompt_tokens", "completion_tokens"):
                    LLM_TOKEN_COUNTER.labels(
                        agent=self.name, model=model, token_type=tok_type
                    ).inc(record.get(tok_type, 0))
                cost = record.get("estimated_cost_usd") or 0.0
                LLM_COST_COUNTER.labels(agent=self.name, model=model).inc(cost)

        response = None
        try:
            response = await flex_acompletion(**call_kwargs)
            _write_audit(response=response)
            return response
        except Exception as exc:
            _write_audit(error=exc)
            raise

    async def acompletion_json(self, prompt_name: str, user_payload: Any, **kwargs) -> dict[str, Any]:
        """Run a prompt-registry-backed completion and parse a JSON response."""
        from aaa.platform.prompt_registry import load_prompt

        messages = [
            {"role": "system", "content": load_prompt(prompt_name)},
            {
                "role": "user",
                "content": json.dumps(user_payload, indent=2, default=str),
            },
        ]
        response_format = kwargs.pop("response_format", {"type": "json_object"})
        response = await self.acompletion(
            messages=messages,
            response_format=response_format,
            **kwargs,
        )
        content = getattr(response.choices[0].message, "content", None) or "{}"
        return json.loads(content)

    def prompt_metadata(
        self,
        prompt_name: str,
        llm_fallback_mode: bool | None = None,
    ) -> dict[str, Any]:
        from aaa.platform.prompt_registry import prompt_version_hash

        metadata: dict[str, Any] = {
            "prompt_source": "PROMPT.md",
            "prompt_version_hash": prompt_version_hash(),
            "agent_prompt": prompt_name,
        }
        if llm_fallback_mode is not None:
            metadata["llm_fallback_mode"] = llm_fallback_mode
        return metadata

    def prompt_note(self, prompt_name: str, llm_fallback_mode: bool) -> str:
        metadata = self.prompt_metadata(prompt_name, llm_fallback_mode)
        return (
            "Prompt metadata: "
            f"source={metadata['prompt_source']}, "
            f"agent_prompt={metadata['agent_prompt']}, "
            f"prompt_version_hash={metadata['prompt_version_hash']}, "
            f"llm_fallback_mode={str(llm_fallback_mode).lower()}."
        )

    @abstractmethod
    async def process(self, message: Any) -> Any:
        pass
