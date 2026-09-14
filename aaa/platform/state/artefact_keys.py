"""Artefact-key namespacing for tier-3 spawns (finding P5).

``phase_artefacts`` is keyed by template id and ``_apply_delta`` merges each
report's delta with ``dict.update``.  That is right for a phase re-dispatched
after a ``rerun`` verdict: the same agent re-emits the same template, and the
newer artefact *is* the phase's answer.  It is wrong for a tier-3 spawn, which
emits a **second** T08 or T11 beside the phase's own.  The key collides, the
spawn's copy wins, and the Verifier's critique — written against the phase's
copy — stays attached to a template id that no longer names the artefact it
judged.  The post-fix run shows exactly that: ``T08`` stored under ``Privacy/``
with a Phase 2 ``escalate_hitl`` critique, ``T11`` under ``CyberSecurity/``
with a Phase 3 ``rerun`` critique, and neither phase's artefact readable any
more.

The key space gains one shape: ``<template_id>@<spawn>``.  The artefact still
declares its own ``template_id`` and still validates against that schema — only
the *slot* differs.  Every consumer that keys on an exact template id
(``_TEMPLATE_ARTICLES``, ``phase_status``, the completeness expectation,
``_supporting_tids``) therefore keeps reading the phase's artefact, which is the
one the phase was contracted to deliver and the one that was critiqued, while
the spawn's contribution stays in evidence under a key of its own.
"""
from __future__ import annotations

from typing import Any

#: Separator between a template id and the spawn that produced a variant of it.
#: ``@`` appears in no template id, so ``key.split`` is unambiguous.
SPAWN_SEPARATOR: str = "@"

#: Spawn names used by the two tier-3 sub-agents.
SPAWN_CYBER: str = "Cyber"
SPAWN_PRIVACY: str = "Privacy"


def namespaced_key(template_id: str, spawn: str) -> str:
    """Return the ``phase_artefacts`` key a *spawn* writes for *template_id*.

    :param template_id: The template the spawn extends, e.g. ``T11_robustness_report``.
    :param spawn: The spawn's short name, e.g. ``Cyber``.
    :returns: ``"<template_id>@<spawn>"``; *template_id* unchanged when *spawn*
        is empty, so a caller with nothing to namespace by cannot silently
        produce a key ending in a bare separator.
    """
    if not spawn:
        return template_id
    if is_namespaced(template_id):
        return template_id
    return f"{template_id}{SPAWN_SEPARATOR}{spawn}"


def is_namespaced(key: str) -> bool:
    """Return True when *key* already carries a spawn namespace."""
    return SPAWN_SEPARATOR in key


def base_template_id(key: str) -> str:
    """Return the template id *key* names, with any spawn namespace stripped.

    Consumers that want to know *which template* an artefact is — the HITL
    packet's phase lookup, a reader of ``embedded_artefacts`` — ask this rather
    than re-deriving the split.
    """
    return key.split(SPAWN_SEPARATOR, 1)[0]


def namespace_artefacts(artefacts: dict[str, Any], spawn: str) -> dict[str, Any]:
    """Return *artefacts* re-keyed into *spawn*'s namespace.

    Applied at the delta boundary rather than trusted to the agent: whatever a
    spawn emits, it cannot land on a bare template id and displace the phase's
    own artefact.  Each ref keeps (or gains) a ``template_id`` naming the schema
    it validates against, so the namespaced key never becomes the artefact's
    claimed identity.

    :param artefacts: A delta's ``phase_artefacts`` block.
    :param spawn: The spawn's short name.
    :returns: A new dict keyed by namespaced ids.
    """
    out: dict[str, Any] = {}
    for key, ref in (artefacts or {}).items():
        new_key = namespaced_key(key, spawn)
        if isinstance(ref, dict):
            ref = {**ref, "template_id": ref.get("template_id") or base_template_id(key)}
        out[new_key] = ref
    return out


__all__ = [
    "SPAWN_SEPARATOR", "SPAWN_CYBER", "SPAWN_PRIVACY",
    "namespaced_key", "is_namespaced", "base_template_id", "namespace_artefacts",
]
