# UPDATE.md — AAA Gap-Fix Implementation Plan

> **Who runs this file**: An AI coding agent (e.g. Claude, Codex, GPT-4o in agentic mode).  
> **What it does**: Closes the backend, evidence, corpus, customer upload, and report-delivery gaps identified against the exposé and Big 4 quality bar.  
> **What it does NOT do**: Change LLM chat models, rename agents, alter the 12-agent topology
> defined in `ARCHITECTURE.md`, or turn the demo into a broad product portal. Every task is additive — no existing behaviour is deleted.
>
> **Before you start, read these four files in full**:  
> 1. `ARCHITECTURE.md` — canonical design reference  
> 2. `aaa/platform/state.py` — `AuditState` and all nested TypedDicts  
> 3. `PROMPT.md` — canonical LLM multi-agent prompt specification  
> 4. `templates/` directory listing — 20 JSON Schema files (T01a–T18)

---

## Rules for the Implementing Agent

1. **One task at a time.** Complete all steps of a task, run its success check, then move to the next.
2. **Never change an LLM chat model name.** `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.4-nano` stay as-is everywhere.
3. **Never delete existing fields.** Only add new fields, new files, or new code blocks.
4. **Run the success check** listed at the end of every task before moving on. If it fails, fix it before proceeding.
5. **Preserve TypedDict `total=False`** where it already exists in `state.py`. New optional fields use `Optional[X]` with default `None`.
6. **Tasks marked `[PARALLEL]`** have no dependency on each other and can be implemented in any order or simultaneously.
7. **Tasks marked `[DEPENDS: TASK-XXX]`** must be started only after the listed task's success check has passed.
8. **Embedding model consistency.** All dense embedding calls in this repo must use OpenAI `text-embedding-3-large` with 3072-dimensional vectors unless a task explicitly proves otherwise. Do not introduce `text-embedding-3-small`.
9. **Corpus source location.** Regulatory corpus source files live in `data/regulatory_corpus/`. Do not add `scripts/corpus_sources/`.
10. **Customer workflow is in scope.** The target customer journey is intentionally simple: upload required documents and optional model/data artefacts, run the audit, and download the generated report. Add only the UI/API work needed for that flow; do not build dashboards, account management, billing, chat, or other product-portal features.
11. **Use `PROMPT.md` as the prompt source of truth.** Apply it through a prompt registry/runtime; do not leave prompts as disconnected documentation. Agent implementations must invoke the LLM path in normal operation and reserve deterministic/rule-only behaviour for explicit offline/CI fallback.

---

## Task Execution Order

```
TASK-000  ──────────────────────────────────────────────────────────►  run first
TASK-001  [DEPENDS: TASK-000]  ──────────────────────────────────────►
TASK-002  [PARALLEL with 000]  ──────────────────────────────────────►
TASK-003  [DEPENDS: TASK-000, PARALLEL with 001 and 002]  ───────────►
TASK-004  [PARALLEL with 001, 002, 003]  ────────────────────────────►
TASK-005  [DEPENDS: TASK-004]  ──────────────────────────────────────►
TASK-006  [DEPENDS: TASK-003]  ──────────────────────────────────────►
TASK-007  [PARALLEL with 006, DEPENDS: TASK-003]  ──────────────────►
TASK-008  [DEPENDS: TASK-002, TASK-003, TASK-006, TASK-007]  ────────►
TASK-009  [PARALLEL — no dependencies]  ─────────────────────────────►
TASK-010  [PARALLEL — no dependencies]  ─────────────────────────────►
TASK-011  [DEPENDS: TASK-001]  ───────────────────────────────────────►
```

---

## TASK-000 — Apply PROMPT.md to the LLM Multi-Agent Runtime

**Closes gaps**: P1 (`PROMPT.md` not applied in code), P2 (phase agents are too deterministic/manual), P3 (prompt updates not propagated to agent runtime)  
**Prerequisites**: None  
**Parallel-safe**: No — this is foundational for all prompt-aware agent tasks

### Context

`PROMPT.md` is now the canonical LLM multi-agent prompt specification. The current repo
contains several deterministic agent implementations and one in-code verifier prompt, but
no prompt registry/runtime that applies `PROMPT.md` across the agent graph. The system must
operate as a multi-agent LLM audit pipeline in normal mode: deterministic tools compute
measurements and render artefacts, while LLM agents interpret evidence, decide findings,
and emit schema-conformant Reports.

### Steps

#### Step 1 — Add a prompt registry

Create `aaa/platform/prompt_registry.py`.

It must expose:

```python
def load_prompt(agent_name: str) -> str: ...
def prompt_version_hash() -> str: ...
```

The registry may either parse bounded sections from `PROMPT.md` or load generated static
prompt constants copied from `PROMPT.md`, but `PROMPT.md` must remain the human-readable
source of truth. Include prompts for at least:

- `orchestrator`
- `verifier`
- `regulatory_rag`
- `phase1_scope`
- `phase2_data`
- `phase3_model`
- `phase4_output`
- `phase5_governance`
- `phase6_report`
- `tier3_specialist`
- `hitl_escalation`

#### Step 2 — Apply registry prompts in agent code

Update agent implementations so normal online execution calls `BaseAgent.acompletion(...)`
with the registry-provided system prompt and engagement-specific user payload. Do not
hard-code the same full prompt text in multiple agent files.

At minimum, wire prompts into:

- `aaa/agents/tier1/verifier.py`
- `aaa/agents/tier2/scope_agent.py`
- `aaa/agents/tier2/data_auditor.py`
- `aaa/agents/tier2/model_validator.py`
- `aaa/agents/tier2/output_evaluator.py`
- `aaa/agents/tier2/governance_agent.py`
- `aaa/agents/tier2/report_architect.py`

Deterministic calculations/tool calls may remain, but their results must be provided to
the LLM agent for audit judgement and report synthesis. Offline mode may use existing
fallbacks, but fallback artefacts must include a clear note such as
`"llm_fallback_mode": true` or equivalent metadata.

#### Step 3 — Preserve model registry usage

Do not change chat model names. Use `aaa/platform/model_registry.py` as the source for
agent model/service-tier configuration. Prompt text must not hard-code model names.

#### Step 4 — Add prompt-version metadata to artefacts

For each agent-generated Report/artefact, include prompt metadata where schemas allow it,
for example:

```json
"prompt_metadata": {
  "prompt_source": "PROMPT.md",
  "prompt_version_hash": "<sha256>",
  "agent_prompt": "phase2_data"
}
```

If a schema does not allow this field, include the metadata in the existing evidence/tool
summary field instead of breaking schema validation.

#### Step 5 — Enforce no hidden chain-of-thought output

Agents may reason privately, but outputs must not include hidden chain-of-thought,
`<scratchpad>` blocks, or raw prompt text. Outputs should include concise
`rationale_summary`, issue rationales, and source references only.

#### Step 6 — Add tests

Add focused tests for:

- prompt registry loads every required agent prompt
- `prompt_version_hash()` changes when `PROMPT.md` changes
- verifier prompt includes materiality requirements
- phase prompts include client-document RAG protocol where required
- report architect prompt includes auditor-opinion protocol

### Success Check

```bash
python3 -m pytest tests/unit/test_prompt_registry.py

python3 - <<'PY'
from aaa.platform.prompt_registry import load_prompt, prompt_version_hash

required = [
    'orchestrator', 'verifier', 'regulatory_rag', 'phase1_scope', 'phase2_data',
    'phase3_model', 'phase4_output', 'phase5_governance', 'phase6_report',
    'tier3_specialist', 'hitl_escalation',
]
for name in required:
    prompt = load_prompt(name)
    assert isinstance(prompt, str) and len(prompt) > 200, name
assert 'materiality' in load_prompt('verifier')
assert 'client_doc_search' in load_prompt('phase1_scope')
assert 'client_doc_search' in load_prompt('phase2_data')
assert 'client_doc_search' in load_prompt('phase3_model')
assert 'client_doc_search' in load_prompt('phase5_governance')
assert 'AUDITOR OPINION PROTOCOL' in load_prompt('phase6_report')
assert len(prompt_version_hash()) == 64
print('TASK-000 OK')
PY
```

---

## TASK-001 — Per-Engagement Client Document RAG Pipeline

**Closes gaps**: E2 (RAG for client document parsing), B7 (client document RAG)  
**Prerequisites**: TASK-000  
**Parallel-safe**: Yes

### Context

Currently, `Stage B` collects Annex IV §1–§9 data as structured JSON fields in
`AnnexIVDossier` (defined in `aaa/platform/state.py`). Several fields already store
MinIO URIs pointing to uploaded files:

