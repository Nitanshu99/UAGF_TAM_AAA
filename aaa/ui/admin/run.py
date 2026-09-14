"""The run record: what identifies this audit and what it cost to trust it."""
from __future__ import annotations

import html

import streamlit as st

from aaa.ui.styles import section_title

#: run_integrity / AuditState field → the label a reviewer scans for.
_FIELDS: tuple[tuple[str, str], ...] = (
    ("run_id", "Run id"),
    ("code_revision", "Code revision"),
    ("generated_at", "Completed"),
    ("artefact_count", "Artefacts produced"),
)


def _rows(pairs: list[tuple[str, str]]) -> str:
    """Render a definition table."""
    return "".join(
        f"<tr><td style='color:var(--text-3);inline-size:38%'>{html.escape(k)}</td>"
        f"<td><code>{html.escape(v)}</code></td></tr>" for k, v in pairs)


def render_run_record(final: dict, integrity: dict) -> None:
    """Render run identity plus the phase and escalation record.

    :param final: Final ``AuditState`` dictionary.
    :param integrity: The run's ``run_integrity`` block.
    """
    section_title("Run record",
                  "What to quote when this audit is questioned, and what the "
                  "pipeline itself reported about the run.")
    pairs = [(label, str(integrity.get(key) or final.get(key) or "—"))
             for key, label in _FIELDS]
    pairs.append(("Report signed", "yes" if final.get("report_signed") else "no"))
    if final.get("signature_withheld"):
        pairs.append(("Signature withheld", str(final["signature_withheld"])))
    st.markdown('<div class="aaa-card aaa-scroll-x aaa-rise">'
                f'<table class="aaa-matrix"><tbody>{_rows(pairs)}</tbody></table></div>',
                unsafe_allow_html=True)
    _phase_status(final)


def _phase_status(final: dict) -> None:
    """Show per-phase status when the orchestrator recorded it."""
    status = final.get("phase_status") or {}
    if not isinstance(status, dict) or not status:
        return
    with st.expander(f"Phase status ({len(status)})", expanded=False):
        st.json(status)
