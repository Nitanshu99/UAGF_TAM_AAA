"""Reading a finished run's artefacts out of the evidence store and off disk.

One place, because the customer dashboard and the admin console fetch the same
files for different audiences and must not disagree about which bytes are the
report.
"""
from __future__ import annotations

from aaa.platform.evidence import EvidenceStore


def customer_pdf(eid: str, final: dict) -> bytes | None:
    """The per-company report PDF written at workflow finish, if present.

    :param eid: Engagement identifier.
    :param final: Final ``AuditState``.
    :returns: PDF bytes, or ``None`` when the customer export did not run.
    """
    from aaa.data.paths import customer_dir
    from aaa.data.writer.atomic import normalized_company_name
    stage_a = (final.get("client_submission") or {}).get("stage_a") or {}
    path = (customer_dir(normalized_company_name(stage_a.get("provider_name")))
            / f"{eid}_audit_report.pdf")
    return path.read_bytes() if path.exists() else None


def rendered(final: dict, store: EvidenceStore) -> dict:
    """The T18 ``rendered_report`` block, or an empty mapping."""
    artefacts = final.get("phase_artefacts") or {}
    t18 = store.get_artefact(artefacts.get("T18_audit_report", {}).get("uri", "")) or {}
    return t18.get("rendered_report", {}) or {}


def report_pdf(final: dict, store: EvidenceStore) -> bytes | None:
    """The rendered report PDF held in the evidence store, if present.

    Used as the fallback when the on-disk customer export is missing, which is
    exactly the case a run whose persistence step failed lands in.

    :param final: Final ``AuditState``.
    :param store: Evidence store holding the rendered artefacts.
    :returns: PDF bytes, or ``None``.
    """
    payload = store.get_artefact(rendered(final, store).get("pdf_uri", "")) or {}
    if payload.get("encoding") != "latin-1":
        return None
    return str(payload.get("body", "")).encode("latin-1")


def client_brief_markdown(final: dict, store: EvidenceStore) -> str | None:
    """The Agent 14 plain-language brief, as Markdown.

    :param final: Final ``AuditState`` holding ``phase_artefacts``.
    :param store: Evidence store the brief was written to.
    :returns: The Markdown body, or ``None`` when no brief was produced.
    """
    from aaa.agents.tier2.client_brief import TEMPLATE_ID
    ref = (final.get("phase_artefacts") or {}).get(TEMPLATE_ID)
    uri = ref.get("uri") if isinstance(ref, dict) else None
    payload = store.get_artefact(uri) if uri else None
    body = (payload or {}).get("body") if isinstance(payload, dict) else None
    return body or None


def template_json(final: dict, store: EvidenceStore, template_id: str) -> dict:
    """Fetch one phase artefact by template id.

    :param final: Final ``AuditState``.
    :param store: Evidence store.
    :param template_id: e.g. ``T17_compliance_matrix``.
    :returns: The artefact payload, or an empty mapping.
    """
    artefacts = final.get("phase_artefacts") or {}
    return store.get_artefact(artefacts.get(template_id, {}).get("uri", "")) or {}
