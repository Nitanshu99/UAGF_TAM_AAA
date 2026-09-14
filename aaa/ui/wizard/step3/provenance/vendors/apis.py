"""Questions for first-party model APIs, where no weights ever change hands."""
from __future__ import annotations

#: provider → ordered ``(model_reference key, label, help)`` questions.
API_QUESTIONS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "openai": (
        ("model_id", "Model snapshot id",
         "The dated snapshot, e.g. gpt-4o-2024-08-06. A bare alias like gpt-4o "
         "re-points to new weights without notice and cannot pin an audit."),
        ("revision", "Snapshot date",
         "The date suffix again, or the full ft:… id if this is a fine-tune."),
        ("auth_type", "Authentication", "Usually api_key."),
        ("endpoint_url", "Base URL", "Only if you call through a gateway or proxy."),
        ("decoding_params", "Decoding settings",
         "temperature, top_p, seed and max_tokens as sent in production — the same "
         "weights at different settings produce different audit numbers."),
    ),
    "azure_openai": (
        ("model_id", "Deployment name",
         "Your deployment name, which is chosen by you and is not the model name."),
        ("revision", "Model snapshot and api-version",
         "The underlying model snapshot behind the deployment, plus the api-version "
         "string, which changes response behaviour."),
        ("endpoint_url", "Resource endpoint", "Including the region."),
        ("auth_type", "Authentication", "api_key or Entra ID."),
        ("decoding_params", "Decoding settings",
         "temperature, top_p, max_tokens, plus any content-filter policy applied."),
    ),
    "anthropic": (
        ("model_id", "Model id", "Including its date suffix."),
        ("revision", "anthropic-version header", "The API version used in production."),
        ("auth_type", "Authentication", "Usually api_key."),
        ("decoding_params", "Decoding settings",
         "max_tokens, temperature, top_p, and the extended-thinking budget if enabled."),
    ),
    "google_gemini": (
        ("model_id", "Model id",
         "e.g. gemini-2.5-pro. Include the version suffix if you pin one."),
        ("revision", "Pinned model version",
         "The specific version you run. On Vertex AI give the publisher model version; "
         "an unpinned alias moves underneath you."),
        ("endpoint_url", "Surface, project and region",
         "AI Studio or Vertex AI. For Vertex give the project and region — model "
         "availability and versions differ by region."),
        ("auth_type", "Authentication",
         "api_key for AI Studio, or a service account / OAuth for Vertex AI."),
        ("decoding_params", "Decoding settings",
         "temperature, top_p, top_k, max_output_tokens, and any safety-setting "
         "thresholds you override."),
    ),
}