- `risk_management_file_uri` — Art. 9 risk management file (PDF or DOCX)
- `post_market_plan_uri` — Annex IV §9 post-market plan
- `eu_doc_uri` — EU declaration of conformity
- `system_prompt_uri` — L-branch: system prompt document
- `rag_manifest_uri` — L-branch: RAG configuration
- `guardrail_config_uri` — L-branch: guardrail config
- `golden_set_uri` — L-branch: Q&A evaluation set

Phase agents currently ignore these URIs and only read the structured JSON fields.
The fix creates a per-engagement Qdrant collection that indexes these documents,
and adds a `client_doc_search` tool so agents can retrieve evidence from actual
client documents instead of relying solely on declared form values.

### Steps

#### Step 1 — Create the ingestion tool

Create a new file: `aaa/tools/client_doc_ingest.py`

This file must define one function: `client_doc_ingest(engagement_id: str, doc_uris: list[str], store: EvidenceStore | None = None) -> dict`

The function must do the following in order:
1. For each URI in `doc_uris`, load the document bytes/content. In the current repo `aaa/platform/evidence.py` is an in-memory `EvidenceStore`, not a real MinIO client: when `store` is provided, use `store.get_artefact(uri)` for `minio://...` URIs; when a production MinIO client is later available, keep that behind the same helper. Do not invent a new storage root.
2. Determine the file type from the URI extension (`.pdf`, `.docx`, `.txt`, `.json`, `.md`).
3. Extract plain text from the file:
   - For `.pdf`: use `pypdfium2` (already in `requirements.txt`) — same library used by `scripts/ingest_regulatory_corpus.py`. Extract text page by page.
   - For `.docx`: use `python-docx` — add `python-docx>=1.1` to `requirements.txt` if not present.
   - For `.txt`, `.md`, `.json`: read as UTF-8 string directly.
4. Split each document's text into chunks of 400 tokens with 50-token overlap. Use a simple character-based splitter (every 1600 characters = approx 400 tokens at 4 chars/token). Preserve page numbers for PDFs where available. Do not use LlamaIndex here — keep it simple and dependency-free.
5. For each chunk, generate an embedding using OpenAI `text-embedding-3-large` (3072 dimensions). Use `openai.OpenAI().embeddings.create(...)`; do not use LiteLLM chat-completion plumbing and do not use `text-embedding-3-small`.
6. Create a Qdrant collection named `client_docs_{engagement_id}` (replace any hyphens in `engagement_id` with underscores). The collection must use cosine similarity and 3072-dimensional vectors (matching `text-embedding-3-large`).
7. Upsert all chunk vectors into this collection. Each vector's payload must include enough metadata for the top-3 chunks passed to an LLM to be traceable back to the exact client document:

```json
{
  "text": "<chunk text>",
  "engagement_id": "<engagement_id>",
  "source_uri": "<original EvidenceStore/MinIO URI>",
  "source_filename": "<basename if known>",
  "source_sha256": "<sha256 of original bytes/text>",
  "content_type": "pdf|docx|txt|json|md",
  "document_role": "risk_management_file|post_market_plan|eu_declaration|system_prompt|rag_manifest|guardrail_config|golden_set|unknown",
  "page_number": 1,
  "section_hint": "<heading or JSON path if available>",
  "chunk_index": 0,
  "chunk_total": 1,
  "char_start": 0,
  "char_end": 1600
}
```

Use `null` for page/section values that cannot be extracted. Do not store a bare text-only payload.
8. Return `{"collection_name": "client_docs_{engagement_id}", "chunks_indexed": <total int>, "sources": [<list of URIs processed>]}`.

The function must be idempotent: if the collection already exists, skip re-embedding documents whose `source_uri` is already present (check via `qdrant_client.scroll` before upserting).

#### Step 2 — Create the search tool

Add a second function to `aaa/tools/client_doc_ingest.py`: `client_doc_search(engagement_id: str, query: str, top_k: int = 3) -> list[dict]`

This function must:
1. Embed `query` using `text-embedding-3-large`.
2. Search the `client_docs_{engagement_id}` collection in Qdrant for the top `top_k` results.
3. Return a list of dicts: `[{"text": "<chunk>", "source_uri": "<MinIO URI>", "source_sha256": "...", "document_role": "...", "page_number": 1, "section_hint": "...", "chunk_index": 0, "chunk_total": 7, "score": <float>}]`.
4. If the collection does not exist (engagement has no ingested documents), return an empty list — never raise an exception.

#### Step 3 — Wire ingestion into the Intake Validator

Open `aaa/agents/intake_validator.py`.

Find the point where Stage B processing completes (where `T01c` is written and `intake_completeness_score` is calculated).

After that point, add a call to `client_doc_ingest` with:
- `engagement_id` from `AuditState.engagement_id`
- `doc_uris` = all non-None URI fields from `AnnexIVDossier`: collect `risk_management_file_uri`, `post_market_plan_uri`, `eu_doc_uri`, `system_prompt_uri`, `rag_manifest_uri`, `guardrail_config_uri`, `golden_set_uri`. Filter out `None` values.
- `store=self.store`, because the current `EvidenceStore` is the only storage abstraction available in this repo.

If `doc_uris` is empty (client uploaded no files, only filled text fields), skip ingestion silently.

Store the returned `collection_name` in `AuditState` (see Step 4).

#### Step 4 — Add field to AuditState

Open `aaa/platform/state.py`.

In the `AuditState` TypedDict, add one new field after the `engagement_id` field:

```python
client_doc_collection: Optional[str]  # Qdrant collection name for per-engagement client docs; None if no docs uploaded
```

Import `Optional` from `typing` if not already imported.

#### Step 5 — Wire search into prompt-driven backend agents

`aaa/tools/__init__.py` is currently empty; TASK-000 adds prompt runtime but not a full dynamic tool-calling framework. Wire `client_doc_search` explicitly in the backend agents that need it, and ensure the corresponding `PROMPT.md` sections list the tool and describe when to use it.

Import and call `client_doc_search` in the following agents when `declaration_summary.get("client_doc_collection")` is present, then include the returned chunks in the LLM user payload so the agent can reason over actual uploaded documents:
- `aaa/agents/tier2/scope_agent.py` — declaration verification and Annex III evidence
- `aaa/agents/tier2/data_auditor.py` — data governance policies / dataset documentation
- `aaa/agents/tier2/model_validator.py` — model architecture, training, evaluation, robustness documentation
- `aaa/agents/tier2/governance_agent.py` — monitoring, logging, post-market, QMS, and risk-management documents

Do NOT add it to: Verifier, Regulatory RAG, Phase 4, Phase 6, Tier-3 agents unless a later task explicitly updates `PROMPT.md` and the prompt registry for those agents.

#### Step 6 — Update Dispatch messages to include collection name

Open `aaa/agents/tier1/orchestrator.py`.

`Dispatch.evidence_uris` is a `list[str]` in `aaa/agents/base.py`. Do **not** change it into a dict. In each backend phase dispatch, keep `evidence_uris` as the existing T01a/T01b URI list and add client-document retrieval metadata to `declaration_summary`, like this:

```python
"evidence_uris": evidence_uris,
"declaration_summary": {
    ...existing fields...,
    "engagement_id": state["engagement_id"],
    "client_doc_collection": state.get("client_doc_collection"),
}
```

Phase agents should call `client_doc_search(engagement_id=decl["engagement_id"], query=..., top_k=3)` and include the returned chunk metadata in their artefacts/tool-call summaries where relevant.

### Success Check

Run this command. It must pass without exceptions:

```bash
python -c "
from aaa.tools.client_doc_ingest import client_doc_ingest, client_doc_search
# Dry-run with empty uri list — must return empty result, not crash
result = client_doc_ingest('test-eng-001', [])
assert result['chunks_indexed'] == 0
results = client_doc_search('test-eng-001', 'test query')
assert isinstance(results, list)
print('TASK-001 OK')
"
```

---

## TASK-002 — Add ISAE 3000 and ISO 19011 to the Regulatory Corpus

**Closes gaps**: E4 (ISAE 3000 / ISO 19011 alignment missing)  
**Prerequisites**: None  
**Parallel-safe**: Yes

### Context

The Regulatory RAG agent's Qdrant corpus currently contains: EU AI Act (339 chunks),
GDPR (288 chunks), ISO/IEC 42001:2023 (88 chunks). The exposé's literature review
references ISAE 3000 and ISO 19011 as the assurance and audit methodology standards
underpinning the UAGF-TAM protocol. Phase 6 needs these to generate the formal
auditor's opinion (Gap B1). The corpus ingestion script is at
`scripts/ingest_regulatory_corpus.py`.

