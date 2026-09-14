"""prompt_injection_suite — Vulnerability probing for LLMs (§4.4).

Production path:  garak + promptfoo.
Fallback: pure-Python keyword-based injection detection.

Usage
-----
    from src.tools.prompt_injection_suite import prompt_injection_suite
    results = prompt_injection_suite(system_prompt_uri, model_endpoint)"""
from aaa.tools.prompt_injection_suite.fallback import _run_fallback
from aaa.tools.prompt_injection_suite.probe import (  # noqa: F401
    _DANGEROUS_PATTERNS,
    _run_garak,
    logger,
)
from aaa.tools.prompt_injection_suite.run_fallback import prompt_injection_suite

__all__ = [
    'logger',
    '_DANGEROUS_PATTERNS',
    '_run_garak',
    '_run_fallback',
    'prompt_injection_suite',
]
