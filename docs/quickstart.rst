Quickstart
==========

Prerequisites
-------------

* Python 3.13
* Docker Desktop (optional — enables Postgres, MinIO, Qdrant, Valkey)
* An LLM API key (optional — deterministic fallbacks run without one)

Install
-------

.. code-block:: bash

   git clone <repo-url> && cd UAGF_TAM_AAA
   make install          # creates .venv and installs all dependencies
   cp .env.example .env  # then edit the values you need

Run everything with one command
-------------------------------

.. code-block:: bash

   make start            # or: .venv/bin/python -m aaa

This starts (as configured in ``.env``): the Docker infrastructure, the
database migrations, the FastAPI backend on port 8000, and the Streamlit
wizard UI on port 8501.

Run a headless audit
--------------------

.. code-block:: bash

   .venv/bin/python -m aaa audit \
       --engagement-id eng-demo-001 \
       --intake-dir scripts/fixtures/uci_german_credit \
       --cgsa-fixture-dir scripts/fixtures/cgsa
