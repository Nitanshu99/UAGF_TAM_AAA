# syntax=docker/dockerfile:1.7
# AAA FastAPI service image — referenced by docker-compose.prod.yml (aaa_api).
#
# The dependency set is heavy (torch, sentence-transformers, shap) because the
# agents run explainability and robustness probes in-process; expect a
# multi-GB image and a long first build. Layers are ordered so that a code
# change does not reinstall dependencies.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libpq5 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt constraints.txt ./
RUN pip install --upgrade pip \
 && pip install -r requirements.txt -c constraints.txt

# PROMPT.md is read at import time by aaa.platform.prompt_registry — without
# it every agent module fails to import and the container exits on start.
COPY pyproject.toml alembic.ini PROMPT.md ./
COPY aaa ./aaa
COPY alembic ./alembic
COPY schemas ./schemas
COPY templates ./templates
COPY scripts ./scripts
COPY packages ./packages
RUN pip install --no-deps -e . \
 && useradd --system --uid 10001 --create-home aaa \
 && mkdir -p /app/logs/metrics /app/data \
 && chown -R aaa:aaa /app

USER aaa
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3).status == 200 else 1)"

CMD ["python", "-m", "uvicorn", "aaa.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
