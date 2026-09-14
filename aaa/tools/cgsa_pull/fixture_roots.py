"""Where the CGSA fixtures live, and finding one by assessment id."""
from __future__ import annotations

import os

#: Read at import for backwards compatibility only. Callers should use
#: :func:`fixture_roots`, which re-reads the environment on every call — the CLI
#: assigns ``os.environ["CGSA_FIXTURE_DIR"]`` while parsing its arguments, which
#: is after this module may already have been imported.
_FIXTURE_DIR = os.environ.get("CGSA_FIXTURE_DIR")
#: How deep a root is walked looking for ``{assessment_id}.json``. The mock
#: bundles put theirs at ``mock/<case>/cgsa/<id>.json`` — two levels down.
_FIXTURE_SEARCH_DEPTH = 3
def fixture_roots(explicit: str | None = None) -> list[str]:
    """Directories to search for a CGSA fixture, in order.

    This generalises A14 (finding M21) to the entry points that do not go
    through ``scripts/run_mock_case``. A14 fixed the mock-case runner, which
    wires ``CGSA_FIXTURE_DIR`` to the case's own ``cgsa/`` before importing
    ``aaa``; the Streamlit wizard has no such bootstrap and no
    ``--cgsa-fixture-dir`` flag, so it took whatever ``.env`` shipped — which is
    the very situation M21 describes, one door over. On 2026-09-11 a wizard run
    of case 06 pulled ``fixture_not_found``, T14/T15 came back empty, and Art. 5
    silently became PASS: M21's symptoms exactly.

    Two conventions are inherited from A14 rather than reinvented:

    * ``AAA_CGSA_FIXTURE_DIR`` is the explicit override, and wins outright — it
      is how a case is re-run against a real S5 export held outside the repo;
    * where a case ships its own fixture, that is the more specific answer and
      should be listed before any shared directory.

    :param explicit: A directory (or path-separated list) overriding both.
    :returns: Existing directories, in search order.
    """
    if explicit is None:
        explicit = os.environ.get("AAA_CGSA_FIXTURE_DIR") or None
    raw = explicit if explicit is not None else os.environ.get("CGSA_FIXTURE_DIR", "")
    return [part for part in str(raw or "").split(os.pathsep)
            if part and os.path.isdir(part)]
def _find_fixture(assessment_id: str, roots: list[str]) -> str | None:
    """Locate ``{assessment_id}.json`` under any configured root.

    Tried directly in each root first — the layout
    ``scripts/fixtures/cgsa/<id>.json`` has always used — then by a bounded walk,
    which is what finds ``mock/06_mariposa_edu_gmbh/cgsa/<id>.json`` without the
    caller having to name that directory.

    :param assessment_id: The assessment the dossier declares.
    :param roots: Directories to search.
    :returns: The file path, or ``None``.
    """
    wanted = f"{assessment_id}.json"
    # Each root is exhausted — direct hit, then walk — before the next is tried.
    # Doing every direct hit first would defeat the ordering: `mock` holds its
    # assessments at `mock/<case>/cgsa/<id>.json`, never at the root, so a
    # shared directory listed second would still win every time. That matters
    # because four assessments exist in both places and have drifted.
    for root in roots:
        direct = os.path.join(root, wanted)
        if os.path.exists(direct):
            return direct
        base_depth = root.rstrip(os.sep).count(os.sep)
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.count(os.sep) - base_depth >= _FIXTURE_SEARCH_DEPTH:
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if not d.startswith((".", "__"))]
            if wanted in filenames:
                return os.path.join(dirpath, wanted)
    return None


__all__ = ["_FIXTURE_DIR", "_FIXTURE_SEARCH_DEPTH", "_find_fixture", "fixture_roots"]
