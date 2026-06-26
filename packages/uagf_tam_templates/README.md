# uagf-tam-templates

This package contains the distributable **T01a–T18 JSON Schemas** and the
packaged Jinja partials used by the AAA reporting flow.

It is intended for:

- schema consumers that do not want the full AAA runtime
- tests that validate template compatibility independently of the main app
- future publication as a standalone artefact package

## Install

### Local editable install

```bash
cd packages/uagf_tam_templates
python -m pip install -e .
```

### If published to an index

```bash
python -m pip install uagf-tam-templates
```

## Usage

```python
import uagf_tam_templates as utt

ids = utt.list_templates()
schema = utt.load_schema("T17_compliance_matrix")
utt.validate("T17_compliance_matrix", payload)
markdown = utt.render_partial("T18_audit_report", payload)
```

## Package contents

- `src/uagf_tam_templates/schemas/T*.json` — packaged draft-07 schemas
- `src/uagf_tam_templates/partials/*.j2` — packaged partials for T17 and T18
- `tests/test_loader.py` — smoke tests for discovery, validation, and rendering

## Sync from the main repository

The canonical schema files in this repo live under `templates/`.

To refresh the packaged copies:

```bash
cp templates/T*.json packages/uagf_tam_templates/src/uagf_tam_templates/schemas/
```

## Versioning and release notes

- **License:** MIT
- **Versioning:** SemVer 2.0.0
- **Coverage gate:** `pytest --cov --cov-fail-under=80`
- **Python requirement:** see `pyproject.toml`

Example release flow:

```bash
cd packages/uagf_tam_templates
python -m pip install --upgrade build twine
python -m build
twine check dist/*
```