ISAE 3000 and ISO 19011 must be ingested and retrieved with the **same strategy already
used for ISO/IEC 42001**, but not necessarily the exact same PDF parser implementation.
The strategy is: standards documents parsed into structural units → per-unit
`SentenceSplitter` chunking → dense `text-embedding-3-large` + sparse BM25 embeddings
→ named-vector hybrid Qdrant upsert → `RegulatoryRAG.search(...)` hybrid retrieval from
the existing `regulatory_corpus` collection. First investigate whether the ISO/IEC 42001
PDF pipeline works for the existing ISAE 3000 / ISO 19011 PDFs; if it does not, create a
standards-specific loader/chunker while preserving the same unit/chunk/payload/retrieval
strategy. Do not create a separate Qdrant collection, retrieval API, or prompt-only lookup
path for these standards.

### Steps

#### Step 1 — Source the documents

The following source files already exist in the existing corpus directory. Verify their
presence and update `scripts/ingest_regulatory_corpus.py` to discover them there. Do
**not** create or use `scripts/corpus_sources/`.

- **ISAE 3000 (Revised)**: `data/regulatory_corpus/isae_3000.pdf`
- **ISO 19011:2018**: `data/regulatory_corpus/iso_19011.pdf`

If either file is missing in a fresh clone, fail fast with a clear message telling the
operator which file is missing. Do not silently fall back to unrelated content. Only use a
stub for ISO 19011 in CI/offline tests when the real PDF is intentionally absent.

The CI/offline ISO 19011 stub text, if needed for tests only, is:

```
ISO 19011:2018 Guidelines for auditing management systems.
Clause 5: Managing an audit programme. An audit programme should include objectives, extent, duration, locations, schedule, audit methods, criteria, and selection of audit teams.
Clause 6: Conducting an audit. Phases include: initiating the audit, preparing audit activities, conducting audit activities, preparing and distributing audit report, completing the audit, conducting audit follow-up.
Clause 7: Competence and evaluation of auditors. Auditors must demonstrate knowledge of audit principles, procedures, and techniques; relevant management system standards; organisational context; applicable legal requirements.
Annex A: Additional guidance on auditor competence for specific disciplines.
NOTE: Full standard available from ISO at https://www.iso.org/standard/70017.html
```

#### Step 2 — Investigate PDF parsing and add ingestion logic

In `scripts/ingest_regulatory_corpus.py`, update `discover_corpus(corpus_dir)` and the PDF/plaintext loader dispatch. The current script treats every PDF as `ISO_IEC_42001`; that must be fixed so filename-based regulation mappings are explicit. Before coding the final loader, run a dry parser investigation against:

- `data/regulatory_corpus/isae_3000.pdf`
- `data/regulatory_corpus/iso_19011.pdf`

Check whether the existing ISO/IEC 42001 PDF loader produces meaningful structural units
for each file. Record, in code comments or test assertions, the observed unit counts and
whether headings/clauses are detected correctly. The new entries must:

- Use `regulation = "ISAE 3000"` and `regulation = "ISO 19011"` as the `regulation` field in chunk payloads.
- Reuse the ISO/IEC 42001 PDF parsing path **only if it works for these PDFs**. The same strategy is required, not blindly the same parser. If ISAE 3000 or ISO 19011 text extraction, heading detection, or clause segmentation differs, add a new loader such as `load_standard_pdf_units(path, regulation)` or per-standard helpers. The loader must still output the same `Unit` dataclass shape used by ISO/IEC 42001.
- For ISAE 3000, prefer structural refs such as paragraphs/sections where detectable; otherwise use stable page/heading refs like `Page 12 — Engagement acceptance`.
- For ISO 19011, prefer clause refs such as `5`, `6.3`, `7`; otherwise use stable page/heading refs.
- Use the same chunking defaults as ISO/IEC 42001: `DEFAULT_CHUNK_SIZE = 800`, `DEFAULT_CHUNK_OVERLAP = 100`, and `SentenceSplitter` applied per `Unit` so chunks do not cross legal/standard boundaries.
- Use the same payload shape as ISO/IEC 42001 chunks: `regulation`, `kind`, `ref`, `title`, `source_file`, `chunk_index`, `chunk_total`, `obligations`, `entity_types`, `risk_classes`, plus `text` at upsert time. Do not create a separate payload schema for ISAE/ISO 19011.
- Use the same dense + sparse embedding strategy as ISO/IEC 42001: dense OpenAI `text-embedding-3-large` vectors and sparse `Qdrant/bm25` vectors.
- Use the same SHA-256 idempotency mechanism already implemented: chunk point IDs are SHA-256 of `text + regulation + ref + chunk_index`.
- Store chunks in the existing hybrid `regulatory_corpus` Qdrant collection (same collection as EU AI Act, GDPR, ISO 42001 — do NOT create a separate collection).
- Keep `DEFAULT_CORPUS_DIR = REPO_ROOT / "data" / "regulatory_corpus"`; do not introduce another default source directory.

Add regression tests or dry-run assertions that fail if either standards PDF produces zero
units, zero chunks, empty refs, or chunks with missing `regulation` / `ref` / `source_file`
payload fields.

#### Step 2a — Keep retrieval identical to ISO/IEC 42001

Open `aaa/agents/tier1/regulatory_rag.py`.

Update only the regulation label mapping so retrieved chunks cite the new standards clearly:

```python
_REGULATION_LABEL = {
    ...existing labels...,
    "ISAE 3000": "ISAE 3000 (Revised)",
    "ISO 19011": "ISO 19011:2018",
}
```

Do not add a separate retrieval branch. ISAE 3000 and ISO 19011 must be returned through
the same `_vector_search(...)` path as ISO/IEC 42001: query embedded with
`text-embedding-3-large`, sparse BM25 query vector, Qdrant `Fusion.RRF`,
`with_payload=True`, then `_point_to_hit(...)`.

#### Step 3 — Update the corpus table comment in ARCHITECTURE.md

Open `ARCHITECTURE.md`. Find the corpus table in section `3.1a`. Add two rows:

```
| ISAE 3000 (Revised) | PDF (IAASB) | TBD after ingestion | pypdfium2 PDF backend |
| ISO 19011:2018      | PDF or stub | TBD after ingestion | pypdfium2 or plaintext |
```

Replace "TBD after ingestion" with the actual chunk counts after running the ingestion script.

#### Step 4 — Add a corpus coverage probe

In `scripts/ingest_regulatory_corpus.py`, add the following two queries to the existing `COVERAGE_PROBE_QUERIES` list (if this list does not exist, create it and run it at the end of the ingestion):

```python
"ISAE 3000 assurance engagement objectives reasonable assurance",
"ISO 19011 audit programme planning audit criteria"
```

After ingestion, log a WARNING if either query returns zero Qdrant results.

### Success Check

```bash
python scripts/ingest_regulatory_corpus.py --dry-run 2>&1 | grep -E "ISAE|ISO 19011"
# Must print at least one line mentioning ISAE 3000 and one mentioning ISO 19011
# (dry-run mode should list sources without calling OpenAI embeddings)

python3 - <<'PY'
from pathlib import Path
from scripts import ingest_regulatory_corpus as ingest

for file_name, regulation in [
    ('isae_3000.pdf', 'ISAE 3000'),
    ('iso_19011.pdf', 'ISO 19011'),
]:
    path = Path('data/regulatory_corpus') / file_name
    assert path.exists(), f'missing {path}'
    units = ingest.load_units_for_path(path, regulation)  # add this dispatch helper if absent
    assert units, f'no structural units parsed for {path}'
    chunks = ingest.chunk_units(units, ingest.CheckerLookup({}, [], []))
    assert chunks, f'no chunks produced for {path}'
    for chunk in chunks[:5]:
        assert chunk.payload.get('regulation') == regulation
        assert chunk.payload.get('ref')
        assert chunk.payload.get('source_file') == file_name
print('TASK-002 standards PDF chunking OK')
PY
```

If `--dry-run` is not implemented, add it: `--dry-run` flag prints source list and exits without calling any external APIs.

---

## TASK-003 — Add Materiality Fields to AuditState and Finding Types

**Closes gaps**: B8 (materiality thresholds expressed in assurance language)  
**Prerequisites**: TASK-000  
**Parallel-safe**: Yes

### Context

`AuditState` in `aaa/platform/state.py` currently has `final_verdict` as a three-value
enum (`PASS | PASS_WITH_OBSERVATIONS | FAIL`). Big 4 reports express findings in terms of
**materiality** — whether a non-conformity is significant enough to affect the overall
assurance conclusion. This task adds materiality fields to `Finding` and `RemediationItem`
without changing the existing `final_verdict` logic.

### Steps

#### Step 1 — Add Materiality type

Open `aaa/platform/state.py`.

Add the following new type definition near the top of the file, after the existing
`Literal` imports and before the `AnnexIIIEntry` class:

```python
Materiality = Literal[
    "material",          # Non-conformity is significant enough to affect the assurance conclusion
    "possibly_material", # Non-conformity requires professional judgement; flagged for human review
    "not_material"       # Non-conformity noted but does not affect overall conclusion
]
```

#### Step 2 — Add materiality to the Finding TypedDict

