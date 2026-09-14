"""The packaged schemas are the templates the pipeline validates against, byte for byte.

``packages/uagf_tam_templates`` drifted from ``templates/`` in both directions: the
package lacked T01a ``organisation_contacts`` and T18 ``auditor_opinion``, while
``templates/`` lacked the T10 techniques ``token_importance`` and
``feature_snapshot`` that the code emits (T-20260913-020). ``templates/`` is the
source; the package ships a copy.
"""
from __future__ import annotations

from pathlib import Path

TEMPLATES = Path("templates")
PACKAGED = Path("packages/uagf_tam_templates/src/uagf_tam_templates/schemas")


def test_every_template_is_packaged_identically() -> None:
    """Same set of schemas, same bytes."""
    source = {p.name: p.read_bytes() for p in TEMPLATES.glob("T*.json")}
    packaged = {p.name: p.read_bytes() for p in PACKAGED.glob("T*.json")}
    assert sorted(source) == sorted(packaged)
    assert [name for name in source if source[name] != packaged[name]] == []


def test_the_client_brief_has_a_contract() -> None:
    """T19 was stored with no template, so the store-time check said nothing (T-20260913-022)."""
    from aaa.agents.tier2.client_brief.constants import TEMPLATE_ID
    from aaa.platform.evidence.contract import artefact_schema_errors

    body = "# Brief\n\nArticle 9 — fails."
    content = {"format": "markdown", "body": body, "bytes_size": len(body.encode("utf-8"))}
    assert artefact_schema_errors(TEMPLATE_ID, content) == []
    assert artefact_schema_errors(TEMPLATE_ID, {"format": "markdown", "body": ""})
