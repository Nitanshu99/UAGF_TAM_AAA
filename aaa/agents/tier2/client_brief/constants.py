"""Prompt name and the plain-language vocabulary the client brief is written in."""
from __future__ import annotations

PROMPT_NAME = "client_brief"

#: Template id the assembled Markdown is stored under in the evidence store.
TEMPLATE_ID = "T19_client_brief"

#: What each obligation is *about*, in the reader's language. The brief is read
#: by the people who built the system, not by their counsel, so every section is
#: headed by the subject before the article number.
ARTICLE_TITLES: dict[str, str] = {
    "Art.5": "Prohibited AI practices",
    "Art.6": "Whether the system counts as high-risk",
    "Art.9": "Risk management system",
    "Art.10": "Data and data governance",
    "Art.10§2(f)": "Checking datasets for bias",
    "Art.11": "Technical documentation",
    "Art.12": "Automatic logging of what the system does",
    "Art.13": "Transparency toward the organisations deploying the system",
    "Art.14": "Human oversight",
    "Art.15": "Accuracy, robustness and cybersecurity",
    "Art.15§1": "Declared accuracy levels and metrics",
    "Art.17": "Quality management system",
    "Art.25": "Responsibilities along the AI value chain",
    "Art.27": "Fundamental rights impact assessment before deployment",
    "Art.43": "Conformity assessment before going to market",
    "Art.50": "Telling people they are interacting with an AI system",
    "Art.72": "Monitoring the system after it is on the market",
    "Annex_III": "The high-risk use case the system falls under",
    "Annex_IV": "What the technical documentation must contain",
    "GPAI_51": "General-purpose model classification",
    "GPAI_52": "General-purpose model notification duties",
    "GPAI_53": "General-purpose model provider obligations",
    "GPAI_54": "Authorised representative for GPAI providers",
    "GPAI_55": "Obligations for systemic-risk GPAI models",
    "Annex_XI": "Technical documentation for GPAI models",
    "Annex_XII": "Information passed to downstream providers",
}

#: How a matrix verdict is stated to the customer. INSUFFICIENT_EVIDENCE is not
#: a failure and must not read like one: it says the audit could not conclude on
#: what was supplied, which is a different fact with a different remedy.
VERDICT_LABELS: dict[str, str] = {
    "PASS": "Met",
    "PASS_WITH_OBSERVATIONS": "Met, with observations",
    "FAIL": "Not met",
    "INSUFFICIENT_EVIDENCE": "Could not be checked",
}

#: Worst first — the reader's first question is what is broken.
VERDICT_ORDER: tuple[str, ...] = (
    "FAIL", "INSUFFICIENT_EVIDENCE", "PASS_WITH_OBSERVATIONS", "PASS")


def article_title(article: str) -> str:
    """Return the plain-language subject of *article*, or the id itself.

    :param article: Matrix article key, e.g. ``"Art.10§2(f)"``.
    :returns: A short noun phrase naming what the obligation is about.
    """
    return ARTICLE_TITLES.get(article, article)


def verdict_label(verdict: str) -> str:
    """Return the customer-facing wording for a matrix *verdict*."""
    return VERDICT_LABELS.get(verdict, verdict)


def verdict_rank(verdict: str) -> int:
    """Sort key placing the worst verdict first."""
    return (VERDICT_ORDER.index(verdict) if verdict in VERDICT_ORDER
            else len(VERDICT_ORDER))