Find the `Finding` TypedDict (or class) in `state.py`. If it does not exist as a named
type and findings are stored as plain dicts, create a TypedDict for it now.

The `Finding` TypedDict must have these fields (add the ones that are missing; do not
remove existing fields):

```python
class Finding(TypedDict, total=False):
    finding_id: str                   # e.g. "F-001"
    article: str                      # e.g. "Art. 9"
    phase_id: str                     # e.g. "P5"
    description: str
    severity: Literal["critical", "major", "minor", "observation"]
    materiality: Materiality          # NEW — required field
    materiality_rationale: str        # NEW — one sentence explaining the materiality assessment
    evidence_uri: str | None
```

#### Step 3 — Add materiality to the RemediationItem TypedDict

Find the `RemediationItem` TypedDict (or wherever remediation items are defined).
Add these fields:

```python
class RemediationItem(TypedDict, total=False):
    # ... existing fields (keep all) ...
    materiality: Materiality           # NEW
    materiality_rationale: str         # NEW — one sentence
```

#### Step 4 — Add materiality_summary to AuditState

In the `AuditState` TypedDict, add these two fields in the `# --- compliance assembly ---` section:

```python
material_findings_count: Optional[int]      # NEW — count of findings with materiality = "material"
possibly_material_findings_count: Optional[int]  # NEW
```

#### Step 5 — Update the Orchestrator's final_verdict derivation

Open `aaa/agents/tier1/orchestrator.py`.

Find the section where `final_verdict` is set (it compares against `cgsa_phase5_verdict` and `blocking_findings`).

After the existing logic sets `final_verdict`, add this block to compute the new counts:

```python
state["material_findings_count"] = sum(
    1 for f in state.get("blocking_findings", [])
    if f.get("materiality") == "material"
)
state["possibly_material_findings_count"] = sum(
    1 for f in state.get("blocking_findings", [])
    if f.get("materiality") == "possibly_material"
)
```

Do not change the existing `final_verdict` logic. This is additive only.

#### Step 6 — Update the Verifier prompt via PROMPT.md/runtime

`PROMPT.md` now contains the canonical verifier materiality protocol. Update
`aaa/agents/tier1/verifier.py` to load its system prompt through the TASK-000 prompt
registry instead of maintaining a divergent `_SYSTEM_PROMPT` copy.

Ensure the loaded verifier prompt includes this instruction in the reasoning procedure / output contract:

> For every issue you flag with severity "critical" or "major", you must also assess its
> materiality. A finding is "material" if it would lead a reasonable regulator to question
> whether the system is compliant. A finding is "possibly_material" if it requires human
> judgement. A finding is "not_material" if it is a documentation gap that does not affect
> actual compliance. Include `materiality` and `materiality_rationale` in every issue object.

The current Verifier returns `issues: list[str]`; keep backward compatibility, but add an optional `materiality_assessments` list to the JSON output contract and thread it through the returned critique dict when present:

```json
"materiality_assessments": [
  {
    "issue": "<matching issue text or finding_id>",
    "severity": "critical|major|minor|observation",
    "materiality": "material|possibly_material|not_material",
    "materiality_rationale": "<one sentence>"
  }
]
```

### Success Check

```python
python -c "
from aaa.platform.state import Finding, RemediationItem, AuditState
# Check the new fields exist in the TypedDict annotations
assert 'materiality' in Finding.__annotations__, 'materiality missing from Finding'
assert 'materiality' in RemediationItem.__annotations__, 'materiality missing from RemediationItem'
assert 'material_findings_count' in AuditState.__annotations__, 'material_findings_count missing from AuditState'
print('TASK-003 OK')
"
```

---

## TASK-004 — Add Owner, Deadline, and Priority to Remediation Items

**Closes gaps**: B4 (findings memo with owner, deadline, priority)  
**Prerequisites**: None  
**Parallel-safe**: Yes

### Context

`T18_audit_report` currently renders a `remediation_roadmap` list that comes from the
CGSA payload (`aaa_phase5_handoff.remediation_roadmap[]`). The CGSA items have `rank`,
`control_id`, `gap_detail`, `gap_severity`. They do not have `assigned_owner`,
`deadline`, or `priority_label`. Big 4 findings memos always have these three fields
because clients need to know who owns each remediation action and by when.

### Steps

#### Step 1 — Extend RemediationItem TypedDict

Open `aaa/platform/state.py`.

In the `RemediationItem` TypedDict (same one extended in TASK-003), add these fields:

```python
class RemediationItem(TypedDict, total=False):
    # ... all existing fields ...
    # ... materiality fields from TASK-003 ...
    assigned_owner: Optional[str]    # NEW — role or team name, e.g. "Data Science Lead", "DPO"
    deadline_weeks: Optional[int]    # NEW — suggested weeks from report date to remediate
    priority_label: Literal["immediate", "short_term", "medium_term", "long_term"] | None  # NEW
```

The mapping from `gap_severity` to `priority_label` and `deadline_weeks` is:
- `critical` → `priority_label = "immediate"`, `deadline_weeks = 4`
- `major` → `priority_label = "short_term"`, `deadline_weeks = 12`
- `minor` → `priority_label = "medium_term"`, `deadline_weeks = 26`
- `observation` → `priority_label = "long_term"`, `deadline_weeks = 52`

#### Step 2 — Add owner mapping to Stage A triage form

Open `templates/T01a_stage_a_triage.json` (the JSON Schema for Stage A).

Add a new optional property to the schema's `properties` object:

```json
"organisation_contacts": {
  "type": "object",
  "description": "Key contacts for remediation ownership assignment",
  "properties": {
    "technical_lead":    { "type": "string", "description": "Name or role of the technical owner" },
    "data_lead":         { "type": "string", "description": "Name or role of the data governance owner" },
    "compliance_lead":   { "type": "string", "description": "Name or role of the compliance/legal owner" },
    "dpo":               { "type": "string", "description": "Data Protection Officer name or role, if applicable" },
    "executive_sponsor": { "type": "string", "description": "Executive accountable for AI governance" }
  },
  "additionalProperties": false
}
```

Do NOT add `organisation_contacts` to the `required` array — it remains optional.

#### Step 3 — Add owner auto-assignment in Phase 5

Open `aaa/agents/tier2/governance_agent.py`.

Find where `remediation_roadmap` items are built from the CGSA payload (the §5.4 map section).

After building each `RemediationItem`, add this auto-assignment logic:

```python
# Auto-assign owner based on the domain the finding comes from
domain_to_owner_field = {
    "D1": "technical_lead",    # D1 = Model & Algorithm
    "D2": "data_lead",         # D2 = Data Management
    "D3": "technical_lead",    # D3 = System Architecture
    "D4": "compliance_lead",   # D4 = Governance & Accountability
    "D5": "compliance_lead",   # D5 = Transparency & Explainability
    "D6": "dpo",               # D6 = Privacy & Security
}
contacts = state.get("client_submission", {}).get("stage_a", {}).get("organisation_contacts", {})
owner_field = domain_to_owner_field.get(item.get("domain_id"), "technical_lead")
item["assigned_owner"] = contacts.get(owner_field, "To be assigned")

# Auto-set deadline and priority from severity
severity_map = {
    "critical": ("immediate", 4),
    "major":    ("short_term", 12),
    "minor":    ("medium_term", 26),
}
priority_label, deadline_weeks = severity_map.get(item.get("gap_severity"), ("long_term", 52))
item["priority_label"]  = priority_label
item["deadline_weeks"]  = deadline_weeks
```

#### Step 4 — Update T18 template schema

Open `templates/T18_audit_report.json`.

Find the `remediation_roadmap` array items definition. Add these properties to each item's schema:

```json
"assigned_owner":  { "type": "string" },
"deadline_weeks":  { "type": "integer" },
"priority_label":  { "type": "string", "enum": ["immediate", "short_term", "medium_term", "long_term"] }
```

### Success Check

```python
python -c "
from aaa.platform.state import RemediationItem
annots = RemediationItem.__annotations__
assert 'assigned_owner' in annots
assert 'deadline_weeks' in annots
assert 'priority_label' in annots
print('TASK-004 OK')
"
```

---

## TASK-005 — Add Management Response Section to T18

**Closes gaps**: B5 (management response section missing)  
**Prerequisites**: TASK-004 (management response references the same findings table)  
**Parallel-safe**: No — depends on TASK-004

### Context

Big 4 assurance reports contain a "Management Response" section where the client
organisation formally responds to each finding. The AAA report should include this
section as a structured table with empty response fields, so the client can fill it in
after receiving the draft report. The Phase 6 Report Architect generates the shell;
the client fills in the "Response" and "Action Plan" columns.

### Steps

#### Step 1 — Add management_response to T18 template schema

Open `templates/T18_audit_report.json`.

Add a new property at the top level of the schema's `properties` object:

