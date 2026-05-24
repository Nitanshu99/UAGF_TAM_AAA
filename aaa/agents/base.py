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
    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model

    @abstractmethod
    async def process(self, message: Any) -> Any:
        pass
