"""Questions for platforms that route or manage someone else's weights.

These need one question the first-party APIs do not: the identifier the
customer holds names a *route*, and the weights actually answering a request
sit one hop further on. OpenRouter can serve a single slug from several
upstream providers at different quantizations, and Bedrock fronts other
vendors' models behind an ARN.
"""
from __future__ import annotations

#: provider → ordered ``(model_reference key, label, help)`` questions.
GATEWAY_QUESTIONS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "openrouter": (
        ("model_id", "Route slug", "As OpenRouter addresses it, e.g. org/model."),
        ("revision", "Pinned variant",
         "Include any :variant suffix you pin. Without one the route can move "
         "between upstream builds."),
        ("upstream_provider", "Upstream provider actually served",
         "One slug can be served by several providers at different quantizations, so "
         "the slug alone does not say which weights answered. Name the provider you "
         "pin, or state that routing is automatic."),
        ("quantization", "Quantization served",
         "As reported by the route, if you constrain it."),
        ("endpoint_url", "Base URL", "Only if you call through your own proxy."),
        ("decoding_params", "Decoding settings",
         "temperature, top_p, seed, max_tokens, plus any provider-routing or "
         "fallback preferences you set."),
    ),
    "nvidia_nim": (
        ("model_id", "NGC model id", "The catalog identifier for the model."),
        ("revision", "Container image digest",
         "The sha256 digest of the NIM image, not the mutable tag."),
        ("endpoint_url", "Endpoint",
         "build.nvidia.com, or your own URL if the NIM is self-hosted."),
        ("quantization", "Optimisation profile and quantization",
         "Throughput or latency profile — quantization differs between them."),
        ("auth_type", "Authentication", "Usually api_key."),
    ),
    "aws_bedrock": (
        ("model_id", "Model ARN",
         "The ARN, not the friendly name. Use the custom or imported model ARN if "
         "this model was fine-tuned."),
        ("revision", "Model version or inference profile",
         "The version behind the ARN, and whether you call on-demand, with "
         "provisioned throughput, or through an inference profile."),
        ("endpoint_url", "Region",
         "Model availability and versions differ by region."),
        ("auth_type", "Authentication", "Usually aws_sigv4."),
        ("decoding_params", "Decoding settings",
         "temperature, top_p, max_tokens, plus the guardrail id and version if one "
         "is attached to the invocation."),
    ),
}