```json
"management_response": {
  "type": "array",
  "description": "Client management responses to audit findings. Shell is generated by AAA; responses are filled by client after draft report delivery.",
  "items": {
    "type": "object",
    "required": ["finding_id", "finding_summary", "materiality", "auditor_recommendation"],
    "properties": {
      "finding_id":             { "type": "string", "description": "References Finding.finding_id" },
      "finding_summary":        { "type": "string", "description": "One-sentence summary of the finding" },
      "materiality":            { "type": "string", "enum": ["material", "possibly_material", "not_material"] },
      "auditor_recommendation": { "type": "string", "description": "The specific action AAA recommends" },
      "management_response":    { "type": "string", "description": "CLIENT TO COMPLETE: Management's response to this finding", "default": "[Management response pending]" },
      "action_plan":            { "type": "string", "description": "CLIENT TO COMPLETE: Specific actions management commits to take", "default": "[Action plan pending]" },
      "target_completion_date": { "type": "string", "description": "CLIENT TO COMPLETE: Target date in YYYY-MM-DD format", "default": "[Date pending]" },
      "responsible_owner":      { "type": "string", "description": "CLIENT TO COMPLETE: Name and role of person responsible" }
    }
  }
}
```

#### Step 2 — Populate management_response shell in Phase 6

Open `aaa/agents/tier2/report_architect.py`.

In the section where the `T18` payload is assembled (before calling `report_render`),
add this block to generate the management response shell:

```python
management_response_shell = []
for finding in state.get("blocking_findings", []) + state.get("positive_findings", []):
    # Only include material and possibly_material findings in the response table
    if finding.get("materiality") in ("material", "possibly_material"):
        management_response_shell.append({
            "finding_id":             finding.get("finding_id", "F-???"),
            "finding_summary":        finding.get("description", "")[:200],
            "materiality":            finding.get("materiality", "possibly_material"),
            "auditor_recommendation": finding.get("recommendation", ""),
            "management_response":    "[Management response pending]",
            "action_plan":            "[Action plan pending]",
            "target_completion_date": "[Date pending]",
            "responsible_owner":      finding.get("assigned_owner", "[To be assigned]")
        })

t18_payload["management_response"] = management_response_shell
```

If `blocking_findings` items do not yet have a `recommendation` field, use `gap_detail` from the corresponding CGSA remediation item as a fallback.

#### Step 3 — Add management response section to the PDF rendering

Open `aaa/tools/report_render.py` (or wherever the ReportLab PDF is generated).

Find the section where the remediation roadmap is rendered. After that section, add
a new section titled **"Section 9: Management Response"** with these elements:

1. A section heading: "9. Management Response"
2. An introductory paragraph (fixed text):
   > "The following table presents the audit findings requiring management attention,
   > together with placeholder fields for management responses. The client organisation
   > is requested to complete the 'Management Response', 'Action Plan', 'Target
   > Completion Date', and 'Responsible Owner' columns and return the completed table
   > to the audit team within 10 business days of receiving this draft report."
3. A table with columns: `Finding ID | Finding | Materiality | Recommendation | Management Response | Action Plan | Target Date | Owner`
4. Render each item from `t18_payload["management_response"]` as a table row.
5. Use a light-grey background for the "Recommendation" column and white background for
   the "Management Response", "Action Plan", "Target Date", and "Owner" columns (these
   are the client-fill fields).

### Success Check

```python
python -c "
import json
schema = json.load(open('templates/T18_audit_report.json'))
props = schema.get('properties', {})
assert 'management_response' in props, 'management_response missing from T18 schema'
items = props['management_response'].get('items', {}).get('properties', {})
assert 'management_response' in items, 'management_response field missing from T18 items'
assert 'action_plan' in items
print('TASK-005 OK')
"
```

---

## TASK-006 — Add Risk Heat Map Generation Tool

**Closes gaps**: B2 (risk heat map missing from PDF)  
**Prerequisites**: TASK-003 (materiality fields needed to populate heat map)  
**Parallel-safe**: No — depends on TASK-003

### Context

Big 4 audit reports include a risk heat map: a 5×5 matrix with "Likelihood" on the
X-axis and "Impact" (or "Severity") on the Y-axis. Each finding is plotted as a dot.
The current ReportLab output is text-only. This task adds a `risk_heatmap_render` tool
that generates a PNG and embeds it in the PDF.

### Steps

#### Step 1 — Create the tool

Create a new file: `aaa/tools/risk_heatmap_render.py`

This file must define one function: `risk_heatmap_render(findings: list[dict], output_path: str) -> str`

The function must:
1. Create a 5×5 grid matplotlib figure. Do not use seaborn — use `matplotlib.pyplot` only (already in `requirements.txt` as a transitive dependency of shap; if not present, add `matplotlib>=3.9` to `requirements.txt`).
2. The X-axis is "Likelihood" with labels: `["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]` (left to right, values 1–5).
3. The Y-axis is "Impact / Severity" with labels: `["Negligible", "Minor", "Moderate", "Major", "Critical"]` (bottom to top, values 1–5).
4. Colour the cells using this scheme (RGB hex values):
   - Cells where `likelihood + impact >= 8`: `#FF4444` (red — high risk)
   - Cells where `likelihood + impact` is 6 or 7: `#FFA500` (amber — medium risk)
   - All other cells: `#90EE90` (green — low risk)
5. For each finding in `findings`:
   - Map `severity` to an `impact` score: `critical=5, major=4, minor=3, observation=2`
   - Map `materiality` to a `likelihood` score: `material=5, possibly_material=3, not_material=1`
   - Plot a black dot at `(likelihood, impact)` coordinates.
   - Annotate the dot with `finding_id` (tiny font, 7pt).
6. Add a title: "Risk Assessment Matrix"
7. Save to `output_path` as a PNG at 150 DPI.
8. Return `output_path`.

If `findings` is empty, generate the empty grid without dots and return `output_path`.

#### Step 2 — Wire the tool into Phase 6

Open `aaa/agents/tier2/report_architect.py`.

Before calling `report_render`, add:

```python
from aaa.tools.risk_heatmap_render import risk_heatmap_render
import tempfile, os

heatmap_tmp = os.path.join(tempfile.gettempdir(), f"heatmap_{engagement_id}.png")
risk_heatmap_render(
    findings=state.get("blocking_findings", []),
    output_path=heatmap_tmp
)
t18_payload["risk_heatmap_uri"] = heatmap_tmp  # Report renderer reads this
```

#### Step 3 — Embed heat map in the PDF

Open `aaa/tools/report_render.py`.

Find the executive summary section. After the executive summary paragraph and before
the compliance matrix, add this block:

```python
if t18_payload.get("risk_heatmap_uri") and os.path.exists(t18_payload["risk_heatmap_uri"]):
    from reportlab.platypus import Image as RLImage
    story.append(RLImage(t18_payload["risk_heatmap_uri"], width=14*cm, height=10*cm))
    story.append(Paragraph("Figure 1: Risk Assessment Matrix", styles['Caption']))
```

Import `cm` from `reportlab.lib.units` at the top of the file if not already imported.

#### Step 4 — Add risk_heatmap_uri to T18 schema

Open `templates/T18_audit_report.json`.

Add to `properties`:

```json
"risk_heatmap_uri": {
  "type": ["string", "null"],
  "description": "Temporary filesystem path to the generated risk heat map PNG"
}
```

### Success Check

```bash
python -c "
from aaa.tools.risk_heatmap_render import risk_heatmap_render
import tempfile, os
findings = [
    {'finding_id': 'F-001', 'severity': 'critical', 'materiality': 'material'},
    {'finding_id': 'F-002', 'severity': 'major',    'materiality': 'possibly_material'},
]
out = tempfile.mktemp(suffix='.png')
result = risk_heatmap_render(findings, out)
assert os.path.exists(result) and os.path.getsize(result) > 0
print('TASK-006 OK')
"
```

---

## TASK-007 — Add Control Maturity Radar Chart Tool

**Closes gaps**: B3 (control maturity radar chart missing from PDF)  
**Prerequisites**: TASK-003 (for type safety; can be run in parallel with TASK-006)  
**Parallel-safe**: Yes (alongside TASK-006)

### Context

The S4 CGSA payload contains `domains[]` — six governance domains (D1–D6), each with
a `domain_score` on a 0.0–4.0 maturity scale. These scores are already in `AuditState`
via `cgsa_payload.domains`. They are currently listed as text in T14 but never visualised.
This task adds a radar (spider) chart to the PDF.

### Steps

#### Step 1 — Create the tool

Create a new file: `aaa/tools/maturity_radar_render.py`

This file must define one function: `maturity_radar_render(domain_scores: dict[str, float], output_path: str) -> str`

