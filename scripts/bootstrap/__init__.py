"""Stage 2 of ``python bootstrap.py`` — everything after the virtualenv.

Runs inside ``.venv`` (stage 1, :mod:`scripts.bootstrap.venv_stage`, put it
there) and takes a fresh clone the rest of the way::

    python -m scripts.bootstrap [--openrouter-key ...] [--mock-llm] [--no-run]

Steps, continuing stage 1's count:

3. Docker (CLI, Compose v2, running daemon) and the two bundles in the root.
4. ``.env`` — created from ``.env.example`` when missing; OpenRouter is set as
   the one provider for agents *and* embeddings, vendor placeholders blanked,
   Langfuse provisioned with generated keys on a fresh file.
5. ``mariposa.zip`` → ``mock/06_mariposa_edu_gmbh/``; ``corpus.zip`` → ``data/``.
6. ``docker compose --profile obs --profile ui up -d --wait``, then Alembic.
7. ``playwright install chromium``.
8. The regulatory corpus into Qdrant, unless it is already there from the
   same embedder (a corpus built by another one is rebuilt).
9. The FastAPI backend and the Streamlit wizard, health-checked.
10. One Chromium window: every service dashboard in a tab, the wizard in
    front, filled from the bundle and dispatched; held open afterwards.

``--mock-llm`` runs the same path without spending anything: a local stub
serves embeddings (deterministic vectors) and refuses chat, so the agents take
their deterministic fallbacks. Its corpus is stamped with the stub's host and
is rebuilt automatically on the next real run.
"""
