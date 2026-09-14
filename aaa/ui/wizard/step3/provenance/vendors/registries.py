"""Questions for providers whose weights the customer pulls or hosts."""
from __future__ import annotations

#: provider → ordered ``(model_reference key, label, help)`` questions.
REGISTRY_QUESTIONS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "huggingface": (
        ("model_id", "Repository id",
         "The repo you run, as org/name — e.g. cimphony-ai-admin/Cimphony-Mistral-Law-7B."),
        ("revision", "Commit SHA",
         "The exact commit in production. A branch name such as 'main' re-points over "
         "time and does not pin a model."),
        ("gated", "Gated or private repo?",
         "Gated repos need licence acceptance before download. If yes, say who on your "
         "side can grant the auditor access."),
        ("license", "Licence", "As stated on the model card, e.g. apache-2.0."),
        ("base_model_id", "Base model repository",
         "Adapters only — the base the adapter is loaded onto."),
        ("base_model_revision", "Base model commit SHA",
         "Adapters only — the base pinned to a commit, not a branch."),
        ("peft_type", "Adapter method", "Adapters only, e.g. LORA."),
        ("runtime_versions", "Library versions",
         "transformers / torch / peft versions as run in production."),
        ("quantization", "Quantization", "As loaded — none, int8, int4, awq, gptq."),
    ),
    "self_hosted": (
        ("model_id", "Served model name", "The name your server exposes for this model."),
        ("revision", "Server image digest and weight revision",
         "The sha256 digest of the serving image plus the registry revision the "
         "weights came from."),
        ("endpoint_url", "Endpoint URL", "Where the model is served."),
        ("quantization", "Quantization", "As served, plus tensor-parallel size if used."),
        ("runtime_versions", "Server and library versions",
         "e.g. vLLM / TGI / Ollama version."),
    ),
    "other": (
        ("model_id", "Model identifier", "However your vendor names this model."),
        ("revision", "Version pin",
         "Whatever your vendor offers that cannot change — a digest, a dated "
         "snapshot, or a version number."),
        ("endpoint_url", "Endpoint or download location", "Where the model is obtained."),
        ("license", "Licence", "Licence governing the weights or the API."),
    ),
}
