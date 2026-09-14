# Per-agent LLM-call assessment tooling

Produces one markdown file per mock case recording the *exact* assembled input and raw
output of every LLM call in a run, with a per-call assessment.

## Procedure

```bash
wc -l < logs/audit/llm_audit.jsonl            # 1. record the boundary
python -m scripts.run_mock_case 01_finclear_gmbh   # 2. run the case
python -m scripts.agent_assessment.extract_calls <boundary> calls.json [end_line]
python -m scripts.agent_assessment.digest_calls calls.json      # read this to judge
python -m scripts.agent_assessment.gen_report calls.json \
       local/assessments/analysis/analysis_case1.py \
       local/assessments/case_01_finclear_gmbh/report.md
```

Run them as modules from the repository root, like every other script here. The
digest and report share helpers in this package, so running one by file path puts
`scripts/agent_assessment/` on the import path instead of the repository root and the
import of its siblings fails.

`extract_calls.py` slices the append-only audit trail by line offset — unambiguous since
`aaa/agents/base/audit.py` began stamping `ts` and `engagement_id`.

### Several cases in one sitting

The trail is append-only and shared, so cases must be run **sequentially** and each
one's slice recorded as it goes: `[boundary, end_line)`. Pass both to
`extract_calls.py`; without `end_line` the slice runs to the end of the file, which is
only unambiguous for the last case run.

### Reading a run before judging it

`digest_calls.py` is the reading aid. One case is ~50 calls of ~10,000 prompt tokens,
and the delivered markdown carries all of it verbatim — necessary for the document,
useless for forming the judgement. The digest prints, per call: the system prompt's
section headings and a hash (so a prompt identical to an earlier call is visible as
such rather than re-read), the user payload by key with counts for the bulky parts,
whether regulatory and client-document retrieval actually reached the call, and the
reply — flagging any reply under 400 characters, which is almost always a refusal, a
retrieval plan, or a stub. `--full 3,17` prints those calls verbatim instead, for the
ones the digest says are worth reading in full.

`local/assessments/analysis/analysis_case<N>.py` is the judgement layer: `HEADER`, `FOOTER`, `TITLES`, `NOTES`
(seq -> assessment markdown) and `GROUPS`. `gen_report.py` interleaves it with the
verbatim call data.

## The document is generated — edit the analysis file, never the markdown

`local/assessments/case_0<N>_*.md` is **output**. Anything written directly into it is
lost the next time `gen_report.py` runs. Every word of prose in it comes from
`local/assessments/analysis/analysis_case<N>.py`; the mechanical half comes from `calls.json`.

`calls.json` is not kept in the repo. To regenerate the document without re-running the
case, re-slice the same boundary from the audit trail (case 01 is line 2364), then run
`gen_report.py`. Confirm a change was faithful by rendering to a scratch path and diffing
against the committed document before overwriting it.

## Recording a fix

Fixes are applied one at a time, each verified before the next is started, and each is
recorded in **three** places in `local/assessments/analysis/analysis_case<N>.py`:

1. **The findings register** (`HEADER`) — mark the row `blocking · **FIXED**` and update the
   `> **Status.**` note that lists which findings are closed. The finding text itself is
   left as originally written: it describes the code as it stood during the assessed run,
   and that is the evidence.
2. **The fix table and remediation log** (`FOOTER`) — tick the row, and add a
   `#### Fix N — <what it did> (<findings>) · applied <date>` section recording what changed,
   how it was verified (a before/after measurement against the assessed run, not just "tests
   pass"), and — importantly — **what the fix left open**.
3. **The per-call suggestions** (`_APPLIED`, at the end of the file) — append a
   `> **Since the assessment.**` line to the `NOTES` entry whose suggestion the fix
   implemented, so a reader of call #N learns its recommendation was taken without scanning
   the log. Suggestions are left as written; only their status is appended.

Keep the `#### State of the suite after fixes 1-N` block current: test count, `ruff`,
`pylint`, and whether the pipeline has been re-run end to end (the KPIs and call transcripts
above it are those of the original assessed run and do **not** move when a fix lands).
