"""The organisation and system tokens an assessment filename is matched on."""
from __future__ import annotations

import re

_TOKEN = re.compile(r"[a-z0-9]+")
#: Dropped before comparing organisation names. "Acme Analytics GmbH" and
#: "Acme Analytics" are the same company; a customer typing one of them into the
#: wizard should not miss an assessment filed under the other.
_LEGAL_FORMS = frozenset({
    "gmbh", "ug", "ag", "kg", "ohg", "se", "ev", "ltd", "limited", "plc",
    "llp", "inc", "llc", "corp", "co", "company", "bv", "nv", "sa", "sas",
    "sarl", "srl", "spa", "ab", "as", "aps", "oy", "oyj", "sp", "zoo",
})
#: Dropped before comparing system names: the CGSA records "CreditScore v1.0.0"
#: where the wizard asks for name and version in separate fields.
_VERSION = re.compile(r"^v?\d+([._]\d+)*$")
def _org_tokens(text: str) -> frozenset[str]:
    """Normalise an organisation name to comparable tokens."""
    return frozenset(t for t in _TOKEN.findall(str(text or "").lower())
                     if t not in _LEGAL_FORMS)
def _system_tokens(text: str) -> frozenset[str]:
    """Normalise a system name to comparable tokens, version stripped."""
    return frozenset(t for t in _TOKEN.findall(str(text or "").lower())
                     if not _VERSION.match(t))


__all__ = ["_LEGAL_FORMS", "_TOKEN", "_VERSION", "_org_tokens", "_system_tokens"]