`domain_scores` is a dict mapping domain name to score, e.g.:
```python
{
    "D1 Model & Algorithm": 2.5,
    "D2 Data Management": 3.0,
    "D3 System Architecture": 1.5,
    "D4 Governance & Accountability": 2.0,
    "D5 Transparency & Explainability": 2.5,
    "D6 Privacy & Security": 3.5
}
```

The function must:
1. Use `matplotlib.pyplot` with a polar subplot (`subplot_kw=dict(polar=True)`).
2. Plot the six domain scores as a filled radar polygon. Use `#5b6cff` (blue) with 30% alpha for the fill and solid `#5b6cff` for the border line (2pt).
3. Draw four concentric reference circles at scores 1.0, 2.0, 3.0, 4.0.
4. Label the reference circles with their maturity labels: `1=Initial`, `2=Developing`, `3=Defined`, `4=Optimised`. Place labels at the right side of each circle (angle = 0).
5. Label each axis with the domain name (short labels: `D1`, `D2` ... `D6` on the outer edge, full name inside in small font).
6. Add a title: "Governance Maturity by Domain".
7. Add a text box in the lower-right corner showing the composite score: `"Composite: X.X / 4.0"` using the average of all domain scores.
8. Save to `output_path` as a PNG at 150 DPI.
9. Return `output_path`.

If `domain_scores` is empty, generate a blank polar chart and return `output_path`.

#### Step 2 — Extract domain scores in Phase 5

Open `aaa/agents/tier2/governance_agent.py`.

In the CGSA consumption section (Step 3 of the Phase 5 Protocol), after processing
`domains[]`, add this extraction:

```python
domain_scores_for_chart = {}
for domain in cgsa_payload.get("domains", []):
    domain_id = domain.get("domain_id", "")
    domain_name = domain.get("domain_name", domain_id)
    domain_score = domain.get("domain_score", 0.0)
    label = f"{domain_id} {domain_name}"
    domain_scores_for_chart[label] = float(domain_score)

state["cgsa_domain_scores"] = domain_scores_for_chart
```

#### Step 3 — Add domain_scores field to AuditState

Open `aaa/platform/state.py`.

In the `# --- S4 CGSA hand-off ---` section of `AuditState`, add:

```python
cgsa_domain_scores: Optional[dict]  # NEW — {domain_label: score} for radar chart
```

#### Step 4 — Wire into Phase 6

Open `aaa/agents/tier2/report_architect.py`.

After the heat map generation block (from TASK-006), add:

```python
from aaa.tools.maturity_radar_render import maturity_radar_render

radar_tmp = os.path.join(tempfile.gettempdir(), f"radar_{engagement_id}.png")
domain_scores = state.get("cgsa_domain_scores", {})
if domain_scores:
    maturity_radar_render(domain_scores, radar_tmp)
    t18_payload["maturity_radar_uri"] = radar_tmp
```

#### Step 5 — Embed in PDF

Open `aaa/tools/report_render.py`.

In the Phase 5 governance section of the PDF (where T14 findings are rendered), add
the radar chart after the governance summary paragraph:

```python
if t18_payload.get("maturity_radar_uri") and os.path.exists(t18_payload["maturity_radar_uri"]):
    story.append(RLImage(t18_payload["maturity_radar_uri"], width=12*cm, height=10*cm))
    story.append(Paragraph("Figure 2: AI Governance Maturity by Domain", styles['Caption']))
```

### Success Check

```bash
python -c "
from aaa.tools.maturity_radar_render import maturity_radar_render
import tempfile, os
scores = {
    'D1 Model Algorithm': 2.5, 'D2 Data Management': 3.0,
    'D3 Architecture': 1.5,    'D4 Governance': 2.0,
    'D5 Transparency': 2.5,    'D6 Privacy': 3.5
}
out = tempfile.mktemp(suffix='.png')
result = maturity_radar_render(scores, out)
assert os.path.exists(result) and os.path.getsize(result) > 0
print('TASK-007 OK')
"
```

---

## TASK-008 — Add Formal Auditor's Opinion to T18 and Phase 6

