# uagf-tam-templates

Distributable **T01a–T18 JSON-Schema templates** and **Jinja2 partials** for the
UAGF-TAM Autonomous AI Auditor (§4A of `ARCHITECTURE.md`).

This package lets third-party audit toolchains, regulators, or auditees
consume the canonical artefact schemas without installing the full AAA
runtime.

## Install

```bash
pip install uagf-tam-templates
```

## Usage

```python
import uagf_tam_templates as utt

# Discover all packaged templates
utt.list_templates()
# -> ['T01a_stage_a_triage', 'T01b_annex_iv_dossier', ..., 'T18_audit_report']

# Load and validate
schema = utt.load_schema("T17_compliance_matrix")
utt.validate("T17_compliance_matrix", my_payload)

# Render the packaged Jinja2 partial
md = utt.render_partial("T17_compliance_matrix", my_payload)
```

## Contents

- `src/uagf_tam_templates/schemas/T*.json` — JSON Schema (draft-07) for
  T01a, T01b, T01c, T02–T16, T17, T18.
- `src/uagf_tam_templates/partials/*.j2` — Jinja2 partials for the
  human-readable rendering of T17 (compliance matrix) and T18 (audit
  report).

## Versioning and publication

- **Licence:** MIT.
- **Versioning:** [SemVer 2.0.0](https://semver.org).  Bump `MAJOR` only
  when a schema field is removed or its semantics changes.
- **CI gate:** `pytest --cov` runs against the packaged schemas with a
  `--cov-fail-under=80` minimum (see `pyproject.toml`).
- **Publish flow** (release engineer):

  ```bash
  cd packages/uagf_tam_templates
  python -m pip install --upgrade build twine
  python -m build                      # produces dist/*.whl and *.tar.gz
  twine check dist/*
  twine upload --repository testpypi dist/*   # 1) staging
  twine upload dist/*                          # 2) PyPI
  ```

Schema files are kept in lock-step with `src/templates/*.json` in the AAA
mono-repo; regenerate the package copies with:

```bash
cp src/templates/T*.json packages/uagf_tam_templates/src/uagf_tam_templates/schemas/
```
