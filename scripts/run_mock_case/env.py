"""Process bootstrap: repo paths, .env loading, CGSA fixture wiring."""
from __future__ import annotations

import os
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
AUDIT_LOG = REPO_ROOT / "logs" / "audit" / "llm_audit.jsonl"

#: Stage B fields that reference client-uploaded documents.  These must live
#: in the EvidenceStore (MinIO) as ``minio://`` URIs for client_doc_ingest to
#: index them; raw local paths are silently skipped by the ingester.
DOC_FIELDS = (
    "risk_management_file_uri",
    "post_market_plan_uri",
    "eu_doc_uri",
    "system_prompt_uri",
    "rag_manifest_uri",
    "guardrail_config_uri",
    "golden_set_uri",
)


def load_dotenv_file(path: pathlib.Path) -> None:
    """Load ``.env`` into ``os.environ`` (shell env wins); LiteLLM reads os.environ."""
    if not path.exists():
        return
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(path, override=False)
        return
    except Exception:  # pylint: disable=broad-exception-caught
        pass
    for raw in path.read_text("utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def bootstrap(case_dir: pathlib.Path) -> None:
    """Prepare the process *before* any ``aaa`` import (env is read at import time).

    :param case_dir: The mock case folder (``mock/<case>``).
    """
    os.chdir(REPO_ROOT)
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    load_dotenv_file(REPO_ROOT / ".env")
    # A real run persists its evidence (P9). ``setdefault`` after the .env load
    # so a deliberate EVIDENCE_BACKEND in the shell or in .env still wins; what
    # it removes is the *silent* default, which is memory and is right only for
    # a unit test. ``aaa.settings`` reads the environment at import time, so
    # like CGSA_FIXTURE_DIR below this has to happen before importing aaa.
    os.environ.setdefault("EVIDENCE_BACKEND", "minio")
    # Auto-wire the correct CGSA fixture for this case. cgsa_pull reads
    # CGSA_FIXTURE_DIR at import time, so this must happen before importing aaa.
    # An explicit value wins, on the same reasoning as EVIDENCE_BACKEND above:
    # it is how a case is re-run against a real S5 export, which is confidential
    # and therefore lives outside the repo rather than in `mock/`.
    cgsa = case_dir / "cgsa"
    if cgsa.is_dir():
        # M21: this used to defer to an existing CGSA_FIXTURE_DIR, and `.env`
        # ships one (`scripts/fixtures/cgsa`), so the per-case wiring never ran.
        # Case 06's assessment lives only in `mock/06_.../cgsa/`, so Phase 5
        # pulled `fixture_not_found`, T14/T15 came back empty, and Art. 5, 9,
        # 12, 17, 50 and 72 lost the CGSA findings that carry their verdicts —
        # Art. 5 silently became PASS. The case's own fixture is the more
        # specific answer and now wins; an explicit override is still possible
        # through AAA_CGSA_FIXTURE_DIR.
        os.environ["CGSA_FIXTURE_DIR"] = os.environ.get(
            "AAA_CGSA_FIXTURE_DIR") or str(cgsa)


def unbuffer_output() -> None:
    """Make this process's stdout/stderr line-buffered (finding Q10).

    Python block-buffers stdout when it is not a tty, so a run whose output is
    piped or redirected — which is how a 5,000-second run is watched — printed
    nothing until it exited. The preflight line exists to be read *before* the
    run spends anything, and *"watch the per-phase progress logs below…"* is an
    invitation the buffer made impossible to accept.

    Idempotent, and a no-op on a stream that cannot be reconfigured (a captured
    ``StringIO`` under pytest, for instance).
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(line_buffering=True)  # type: ignore[union-attr]
        except (AttributeError, ValueError):  # not a reconfigurable TextIOWrapper
            continue