**Closes gaps**: B1 (formal auditor's opinion missing), E4 (ISAE 3000 language)  
**Prerequisites**: TASK-002, TASK-003, TASK-006, TASK-007  
**Parallel-safe**: No

### Context

T18 currently has `final_verdict` as an enum string. Big 4 assurance reports always
contain a formal opinion paragraph written in ISAE 3000 assurance language. The opinion
distinguishes between "reasonable assurance" (PASS) and "qualified conclusion"
(PASS_WITH_OBSERVATIONS) and an "adverse conclusion" (FAIL). The Phase 6 Report
Architect must generate this paragraph based on the audit results.

### Steps

#### Step 1 — Add auditor_opinion field to T18 template schema

Open `templates/T18_audit_report.json`.

Add to `properties`:

```json
"auditor_opinion": {
  "type": "object",
  "required": ["opinion_type", "opinion_paragraph", "basis_paragraph", "methodology_basis"],
  "properties": {
    "opinion_type": {
      "type": "string",
      "enum": [
        "unqualified",           // PASS — reasonable assurance, no material findings
        "qualified",             // PASS_WITH_OBSERVATIONS — reasonable assurance except for specific matters
        "adverse",               // FAIL — adverse conclusion
        "disclaimer_of_opinion"  // ESCALATE_HITL — unable to form a conclusion
      ]
    },
    "opinion_paragraph":   { "type": "string", "description": "The formal opinion statement in ISAE 3000 language" },
    "basis_paragraph":     { "type": "string", "description": "Basis for the opinion / qualified matters" },
    "methodology_basis":   { "type": "string", "description": "Reference to UAGF-TAM, ISAE 3000, ISO 19011" },
    "scope_paragraph":     { "type": "string", "description": "What was and was not in scope" }
  }
}
```

Add `"auditor_opinion"` to the `required` array of the T18 schema.

#### Step 2 — Add auditor_opinion to AuditState

Open `aaa/platform/state.py`.

Add after `final_verdict`:

```python
auditor_opinion: Optional[dict]  # NEW — populated by Phase 6; keys match T18 auditor_opinion schema
```

#### Step 3 — Generate the opinion in Phase 6

Open `aaa/agents/tier2/report_architect.py`.

`ReportArchitect` is deterministic in the current repo, but the target architecture is
LLM-based multi-agent synthesis. Use the TASK-000 prompt registry to load the
`phase6_report` prompt from `PROMPT.md`, gather admitted artefacts/tool outputs into the
user payload, and call `BaseAgent.acompletion(...)` for the final T18 synthesis. Keep a
small deterministic fallback only for explicit offline/CI mode and mark fallback artefacts
with `llm_fallback_mode=true` where schemas allow it.

The Phase 6 LLM prompt must implement this mapping, and the deterministic fallback must
mirror it exactly:

- `final_verdict = "PASS"` and `material_findings_count = 0` → `opinion_type = "unqualified"`
- `final_verdict = "PASS_WITH_OBSERVATIONS"` or `PASS` with material findings → `opinion_type = "qualified"`
- `final_verdict = "FAIL"` → `opinion_type = "adverse"`
- HITL/escalation without enough evidence → `opinion_type = "disclaimer_of_opinion"`

The LLM must fill `opinion_paragraph`, `basis_paragraph`, `methodology_basis`, and
`scope_paragraph` from admitted artefacts only: `decl`, T01a/T01b/T17, phase Reports,
CGSA handoff, material findings, and verifier critiques. It must not invent evidence or
ask the customer for manual drafting. The fallback may use fixed templates.

The fixed `methodology_basis` text must be:

```text
This conformity assessment was conducted in accordance with the UAGF-TAM audit protocol (v1.0.0), applying the methodology of ISAE 3000 (Revised) for non-financial assurance engagements and ISO 19011:2018 for audit programme management. The audit was performed by an automated multi-agent system; results should be reviewed by a qualified human auditor before regulatory submission under Article 43 of the EU AI Act.
```

#### Step 4 — Render opinion in the PDF

Open `aaa/tools/report_render.py`.

Find the cover page or the section immediately after the cover page. Add the
`auditor_opinion` section as the FIRST content section of the report, before the
executive summary:

1. Section heading: "Independent Assurance Conclusion"
2. A styled box (border + light background) containing the `opinion_paragraph`.
3. If `opinion_type` is `"qualified"` or `"adverse"`, add a sub-heading "Basis for Conclusion" and render `basis_paragraph`.
4. A smaller-font paragraph: `methodology_basis`.
5. A smaller-font paragraph: `scope_paragraph`.

Use a coloured left border to signal opinion type: green for `unqualified`, amber for `qualified`, red for `adverse` or `disclaimer_of_opinion`.

### Success Check

```python
python -c "
import json
schema = json.load(open('templates/T18_audit_report.json'))
props = schema.get('properties', {})
assert 'auditor_opinion' in props, 'auditor_opinion missing from T18 schema'
required = schema.get('required', [])
assert 'auditor_opinion' in required, 'auditor_opinion not in T18 required fields'
op_props = props['auditor_opinion'].get('properties', {})
assert 'opinion_paragraph' in op_props
assert 'methodology_basis' in op_props
print('TASK-008 OK')
"
```

---

## TASK-009 — Fix regulatory_coverage ARTICLE_SET

**Closes gaps**: E1 (regulatory coverage KPI undercounts articles already covered by templates)  
**Prerequisites**: None  
**Parallel-safe**: Yes — fully independent

### Context

`aaa/tools/regulatory_coverage.py` defines `ARTICLE_SET` — the set of articles whose
compliance verdict is checked to compute `regulatory_coverage_pct` (KPI 2). The current
set only includes articles in the original T17 schema. However, T15 already covers
Arts. 12 and 72, and T12 covers Art. 50. These are already evidenced but not counted
in the KPI. This task fixes the undercounting without adding new agents or templates.

### Steps

#### Step 1 — Update ARTICLE_SET in regulatory_coverage.py

Open `aaa/tools/regulatory_coverage.py`.

Find the `ARTICLE_SET` dict (or equivalent structure that maps risk tier to a set of
articles). Update it as follows. For each tier, ADD the articles listed — do not remove
any existing articles.

```python
# For risk_tier = "high" — add to existing set:
additional_high = {
    "Art.5",       # Phase 1 Art. 5 gate result
    "Art.6",       # Phase 1 classification — already in T04
    "Art.11",      # Annex IV dossier — already in T01b
    "Art.12",      # Monitoring/logging — already in T15
    "Art.50",      # Output transparency — already in T12 (applies to LLM/chatbot outputs)
    "Art.72",      # Post-market monitoring — already in T15
    "Annex_IV",    # Technical documentation — existing repo article ID spelling
}

# For risk_tier = "gpai" — add to existing set:
additional_gpai = {
    "Art.5",
    "Art.6",
    "Art.11",
    "Art.12",
    "Art.50",      # Art. 50 is especially relevant for GPAI chatbot systems
    "Art.72",
    "Annex_IV",
}

# For risk_tier = "limited" and "minimal" — these tiers do NOT get Art.9/10/15 etc.
# Only add Art.50 if the system is a chatbot/LLM (handled by is_llm_or_agentic flag):
additional_limited = {"Art.50"}  # if is_llm_or_agentic else empty set
```

#### Step 2 — Update verdict derivation for new articles

The `regulatory_coverage.py` tool computes `regulatory_coverage_pct` by checking
whether each article in `ARTICLE_SET` has a verdict in `compliance_matrix`. The new
articles are already populated by Phase 1 (`Art.5`, `Art.6`, `Art.11`) and Phase 5
(`Art.12`, `Art.72`) and Phase 4 (`Art.50`).

For articles that phase agents do not yet write verdicts for (`Art.5`, `Art.11`, `Art.12`, `Art.72`, and `Annex_IV`), add fallback derivation before computing `covered`. Use the repo's verdict enum values (`PASS`, `PASS_WITH_OBSERVATIONS`, `FAIL`, `NOT_APPLICABLE`, `PENDING`) — do not introduce `COMPLIANT` / `PARTIALLY_COMPLIANT` strings.

```python
# If Art.5 is in ARTICLE_SET but not in compliance_matrix, derive it from scope gate state:
if "Art.5" in article_set and "Art.5" not in compliance_matrix:
    compliance_matrix["Art.5"] = "FAIL" if state.get("art5_prohibited") else "PASS"

# If Annex IV dossier quality is in scope but not already in compliance_matrix:
if "Annex_IV" in article_set and "Annex_IV" not in compliance_matrix:
    intake_score = state.get("intake_completeness_score")
    if intake_score is not None:
        if intake_score >= 0.80:
            compliance_matrix["Annex_IV"] = "PASS"
        elif intake_score >= 0.50:
            compliance_matrix["Annex_IV"] = "PASS_WITH_OBSERVATIONS"
        else:
            compliance_matrix["Annex_IV"] = "FAIL"
```

#### Step 3 — Update compliance-matrix assembly article mappings

Open `aaa/agents/tier1/orchestrator.py`.

In `_node_compliance_matrix`, update the `_TEMPLATE_ARTICLES` mapping and any direct critique citations so existing template evidence maps to the expanded article set. At minimum:

| Article | source_phase | supporting_template_ids       |
|---------|-------------|-------------------------------|
| Art.5   | P1          | ["T02_system_card", "T04_risk_tier_decision"] |
| Art.6   | P1          | ["T03_annex_iii_mapping", "T04_risk_tier_decision"] |
| Art.11  | P1          | ["T01b_annex_iv_dossier"] |
| Art.12  | P5          | ["T15_monitoring_logging_review"] |
| Art.50  | P4          | ["T12_output_fairness_report", "T13_output_sampling_log"] |
| Art.72  | P5          | ["T15_monitoring_logging_review"] |
| Annex_IV | P1/ORCH    | ["T01b_annex_iv_dossier", "T01c_intake_completeness_report"] |

`templates/T17_compliance_matrix.json` already models `articles` dynamically and does not contain a static article enum, so only change it if validation blocks the new article IDs.

#### Step 4 — Update the Orchestrator's _ARTICLE_PHASE map

Open `aaa/agents/tier1/orchestrator.py` (or `aaa/agents/tier2/report_architect.py`
— find wherever `_ARTICLE_PHASE` or equivalent lookup is defined).

Add the new articles to the lookup:

```python
_ARTICLE_PHASE = {
    # ... existing entries unchanged ...
    "Art.5":   "P1",
    "Art.6":   "P1",
    "Art.11":  "P1",
    "Art.12":  "P5",
    "Art.50":  "P4",
    "Art.72":  "P5",
    "Annex_IV": "P1",
}
```

### Success Check

```bash
python -c "
from aaa.tools.regulatory_coverage import ARTICLE_SET
high_articles = ARTICLE_SET.get('high', set())
required = {'Art.5', 'Art.6', 'Art.11', 'Art.12', 'Art.50', 'Art.72', 'Annex_IV'}
missing = required - high_articles
assert not missing, f'Missing from ARTICLE_SET: {missing}'
print('TASK-009 OK — ARTICLE_SET now includes:', sorted(high_articles))
"
```

---

## TASK-010 — Align Existing Embedding Utilities and Repo-Surface Assumptions

**Closes gaps**: R1 (existing `text-embedding-3-small` use), R2 (stale path/prompt assumptions)  
**Prerequisites**: None  
**Parallel-safe**: Yes

### Context

The current repo already uses `text-embedding-3-large` / 3072 dimensions in
`scripts/ingest_regulatory_corpus.py` and `aaa/agents/tier1/regulatory_rag.py`,
but `aaa/tools/evidence_truncate.py` still embeds truncation-ranking inputs with
`text-embedding-3-small`. `PROMPT.md` is now present and must remain aligned with the
implementation. Regulatory corpus files belong under `data/regulatory_corpus/`.

### Steps

1. Open `aaa/tools/evidence_truncate.py`.
2. Change `_DENSE_MODEL` from `text-embedding-3-small` to `text-embedding-3-large`.
3. Update the module docstring to say 3072-dimensional embeddings.
4. Search the repo for `text-embedding-3-small` excluding `UPDATE.md`; no implementation file should still use it.
5. Search the repo for `scripts/corpus_sources` excluding `UPDATE.md`; no implementation/documentation path should instruct the agent to use it.
6. Do not modify `aaa/ui/**` or `aaa/api/**` for this narrow embedding/prompt-surface cleanup task; customer upload/report work is handled by TASK-011.

### Success Check

```bash
python3 - <<'PY'
from pathlib import Path
from aaa.tools import evidence_truncate

assert evidence_truncate._DENSE_MODEL == "text-embedding-3-large"

skip_parts = {".git", ".venv", "__pycache__"}
bad_small = []
bad_corpus_sources = []
for path in Path('.').rglob('*'):
    if not path.is_file() or path.name == 'UPDATE.md' or any(p in skip_parts for p in path.parts):
        continue
    text = path.read_text(errors='ignore')
    if 'text-embedding-3-small' in text:
        bad_small.append(str(path))
    if 'scripts/corpus_sources' in text:
        bad_corpus_sources.append(str(path))

assert not bad_small, bad_small
assert not bad_corpus_sources, bad_corpus_sources
print('TASK-010 OK')
PY
```

---

## TASK-011 — Customer Upload-to-Report Workflow

**Closes gaps**: UX1 (customer cannot upload documents/model directly), UX2 (API cannot accept artefact uploads or return reports), UX3 (PDF report not exposed in UI)  
**Prerequisites**: TASK-001  
**Parallel-safe**: No — depends on the client-document ingestion contract from TASK-001

### Context

The current customer-facing flow is still demo/fixture-oriented:

- `aaa/ui/app.py` renders Stage A fields, but Stage B is a raw JSON text area seeded from `scripts/fixtures/uci_german_credit/stage_b.json`.
- There are no `st.file_uploader` controls for risk-management files, EU declarations, post-market plans, L-branch prompts/RAG manifests/guardrails/golden sets, datasets, or model artefacts.
- Uploaded files are not persisted to `EvidenceStore`, so the URI fields in `T01b` cannot be populated by a normal customer.
- `aaa/api/main.py` only exposes health/schema-version/basic engagement CRUD; there is no upload, run, status, artefact, or report endpoint.
- The Streamlit downloads expose AuditState/T17/T18 JSON, but not the rendered PDF payload returned by `report_render`.

The target customer journey is simple: **upload docs and optional model/data artefacts → run audit → download report**.

### Steps

#### Step 1 — Add file artefact storage to EvidenceStore

Open `aaa/platform/evidence.py`.

Add a binary-safe method without removing the existing `store_artefact` API:

```python
def store_file(
    self,
    engagement_id: str,
    phase: str,
    artefact_type: str,
    filename: str,
    content_type: str,
    data: bytes,
    agent_name: str,
) -> str:
    ...
```

For the current in-memory implementation, store a dict payload containing at least:

- `filename`
- `content_type`
- `bytes_size`
- `sha256`
- `body_base64`

Return a `minio://...` URI and add an index row with the same metadata. Keep `get_artefact(uri)` able to return this payload. Do not log file contents.

#### Step 2 — Extend intake schema/state for customer uploads

Open `templates/T01b_annex_iv_dossier.json` and `aaa/platform/state.py`.

Add optional URI fields; do not add them to `required`:

```json
"training_dataset_uri": { "type": ["string", "null"] },
"evaluation_dataset_uri": { "type": ["string", "null"] },
"model_artifact_uri": { "type": ["string", "null"] },
"model_metadata_uri": { "type": ["string", "null"] }
```

These fields align with existing backend expectations: `DataAuditor._load_dataset()` already checks `training_dataset_uri`, and `ModelValidator` can be extended later to load `model_artifact_uri`.

#### Step 3 — Replace Stage B JSON-only UI with guided upload sections

Open `aaa/ui/app.py`.

Keep the existing JSON editor only as an **Advanced JSON editor** expander. The default Stage B experience must have customer-friendly controls:

1. Required Annex IV text areas for the current required T01b text fields.
2. File uploaders for document URI fields:
   - `risk_management_file_uri`
   - `eu_doc_uri`
   - `post_market_plan_uri`
   - `system_prompt_uri`
   - `rag_manifest_uri`
   - `guardrail_config_uri`
   - `golden_set_uri`
3. Optional model/data uploaders:
   - training dataset (`.csv`, `.parquet`, `.json`)
   - evaluation dataset (`.csv`, `.parquet`, `.json`)
   - model artefact (`.pkl`, `.joblib`, `.onnx`, `.pt`, `.safetensors`, `.zip`)
   - model metadata (`.json`, `.md`, `.txt`)
4. On upload, call `EvidenceStore.store_file(...)` and write the returned URI into the Stage B payload.
5. Show a checklist of which documents were uploaded and which optional items are missing.

Do not require a customer to manually paste `minio://...` URIs.

#### Step 4 — Thread uploaded files into the audit run

In `_run_pipeline(...)`, accept the same `EvidenceStore` instance used by the upload widgets instead of creating a fresh empty store after uploads. Ensure Stage A/B/C payloads and all uploaded files are in the same store before `IntakeValidator` runs.

After TASK-001 is implemented, `IntakeValidator` will ingest the uploaded document URIs into the per-engagement client-doc Qdrant collection.

#### Step 5 — Expose final report downloads, including PDF

In `aaa/ui/app.py`, after the run completes:

1. Load T18 from `phase_artefacts["T18_audit_report"]`.
2. Read `t18["rendered_report"]["pdf_uri"]` and `json_uri`.
3. Fetch both from `EvidenceStore`.
4. If the PDF payload has `encoding="latin-1"`, encode the stored body back to bytes and expose it through `st.download_button(..., mime="application/pdf")`.
5. Keep T18 JSON download.
6. Move full AuditState download behind an advanced/debug expander so the primary customer action is downloading the report.

#### Step 6 — Add API endpoints for the same workflow

Open `aaa/api/main.py`.

Add demo-compatible in-memory endpoints (production can later swap storage/backend):

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/engagements/{engagement_id}/files` | Multipart upload; fields: `role`, `file`; stores via `EvidenceStore.store_file` and returns `{uri, sha256, role}` |
| `POST` | `/api/v1/engagements/{engagement_id}/intake` | Submit Stage A/B/C JSON payloads, with uploaded-file URIs already populated |
| `POST` | `/api/v1/engagements/{engagement_id}/run` | Run `IntakeValidator → Orchestrator` for that engagement |
| `GET` | `/api/v1/engagements/{engagement_id}/report` | Return final verdict, KPI summary, T18 JSON URI, and PDF URI |
| `GET` | `/api/v1/engagements/{engagement_id}/report.pdf` | Return rendered PDF bytes with `application/pdf` when available |

Keep this minimal. Do not add authentication, organisations, billing, comments, dashboards, or user-management in this task.

#### Step 7 — Add smoke tests for the customer journey

Add focused tests that do not require a browser:

- `tests/unit/test_evidence_store_file_upload.py` — verifies `store_file` round-trip, sha256, metadata, and no content leakage in index rows beyond metadata.
- `tests/unit/test_ui_upload_helpers.py` or equivalent — verifies uploaded-file payloads populate the correct T01b URI keys.
- `tests/unit/test_api_customer_workflow.py` — uses FastAPI `TestClient` to create an engagement, upload a small text file, submit intake, and confirm report endpoint shape. Use offline mode and tiny fixtures.

### Success Check

```bash
python3 -m pytest \
  tests/unit/test_evidence_store_file_upload.py \
  tests/unit/test_api_customer_workflow.py

python3 - <<'PY'
import inspect
from aaa.platform.evidence import EvidenceStore
import aaa.ui.app as app
import aaa.api.main as api

assert hasattr(EvidenceStore, 'store_file')
ui_src = inspect.getsource(app)
assert 'file_uploader' in ui_src
assert 'application/pdf' in ui_src
routes = {route.path for route in api.app.routes}
assert '/api/v1/engagements/{engagement_id}/files' in routes
assert '/api/v1/engagements/{engagement_id}/run' in routes
assert '/api/v1/engagements/{engagement_id}/report' in routes
print('TASK-011 OK')
PY
```

---

## Final Validation — Run After All Tasks Complete

Run these checks in order. All must pass.

```bash
# 1. Schema validation — all 20 templates must still be valid JSON
python -c "
import json, os, glob
for f in glob.glob('templates/*.json'):
    try:
        json.load(open(f))
    except Exception as e:
        print(f'FAIL {f}: {e}')
        raise
print('All templates: valid JSON')
"

# 2. Prompt runtime checks
python3 -m pytest tests/unit/test_prompt_registry.py

# 3. State type check
python -m mypy aaa/platform/state.py --ignore-missing-imports

# 4. Offline smoke test — must complete without exceptions
python -m aaa.cli run \
  --engagement-id eng-uci-german-credit-001 \
  --intake-dir scripts/fixtures/uci_german_credit \
  --cgsa-fixture-dir scripts/fixtures/cgsa \
  --offline 2>&1 | tail -20
# Output must contain: "final_verdict"

# 5. Customer upload/report workflow tests, once TASK-011 is implemented
python3 -m pytest tests/unit/test_evidence_store_file_upload.py tests/unit/test_api_customer_workflow.py
```

---

## Migration Notes for Human Operator

The following steps require human action and cannot be automated by the implementing agent:

| # | Action | When |
|---|--------|------|
| M1 | Obtain ISAE 3000 PDF from IAASB website and place at `data/regulatory_corpus/isae_3000.pdf` | Before running TASK-002 |
| M2 | Obtain ISO 19011:2018 PDF from ISO (paid) and place it at `data/regulatory_corpus/iso_19011.pdf`, or use the `data/regulatory_corpus/iso_19011_stub.txt` stub created by TASK-002 | Before running TASK-002 |
| M3 | Re-run `scripts/ingest_regulatory_corpus.py` to populate ISAE 3000 and ISO 19011 chunks into Qdrant | After TASK-002 complete |
| M4 | Review the generated `auditor_opinion` on the first real case study — the ISAE 3000 language templates are correct in structure but may need editorial refinement for specific use cases | After TASK-008, during M5 Case Study 1 |
| M5 | Fill in `organisation_contacts` in Stage A fixture file `scripts/fixtures/uci_german_credit/stage_a.json` with placeholder contacts for the German Credit case study demo | Before running `make m5-case1` |
