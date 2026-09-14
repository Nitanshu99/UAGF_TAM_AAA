"""What the bootstrap decides for ``.env``, and how it tells a placeholder from a value."""
from __future__ import annotations

#: What the bootstrap decides: one provider for the agents and all three
#: embedding purposes, durable evidence, ReAct sequencing, no Flex tier.
FIXED: dict[str, str] = {
    "PROVIDER": "openrouter",
    "EMBEDDINGS_CLIENT_DOCS": "openrouter",
    "EMBEDDINGS_REGULATORY": "openrouter",
    "EMBEDDINGS_EVIDENCE": "openrouter",
    "EVIDENCE_BACKEND": "minio",
    "CGSA_FIXTURE_DIR": "mock:scripts/fixtures/cgsa",
    "AAA_ORCHESTRATION_MODE": "react",
    "AAA_DISABLE_FLEX": "true",
}
#: The model configuration the reference Mariposa result was produced with (wizard and CLI
#: runs of 2026-09-14 that agreed on every article). Written only where ``.env`` leaves the
#: key blank, so an explicit choice — including a deliberately different model — stands.
REFERENCE: dict[str, str] = {
    "OPENROUTER_MODEL": "minimax/minimax-m3",
    "OPENROUTER_PROVIDER": "coreweave/fp4",
}
#: Vendor keys ``.env.example`` ships as ``sk-...`` placeholders; a placeholder
#: reads as "configured" to the code, so it is blanked.
VENDOR_KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY",
               "MISTRAL_API_KEY", "NVIDIA_API_KEY")


def is_placeholder(value: str | None) -> bool:
    """True for blank, ``...``-style, ``changeme`` and all-zero example values.

    :param value: A ``.env`` value, or ``None`` when the key is absent.
    :returns: Whether the value is one of the example file's stand-ins.
    """
    text = (value or "").strip()
    return not text or text.endswith("...") or text.startswith("changeme") or set(text) == {"0"}


__all__ = ["FIXED", "REFERENCE", "VENDOR_KEYS", "is_placeholder"]
