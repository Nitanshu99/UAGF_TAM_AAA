from typing import TypedDict, Any, Literal, Optional
from abc import ABC, abstractmethod

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
        """Async LiteLLM call with Flex-aware retry and standard-tier fallback.

        Merges ``self._litellm_kwargs()`` with any extra *kwargs* and delegates
        to :func:`aaa.platform.flex_retry.flex_acompletion`, which applies:

        * A 600 s timeout when ``service_tier="flex"`` is set.
        * Exponential backoff on ``429 / RateLimitError`` (up to
          ``FLEX_MAX_RETRIES`` attempts).
        * Automatic fallback to the standard tier if Flex is persistently
          unavailable, so audits are never silently stalled.
        """
        from aaa.platform.flex_retry import flex_acompletion
        call_kwargs = {**self._litellm_kwargs(), **kwargs}
        return await flex_acompletion(**call_kwargs)

    @abstractmethod
    async def process(self, message: Any) -> Any:
        pass
