"""The client's prior governance self-assessment — derived, never asked for.

S4 files a CGSA against an organisation and a system, and mints the assessment
id itself; the organisation never sees that id. Asking the customer to type it
into the wizard, as step 3 used to, was therefore a field only this repository
could fill. Both names it is filed under are already on the form, so the lookup
belongs here.
"""
from __future__ import annotations

import streamlit as st

from aaa.tools.cgsa_pull import CGSAPullError, cgsa_pull, resolve_assessment_id
from aaa.tools.cgsa_pull.compat import payload_profile

#: Seconds a lookup is reused for. Step 3 re-runs on every keystroke and the
#: search walks the configured CGSA roots, so the result is held briefly; a
#: fixture added mid-session is picked up on the next expiry.
_TTL_SECONDS = 300


@st.cache_data(show_spinner=False, ttl=_TTL_SECONDS)
def lookup_assessment_id(organisation: str, system: str) -> str | None:
    """Find the assessment filed for these names, if exactly one exists.

    :param organisation: Legal provider name.
    :param system: System name.
    :returns: The assessment id, or ``None``.
    """
    return resolve_assessment_id(organisation, system)


def prior_assessment_id() -> str | None:
    """The assessment on file for the names currently in the wizard.

    A session value wins where one exists: the API and CLI declare the id
    directly, and a declaration is a stronger statement than a name match.

    :returns: The assessment id, or ``None`` if none or several matched.
    """
    s = st.session_state
    return (s.get("s3_a_cgsa_assessment_id")
            or lookup_assessment_id(str(s.get("s3_a_provider_name") or ""),
                                    str(s.get("s3_a_system_name") or ""))
            or None)


@st.cache_data(show_spinner=False, ttl=_TTL_SECONDS)
def _profile(assessment_id: str) -> dict | None:
    """What the named assessment can support, or ``None`` if it cannot be read."""
    try:
        return payload_profile(cgsa_pull(assessment_id=assessment_id))
    except CGSAPullError:
        return None


def prior_assessment_profile() -> dict | None:
    """Describe the assessment this run would attach, if there is one.

    :returns: The :func:`~aaa.tools.cgsa_pull.compat.payload_profile` of the
        resolved assessment, or ``None`` when none resolves or it cannot be
        pulled.
    """
    assessment_id = prior_assessment_id()
    return _profile(assessment_id) if assessment_id else None
