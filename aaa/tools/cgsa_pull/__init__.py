"""cgsa_pull — HTTP client that fetches the S4 CGSA payload (§4.5, §10.2).

The S4 team owns a FastAPI endpoint exposing the assessment JSON:

    GET  {S4_CGSA_BASE_URL}/api/v1/assessments/{assessment_id}
         Header: X-Schema-Version

This tool wraps that pull with:
  * exponential back-off (5 attempts, 1–32 s) for 5xx / network errors,
  * a 404 → ``CGSAPullError("not_found")`` to surface as a HITL trigger,
  * a pinned ``X-Schema-Version`` check against ``CGSA_SCHEMA_VERSION``.

Fixture mode (``CGSA_FIXTURE_DIR`` set) reads the payload from
``{CGSA_FIXTURE_DIR}/{assessment_id}.json`` instead of issuing HTTP — used
by the Streamlit demo, unit tests, and CI.

``discover`` answers the question that precedes the pull — *which*
assessment belongs to this client — so no customer is ever asked to quote
an id that S4 minted and never showed them."""
from aaa.tools.cgsa_pull.core import cgsa_pull  # noqa: F401
from aaa.tools.cgsa_pull.discover import discover_assessments
from aaa.tools.cgsa_pull.fetch_once import _fetch_once  # noqa: F401
from aaa.tools.cgsa_pull.fixture_roots import _FIXTURE_DIR, _find_fixture, fixture_roots
from aaa.tools.cgsa_pull.logger import (
    _BACKOFF_BASE_SECONDS,
    _DEFAULT_BASE_URL,
    _MAX_ATTEMPTS,
    _PINNED_SCHEMA_VERSION,
    CGSAPullError,
    _read_fixture,
    logger,
)
from aaa.tools.cgsa_pull.narrow import resolve_assessment_id
from aaa.tools.cgsa_pull.pull_http import _pull_http  # noqa: F401

__all__ = [
    'logger', '_PINNED_SCHEMA_VERSION', '_DEFAULT_BASE_URL', '_FIXTURE_DIR', '_MAX_ATTEMPTS',
    '_BACKOFF_BASE_SECONDS', 'CGSAPullError', '_read_fixture', 'fixture_roots', '_find_fixture', '_fetch_once', '_pull_http',
    'cgsa_pull', 'discover_assessments', 'resolve_assessment_id',
]
