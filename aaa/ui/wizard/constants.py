"""Shared wizard constants: paths, Annex III labels, upload field specs.

Upload field specs map ``field_key`` to ``(label, description,
allowed_file_types)`` and drive the file-uploader widgets in steps 1 and 3.
"""
from __future__ import annotations

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
TEMPLATES_DIR = REPO_ROOT / "templates"
FIXTURE_DIR = REPO_ROOT / "scripts" / "fixtures" / "uci_german_credit"

#: Annex III section number → plain-English questionnaire label.
ANNEX_III_LABELS: dict[str, str] = {
    "1": "1 — Biometric identification and categorisation of natural persons",
    "2": "2 — Management and operation of critical infrastructure",
    "3": "3 — Education and vocational training",
    "4": "4 — Employment, worker management and access to self-employment",
    "5": "5 — Access to and enjoyment of essential private/public services (e.g. credit, insurance)",
    "6": "6 — Law enforcement",
    "7": "7 — Migration, asylum and border control",
    "8": "8 — Administration of justice and democratic processes",
}

#: Supporting documents with a §/Article mapping under Annex IV.
DOC_UPLOAD_FIELDS: dict[str, tuple[str, str, list[str]]] = {
    "risk_management_file_uri": ("Risk management documentation",
                                 "§5 / Art. 9 — Your risk management system file", ["pdf", "doc", "docx"]),
    "eu_doc_uri": ("EU Declaration of Conformity",
                   "§8 — Signed declaration of conformity (if available)", ["pdf", "doc", "docx"]),
    "post_market_plan_uri": ("Post-market monitoring plan",
                             "§9 / Art. 72 — Your post-deployment monitoring plan", ["pdf", "doc", "docx"]),
    "system_prompt_uri": ("System prompt",
                          "LLM / Agentic only — The system prompt used by the model", ["txt", "md", "json"]),
    "rag_manifest_uri": ("RAG manifest",
                         "LLM / Agentic only — Vector-store schema and retrieval configuration",
                         ["json", "yaml", "yml"]),
    "guardrail_config_uri": ("Guardrail configuration",
                             "LLM / Agentic only — Content-filter or safety guardrail configuration",
                             ["json", "yaml", "yml"]),
    "golden_set_uri": ("Golden evaluation set",
                       "LLM / Agentic only — At least 50 Q&A pairs for evaluation", ["json", "csv"]),
    "trace_sample_uri": ("Agentic trace sample",
                        "Agentic only — JSON array of tool-call traces from your own tracing "
                        "(e.g. a Langfuse export): [{\"id\": ..., \"steps\": [{\"type\": "
                        "\"tool_call\", \"tool_name\": ..., \"depth\": ...}]}]", ["json"]),
}

#: Optional model / dataset artefacts that deepen the technical audit.
OPTIONAL_UPLOAD_FIELDS: dict[str, tuple[str, str, list[str]]] = {
    "training_dataset_uri": ("Training dataset",
                             "Optional — The dataset used to train the model", ["csv", "parquet", "json"]),
    "evaluation_dataset_uri": ("Evaluation dataset",
                               "Optional — The dataset used to evaluate/test the model",
                               ["csv", "parquet", "json"]),
    # F6: a directory-shaped model (HF snapshot, Chronos wrapper) arrives as a
    # .zip — the convention `mock/02_*/model/` and `mock/04_*/model/` already
    # use. Saying so is what makes `model_artifact_kind` answerable.
    "model_artifact_uri": ("Model artefact",
                           "Optional — The trained model. A single file, or a .zip of the "
                           "model directory when the model needs several files "
                           "(weights + config.json, an adapter, a wrapper).",
                           ["pkl", "joblib", "onnx", "pt", "safetensors", "zip"]),
    "model_metadata_uri": ("Model metadata", "Optional — Model card or metadata file", ["json", "md", "txt"]),
}
