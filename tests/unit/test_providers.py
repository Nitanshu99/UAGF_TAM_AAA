"""Unit tests for the S6/S7 provider factories, internal adapters, and HTTP clients."""
from __future__ import annotations

import httpx
import pytest
import respx

from aaa.integrations.base import ProviderError
from aaa.integrations.security import (
    ExternalSecurityProvider,
    InternalSecurityProvider,
    select_security_provider,
)
from aaa.integrations.xai import ExternalXAIProvider, InternalXAIProvider, select_xai_provider
from aaa.settings import AAASettings

_STATE = {"engagement_id": "eng-x", "phase_artefacts": {
    "T10_explainability_report": {"uri": "minio://x/t10"},
    "T12_output_fairness_report": {"uri": "minio://x/t12"},
    "T11_robustness_report": {"uri": "minio://x/t11"}}}


def _cfg(**env: str) -> AAASettings:
    """Build settings from explicit values, ignoring the repo .env."""
    return AAASettings(_env_file=None, **env)  # pyright: ignore[reportCallIssue]


def test_factories_default_internal() -> None:
    """Default settings select the internal adapters."""
    assert isinstance(select_xai_provider(_cfg()), InternalXAIProvider)
    assert isinstance(select_security_provider(_cfg()), InternalSecurityProvider)


def test_factories_switch_independently() -> None:
    """S6 external does not flip S7, and vice versa."""
    cfg = _cfg(S6_XAI_MODE="external")
    assert isinstance(select_xai_provider(cfg), ExternalXAIProvider)
    assert isinstance(select_security_provider(cfg), InternalSecurityProvider)


def test_internal_adapters_package_artefact_refs() -> None:
    """Internal evidence carries the artefact references and source marker."""
    xai = InternalXAIProvider().evaluate(_STATE)
    assert xai["evidence_source"] == "internal"
    assert xai["explainability_report"] == {"uri": "minio://x/t10"}
    sec = InternalSecurityProvider().evaluate(_STATE)
    assert sec["robustness_report"] == {"uri": "minio://x/t11"}


@respx.mock
def test_external_xai_posts_handoff_and_parses_evidence() -> None:
    """External mode POSTs the versioned hand-off and returns the evidence."""
    route = respx.post("http://s6.example/api/v1/evaluate").mock(
        return_value=httpx.Response(200, json={"fairness": {"dp_diff": 0.03}}))
    evidence = ExternalXAIProvider("http://s6.example", "tok").evaluate(_STATE)
    assert evidence == {"fairness": {"dp_diff": 0.03}, "evidence_source": "external"}
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer tok"
    assert b'"handoff_schema_version"' in request.content


@respx.mock
def test_external_security_not_found_raises_provider_error() -> None:
    """A 404 from the security service fails immediately with ProviderError."""
    respx.post("http://s7.example/api/v1/evaluate").mock(
        return_value=httpx.Response(404))
    with pytest.raises(ProviderError) as excinfo:
        ExternalSecurityProvider("http://s7.example").evaluate(_STATE)
    assert excinfo.value.reason == "not_found"
