"""Where a declared control's evidence comes from: the guardrail config and the RAG manifest."""
from __future__ import annotations

from typing import Any

from aaa.agents.tier3.uagf_tam_l.control_status import _STATUS_KEYS, control_status


def _guardrails(config: dict[str, Any]) -> dict[str, Any]:
    """Summarise a guardrail configuration as evidence."""
    status = control_status(config)
    return {
        "document": config.get("name"),
        "version": config.get("version"),
        "component": config.get("component"),
        "enforcement_points": config.get("enforcement_points") or [],
        "controls_declared": sorted(
            k for k, v in config.items()
            if k.endswith("guardrails") or k in ("transparency", "human_oversight",
                                                 "logging", "sensitive_disclosure_handling")
            if v),
        "implemented": status["implemented"],
        "partially_implemented": status["partial"],
        "declared_not_implemented": status["not_implemented"],
        "provider_note": (config.get(_STATUS_KEYS[0]) or {}).get("note")
        if isinstance(config.get(_STATUS_KEYS[0]), dict) else None,
    }
def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_name(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _retrieval(manifest: dict[str, Any]) -> dict[str, Any]:
    """Summarise a RAG manifest as evidence, in either dialect a provider writes.

    Case 06 nests ``embedding`` and ``vector_store`` as objects; case 04 names them
    (``"vector_store": "qdrant"``, ``"embedding_model": "…MiniLM…"``) and keeps its
    settings under ``retrieval_config``. The first reader assumed objects, and on
    case 04's manifest ``str.get`` raised before the L-branch reached its model —
    T16 was withheld and Art. 15 lost its evidence (2026-09-13).
    """
    embedding, store = manifest.get("embedding"), manifest.get("vector_store")
    config = _as_dict(manifest.get("retrieval_config"))
    return {
        "document": manifest.get("name"),
        "version": manifest.get("version"),
        "retrieval_type": manifest.get("retrieval_type") or config.get("type"),
        "embedding_provider": _as_dict(embedding).get("provider"),
        "embedding_model": (_as_dict(embedding).get("model") or _as_name(embedding)
                            or _as_name(manifest.get("embedding_model"))),
        "embedding_dimensions": _as_dict(embedding).get("dimensions"),
        "vector_store_engine": _as_dict(store).get("engine") or _as_name(store),
        "distance_metric": _as_dict(store).get("distance_metric") or config.get("distance_metric"),
        "reranker": config.get("reranker"),
        "generative_component_in_path": not manifest.get(
            "no_generative_component_in_this_path", False),
        "reference_taxonomies": [
            t.get("name") for t in (manifest.get("reference_taxonomies") or [])
            if isinstance(t, dict) and t.get("name")],
    }


__all__ = ["_guardrails", "_retrieval"]
