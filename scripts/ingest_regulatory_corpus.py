#!/usr/bin/env python3
"""
scripts/ingest_regulatory_corpus.py — Hybrid (dense + sparse) Qdrant ingestion
of the regulatory corpus consumed by Tier-1 RegulatoryRAG (§3.1 #3, §10).

Pipeline
--------
  0. Pre-load ``data/files/eu_ai_act_compliance_checker.json`` → build the
     article → {obligations, entity_types, risk_classes} lookup used to
     enrich each chunk's payload (§"checker lookup").
  1. Loaders — BeautifulSoup for EUR-Lex HTML (EU AI Act, GDPR),
     pdfplumber for ISO/IEC 42001 PDF. Each loader yields *structural
     units* (article, recital, annex, clause, control) — never raw text.
  2. Chunker — ``llama_index.core.node_parser.SentenceSplitter`` applied
     **per unit** so chunks never cross an article boundary.
  3. Dense embeddings — OpenAI ``text-embedding-3-large`` (dim=3072).
  4. Sparse embeddings — fastembed BM25 (``Qdrant/bm25``) for hybrid search.
  5. Qdrant collections:
       * ``--collection`` (default ``regulatory_corpus``) — named vectors
         {dense, sparse}, payload indexes on filter keys.
       * ``--obligations-collection`` (default ``obligations_index``) —
         dense-only mirror of the compliance-checker questionnaire.
  6. Idempotent upsert keyed by SHA-256 of the chunk text.

Usage
-----
    python3.12 scripts/ingest_regulatory_corpus.py \\
        --corpus data/regulatory_corpus \\
        --checker data/files/eu_ai_act_compliance_checker.json \\
        --collection regulatory_corpus \\
        --obligations-collection obligations_index

    # Dry run (parse + chunk + log counts; no Qdrant writes, no embedding calls)
    python3.12 scripts/ingest_regulatory_corpus.py --dry-run

    # Reset both collections before ingestion
    python3.12 scripts/ingest_regulatory_corpus.py --reset

Required env vars
-----------------
  OPENAI_API_KEY     OpenAI key for text-embedding-3-large (skipped in --dry-run)
  QDRANT_URL         default ``http://localhost:6333``
  QDRANT_API_KEY     optional (Qdrant Cloud)

Optional dependencies (install only when running for real)::

    pip install qdrant-client beautifulsoup4 lxml pdfplumber fastembed \\
                llama-index-embeddings-openai llama-index-vector-stores-qdrant
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator

# Load .env from the repo root early so OPENAI_API_KEY etc. are available
# without the caller having to manually `source .env` in the shell.
try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
except ImportError:
    pass  # python-dotenv not installed; env vars must be set externally

REPO_ROOT = Path(__file__).resolve().parents[1]

# ── Defaults ────────────────────────────────────────────────────────────────
DEFAULT_CORPUS_DIR = REPO_ROOT / "data" / "regulatory_corpus"
DEFAULT_CHECKER_PATH = REPO_ROOT / "data" / "eu_ai_act_compliance_checker.json"
DEFAULT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "regulatory_corpus")
DEFAULT_OBLIGATIONS_COLLECTION = "obligations_index"

DENSE_MODEL = "text-embedding-3-large"
DENSE_DIM = 3072
SPARSE_MODEL = "Qdrant/bm25"

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 100
EMBED_BATCH = 64
UPSERT_BATCH = 128

logger = logging.getLogger("ingest_regulatory_corpus")


# ── Pretty printing (matches scripts/setup.py style) ────────────────────────

def _step(n: int, total: int, msg: str) -> None:
    print(f"\n\033[1;36m[{n}/{total}] {msg}\033[0m", flush=True)


def _ok(msg: str) -> None:
    print(f"  \033[32m✓\033[0m {msg}", flush=True)


def _warn(msg: str) -> None:
    print(f"  \033[33m!\033[0m {msg}", flush=True)


def _err(msg: str) -> None:
    print(f"  \033[31m✗\033[0m {msg}", file=sys.stderr, flush=True)


# ── Domain types ────────────────────────────────────────────────────────────

@dataclass
class Unit:
    """A single structural unit of a regulation (article, recital, annex, clause)."""

    regulation: str            # "EU_AI_Act" | "GDPR" | "ISO_IEC_42001"
    kind: str                  # "article" | "recital" | "annex" | "clause" | "control"
    ref: str                   # "Article 9", "Recital 27", "Annex III", "6.1", "A.6.2"
    title: str                 # short heading, may be "" for recitals
    text: str                  # cleaned plain text
    source_file: str           # basename of the originating file
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """A chunk produced by the per-unit SentenceSplitter."""

    text: str
    payload: dict[str, Any]

    @property
    def point_id(self) -> str:
        """Deterministic UUID5-like ID derived from the chunk text + payload key fields."""
        h = hashlib.sha256()
        h.update(self.text.encode("utf-8"))
        h.update(self.payload.get("regulation", "").encode("utf-8"))
        h.update(self.payload.get("ref", "").encode("utf-8"))
        h.update(str(self.payload.get("chunk_index", 0)).encode("utf-8"))
        digest = h.hexdigest()
        # Qdrant accepts unsigned 64-bit integer IDs or UUID strings. Use UUID format.
        return f"{digest[0:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


# ── Lazy third-party imports ────────────────────────────────────────────────

def _require(modname: str, pip_name: str | None = None) -> Any:
    """Import *modname* with a friendly error if the package is missing."""
    try:
        return __import__(modname, fromlist=["*"])
    except ImportError as exc:
        pkg = pip_name or modname.split(".")[0]
        raise SystemExit(
            f"missing optional dependency '{pkg}' required for ingestion.\n"
            f"  install: pip install {pkg}\n  (original error: {exc})"
        ) from exc


# ── Compliance-checker lookup (Step 0) ──────────────────────────────────────

# "Article 9", "Article 9 point 2", "Article 50 point 1",
# "Annex III" / "Annex 3", "Recital 27"
_REF_RE = re.compile(
    r"(Article\s+\d+(?:\s+point\s+\d+)?|Annex\s+(?:[IVX]+|\d+)|Recital\s+\d+)",
    re.IGNORECASE,
)

_ARABIC_TO_ROMAN = {
    "1": "I", "2": "II", "3": "III", "4": "IV", "5": "V",
    "6": "VI", "7": "VII", "8": "VIII", "9": "IX", "10": "X",
    "11": "XI", "12": "XII", "13": "XIII",
}


def _canon_ref(raw: str) -> str:
    """Canonicalise a citation: ``Article 50 point 1``, ``Annex III``, ``Recital 27``."""
    raw = re.sub(r"\s+", " ", raw).strip()
    m = re.match(r"(article|annex|recital)\s+(.+)", raw, re.IGNORECASE)
    if not m:
        return raw
    head = m.group(1).capitalize()
    tail = m.group(2)
    if head == "Annex":
        tail = _ARABIC_TO_ROMAN.get(tail.strip(), tail.upper())
    else:
        tail = re.sub(r"\bpoint\b", "point", tail, flags=re.IGNORECASE)
    return f"{head} {tail}"


def _parse_refs(source: str | None) -> list[str]:
    """Extract canonical Article/Recital/Annex citations from a free-text ``source`` field."""
    if not source:
        return []
    return [_canon_ref(m.group(1)) for m in _REF_RE.finditer(source)]


def _walk_answer(answer: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    """Collect obligations/entity_types/status_changes from an answer (recurses into conditions)."""
    obligations: set[str] = set()
    entity_types: set[str] = set()
    status_changes: set[str] = set()

    if isinstance(answer.get("obligations"), list):
        obligations.update(answer["obligations"])
    if isinstance(answer.get("status_change"), str):
        status_changes.add(answer["status_change"])
    if isinstance(answer.get("visibility"), str):
        entity_types.update(s.strip() for s in answer["visibility"].split(","))

    conditions = answer.get("conditions") or {}
    if isinstance(conditions, dict):
        for cond_value in conditions.values():
            if isinstance(cond_value, dict):
                o, e, s = _walk_answer(cond_value)  # recursive — same shape
                obligations |= o
                entity_types |= e
                status_changes |= s
    return obligations, entity_types, status_changes


@dataclass
class CheckerLookup:
    """In-memory indexes derived from ``eu_ai_act_compliance_checker.json``."""

    # ref ("Article 9") → {"obligations": [...], "entity_types": [...], "risk_classes": [...]}
    by_article: dict[str, dict[str, list[str]]]
    # obligation name → metadata block from the top-level "obligations" dict
    obligations_catalogue: dict[str, dict[str, Any]]
    # raw question records used to populate the obligations_index collection
    questions: list[dict[str, Any]]

    def for_ref(self, ref: str) -> dict[str, list[str]]:
        """Return the enrichment payload for a canonical ref (article/recital/annex)."""
        return self.by_article.get(ref, {"obligations": [], "entity_types": [], "risk_classes": []})


def build_checker_lookup(path: Path) -> CheckerLookup:
    """Parse the compliance-checker JSON into the article→obligations index."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    by_article: dict[str, dict[str, set[str]]] = {}
    questions: list[dict[str, Any]] = []

    for section in raw.get("sections", []):
        section_id = section.get("id", "")
        section_title = section.get("title", "")
        for q in section.get("questions", []):
            q_refs = _parse_refs(q.get("source"))
            q_obligations: set[str] = set()
            q_entities: set[str] = set()
            q_status: set[str] = set()
            for ans in q.get("answers", []):
                o, e, s = _walk_answer(ans)
                q_obligations |= o
                q_entities |= e
                q_status |= s
            for ref in q_refs:
                bucket = by_article.setdefault(
                    ref, {"obligations": set(), "entity_types": set(), "risk_classes": set()}
                )
                bucket["obligations"] |= q_obligations
                bucket["entity_types"] |= q_entities
                bucket["risk_classes"] |= q_status
            questions.append({
                "section_id": section_id,
                "section_title": section_title,
                "question_id": q.get("id", ""),
                "text": q.get("text", ""),
                "hint": q.get("hint", ""),
                "source": q.get("source", ""),
                "refs": q_refs,
                "obligations": sorted(q_obligations),
                "entity_types": sorted(q_entities),
                "risk_classes": sorted(q_status),
            })

    # Fold the top-level "obligations" catalogue into the per-article index too.
    catalogue = raw.get("obligations", {}) or {}
    for name, meta in catalogue.items():
        for ref in _parse_refs(meta.get("source")):
            bucket = by_article.setdefault(
                ref, {"obligations": set(), "entity_types": set(), "risk_classes": set()}
            )
            bucket["obligations"].add(name)
            for ent in meta.get("applies_to", []) or []:
                bucket["entity_types"].add(ent)

    return CheckerLookup(
        by_article={
            ref: {k: sorted(v) for k, v in payload.items()}
            for ref, payload in by_article.items()
        },
        obligations_catalogue=catalogue,
        questions=questions,
    )


# ── Loaders (Step 1) ────────────────────────────────────────────────────────

_REGULATION_BY_STEM = {
    "EU_AI_Act": "EU_AI_Act",
    "GDPR": "GDPR",
}

_PDF_REGULATION_BY_NAME = {
    "ISO:IEC 42001-2023.pdf": "ISO_IEC_42001",
    "isae_3000.pdf": "ISAE 3000",
    "iso_19011.pdf": "ISO 19011",
}

_REQUIRED_STANDARD_PDFS = {
    "isae_3000.pdf": "ISAE 3000 (Revised)",
    "iso_19011.pdf": "ISO 19011:2018",
}

COVERAGE_PROBE_QUERIES = [
    "ISAE 3000 assurance engagement objectives reasonable assurance",
    "ISO 19011 audit programme planning audit criteria",
]

# EUR-Lex HTML uses these classes/ids consistently across regulations
_EURLEX_ARTICLE_DIV = "eli-subdivision"
_EURLEX_ARTICLE_TITLE = "oj-ti-art"      # e.g. "Article 9"
_EURLEX_ARTICLE_SUBTITLE = "oj-sti-art"  # e.g. "Risk management system"
_EURLEX_RECITAL_ID_PREFIX = "rct_"
_EURLEX_ARTICLE_ID_PREFIX = "art_"
_EURLEX_ANNEX_ID_PREFIX = "anx_"


def _normalise_text(text: str) -> str:
    """Collapse whitespace and strip the unicode artefacts EUR-Lex emits."""
    text = text.replace("\xa0", " ").replace("\u2003", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_html_units(path: Path, regulation: str) -> list[Unit]:
    """Parse an EUR-Lex HTML regulation into structural Units."""
    bs4 = _require("bs4", "beautifulsoup4")
    BeautifulSoup = bs4.BeautifulSoup  # noqa: N806

    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    units: list[Unit] = []
    source_file = path.name

    # Articles
    for div in soup.find_all("div", class_=_EURLEX_ARTICLE_DIV, id=True):
        div_id = div.get("id", "")
        if not div_id.startswith(_EURLEX_ARTICLE_ID_PREFIX):
            continue
        title_p = div.find("p", class_=_EURLEX_ARTICLE_TITLE)
        if not title_p:
            continue
        ref = _normalise_text(title_p.get_text(" ", strip=True))
        sub_p = div.find("p", class_=_EURLEX_ARTICLE_SUBTITLE)
        title = _normalise_text(sub_p.get_text(" ", strip=True)) if sub_p else ""
        text = _normalise_text(div.get_text(" ", strip=True))
        if not text or len(text) < 20:
            continue
        units.append(Unit(
            regulation=regulation, kind="article", ref=ref, title=title,
            text=text, source_file=source_file, extra={"html_id": div_id},
        ))

    # Recitals
    for div in soup.find_all("div", class_="eli-subdivision", id=True):
        div_id = div.get("id", "")
        if not div_id.startswith(_EURLEX_RECITAL_ID_PREFIX):
            continue
        num = div_id.removeprefix(_EURLEX_RECITAL_ID_PREFIX)
        text = _normalise_text(div.get_text(" ", strip=True))
        if not text:
            continue
        units.append(Unit(
            regulation=regulation, kind="recital", ref=f"Recital {num}", title="",
            text=text, source_file=source_file, extra={"html_id": div_id},
        ))

    # Annexes
    for div in soup.find_all(id=True):
        div_id = div.get("id", "")
        if not div_id.startswith(_EURLEX_ANNEX_ID_PREFIX):
            continue
        num = div_id.removeprefix(_EURLEX_ANNEX_ID_PREFIX)
        text = _normalise_text(div.get_text(" ", strip=True))
        if len(text) < 50:
            continue
        units.append(Unit(
            regulation=regulation, kind="annex", ref=f"Annex {num}", title="",
            text=text, source_file=source_file, extra={"html_id": div_id},
        ))

    return units


# ISO/IEC 42001 clause / Annex A control heading patterns
_ISO_CLAUSE_RE = re.compile(r"^\s*(\d+(?:\.\d+){0,3})\s+([A-Za-z][A-Za-z0-9 ,\-:/&()]+)\s*$")
_ISO_CONTROL_RE = re.compile(r"^\s*(A\.\d+(?:\.\d+){0,2})\s+([A-Za-z][A-Za-z0-9 ,\-:/&()]+)\s*$")
_ISO_CLAUSE_NUM_RE = re.compile(r"^\s*(\d+(?:\.\d+){0,3})\s*$")
_ISO_CONTROL_NUM_RE = re.compile(r"^\s*(A\.\d+(?:\.\d+){0,2})\s*$")
_ISO_TITLE_HEAD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 ,\-:/&()]+$")
_ISO_PAGE_NOISE_RE = re.compile(r"^(ISO/IEC\s+42001[:\d\s()E\-]*|\(E\)|\d{1,4})$", re.IGNORECASE)

_ISAE_PARAGRAPH_RE = re.compile(r"^(A?\d+)\.\s+(.*)$")
_ISAE_PAGE_NOISE_RE = re.compile(
    r"^(\d{1,3}|ASSURANCE ENGAGEMENTS OTHER THAN AUDITS OR|"
    r"REVIEWS OF HISTORICAL FINANCIAL INFORMATION|ISAE 3000 \(REVISED\))$",
    re.IGNORECASE,
)


def _pdf_lines_by_page(path: Path) -> list[tuple[int, list[str]]]:
    """Extract non-empty text lines from *path* using the pypdfium2 backend."""
    pdfium = _require("pypdfium2")
    pages: list[tuple[int, list[str]]] = []
    doc = pdfium.PdfDocument(str(path))
    try:
        for page_no, page in enumerate(doc, start=1):
            tp = page.get_textpage()
            try:
                text = tp.get_text_bounded() or ""
            finally:
                tp.close()
                page.close()
            lines = [raw.strip() for raw in text.splitlines() if raw.strip()]
            pages.append((page_no, lines))
    finally:
        doc.close()
    return pages


def load_pdf_units(path: Path, regulation: str = "ISO_IEC_42001") -> list[Unit]:
    """Parse the ISO/IEC 42001 PDF into clause + Annex-A control Units.

    Uses pypdfium2 because pdfminer-based readers (pdfplumber, pypdf) silently
    return zero pages on PDFs that use newline-separated object headers, as
    produced by the PDF Tools AG toolchain ISO ships its standards through.
    """
    pdfium = _require("pypdfium2")
    source_file = path.name

    lines: list[str] = []
    doc = pdfium.PdfDocument(str(path))
    try:
        for page in doc:
            tp = page.get_textpage()
            try:
                page_text = tp.get_text_bounded() or ""
            finally:
                tp.close()
                page.close()
            for raw in page_text.splitlines():
                stripped = raw.strip()
                if not stripped or _ISO_PAGE_NOISE_RE.match(stripped):
                    continue
                lines.append(stripped)
    finally:
        doc.close()

    if not lines:
        _warn(f"{path.name}: pypdfium2 extracted no text — PDF may be scan-only")
        return []

    units: list[Unit] = []
    current_ref = ""
    current_title = ""
    current_kind = ""
    buf: list[str] = []

    def _flush() -> None:
        if current_ref and buf:
            text = _normalise_text(" ".join(buf))
            if len(text) >= 40:
                units.append(Unit(
                    regulation=regulation, kind=current_kind, ref=current_ref,
                    title=current_title, text=text, source_file=source_file,
                ))

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m_ctrl = _ISO_CONTROL_RE.match(line)
        m_clause = _ISO_CLAUSE_RE.match(line)
        m_ctrl_num = _ISO_CONTROL_NUM_RE.match(line)
        m_clause_num = _ISO_CLAUSE_NUM_RE.match(line)
        if m_ctrl:
            _flush()
            buf = []
            current_ref = m_ctrl.group(1)
            current_title = m_ctrl.group(2).strip()
            current_kind = "control"
        elif m_clause and int(m_clause.group(1).split(".")[0]) in range(4, 11):
            _flush()
            buf = []
            current_ref = m_clause.group(1)
            current_title = m_clause.group(2).strip()
            current_kind = "clause"
        elif m_ctrl_num and i + 1 < n and _ISO_TITLE_HEAD_RE.match(lines[i + 1]):
            _flush()
            buf = []
            current_ref = m_ctrl_num.group(1)
            current_title = lines[i + 1].strip()
            current_kind = "control"
            i += 1
        elif (m_clause_num
              and int(m_clause_num.group(1).split(".")[0]) in range(4, 11)
              and i + 1 < n
              and _ISO_TITLE_HEAD_RE.match(lines[i + 1])):
            _flush()
            buf = []
            current_ref = m_clause_num.group(1)
            current_title = lines[i + 1].strip()
            current_kind = "clause"
            i += 1
        else:
            buf.append(line)
        i += 1
    _flush()
    return units


def _is_isae_heading(line: str) -> bool:
    """Return True for ISAE section headings such as Objectives or Obtaining Evidence."""
    if _ISAE_PAGE_NOISE_RE.match(line) or _ISAE_PARAGRAPH_RE.match(line):
        return False
    if len(line) > 100 or line.endswith(".") or "........" in line:
        return False
    words = line.split()
    if not 1 <= len(words) <= 10:
        return False
    return line[:1].isupper() and any(ch.isalpha() for ch in line)


def load_isae_3000_units(path: Path, regulation: str = "ISAE 3000") -> list[Unit]:
    """Parse ISAE 3000 into paragraph/application-material Units.

    Parser investigation (2026-06-01): the ISO/IEC 42001 clause parser extracted
    only 10 oversized, mislabelled units from ``isae_3000.pdf``. ISAE 3000 is
    paragraph-numbered, so this loader segments on ``1.`` / ``A1.`` paragraph
    markers and carries the nearest section heading as the unit title.
    """
    source_file = path.name
    units: list[Unit] = []
    current_ref = ""
    current_title = ""
    current_kind = "paragraph"
    start_page = 0
    buf: list[str] = []

    def _flush() -> None:
        if not current_ref or not buf:
            return
        text = _normalise_text(" ".join(buf))
        if len(text) < 40:
            return
        units.append(Unit(
            regulation=regulation,
            kind=current_kind,
            ref=current_ref,
            title=current_title,
            text=text,
            source_file=source_file,
            extra={"page": start_page},
        ))

    for page_no, lines in _pdf_lines_by_page(path):
        for line in lines:
            if _ISAE_PAGE_NOISE_RE.match(line):
                continue
            match = _ISAE_PARAGRAPH_RE.match(line)
            if match:
                _flush()
                current_ref = match.group(1)
                current_kind = "application" if current_ref.startswith("A") else "paragraph"
                start_page = page_no
                buf = [match.group(2)]
                continue
            if _is_isae_heading(line):
                current_title = line
                continue
            if current_ref:
                buf.append(line)
    _flush()
    return units


def load_units_for_path(path: Path, regulation: str | None = None) -> list[Unit]:
    """Dispatch a corpus source file to the correct structural-unit loader."""
    regulation = regulation or _PDF_REGULATION_BY_NAME.get(
        path.name, _REGULATION_BY_STEM.get(path.stem.replace(" ", "_"), path.stem)
    )
    suffix = path.suffix.lower()
    if suffix == ".html":
        return load_html_units(path, regulation)
    if suffix == ".pdf" and regulation == "ISAE 3000":
        return load_isae_3000_units(path, regulation)
    if suffix == ".pdf":
        return load_pdf_units(path, regulation)
    if suffix in {".txt", ".md"}:
        text = _normalise_text(path.read_text(encoding="utf-8"))
        return [Unit(regulation=regulation, kind="standard", ref="Document", title="", text=text,
                     source_file=path.name)] if text else []
    return []


def discover_corpus(corpus_dir: Path) -> Iterator[tuple[Path, str, str]]:
    """Yield (path, regulation, loader_kind) for every file in *corpus_dir*."""
    missing = [name for name in _REQUIRED_STANDARD_PDFS if not (corpus_dir / name).exists()]
    allow_stub = os.environ.get("AAA_ALLOW_ISO19011_STUB", "false").lower() == "true"
    if missing and not allow_stub:
        labels = ", ".join(f"{name} ({_REQUIRED_STANDARD_PDFS[name]})" for name in missing)
        raise SystemExit(f"missing required standards PDF(s) in {corpus_dir}: {labels}")
    for p in sorted(corpus_dir.iterdir()):
        if p.suffix.lower() == ".html":
            stem = p.stem.replace(" ", "_")
            yield p, _REGULATION_BY_STEM.get(stem, stem), "html"
        elif p.suffix.lower() == ".pdf":
            regulation = _PDF_REGULATION_BY_NAME.get(p.name)
            if regulation:
                yield p, regulation, "pdf"


# ── Chunker (Step 2) ────────────────────────────────────────────────────────

def chunk_units(
    units: list[Unit],
    checker: CheckerLookup,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """Run ``SentenceSplitter`` *per unit* so chunks never cross legal boundaries."""
    li_node_parser = _require(
        "llama_index.core.node_parser", "llama-index"
    )
    li_schema = _require("llama_index.core.schema", "llama-index")
    splitter = li_node_parser.SentenceSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap,
    )

    chunks: list[Chunk] = []
    for unit in units:
        nodes = splitter.get_nodes_from_documents(
            [li_schema.Document(text=unit.text)]
        )
        enrich = checker.for_ref(unit.ref)
        for i, node in enumerate(nodes):
            chunks.append(Chunk(
                text=node.get_content(),
                payload={
                    "regulation": unit.regulation,
                    "kind": unit.kind,
                    "ref": unit.ref,
                    "title": unit.title,
                    "source_file": unit.source_file,
                    "chunk_index": i,
                    "chunk_total": len(nodes),
                    "obligations": enrich["obligations"],
                    "entity_types": enrich["entity_types"],
                    "risk_classes": enrich["risk_classes"],
                },
            ))
    return chunks


# ── Embedders (Steps 3 + 4) ─────────────────────────────────────────────────

def _batched(seq: list[Any], size: int) -> Iterable[list[Any]]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def dense_embed(texts: list[str], model: str = DENSE_MODEL) -> list[list[float]]:
    """Embed *texts* with OpenAI ``text-embedding-3-large`` (batched)."""
    openai = _require("openai")
    client = openai.OpenAI()  # picks up OPENAI_API_KEY from env
    vectors: list[list[float]] = []
    for batch in _batched(texts, EMBED_BATCH):
        resp = client.embeddings.create(model=model, input=batch)
        vectors.extend([item.embedding for item in resp.data])
    return vectors


def sparse_embed(texts: list[str]) -> list[dict[str, list]]:
    """Embed *texts* with fastembed BM25; returns ``[{indices: [...], values: [...]}, ...]``."""
    fe = _require("fastembed")
    encoder = fe.SparseTextEmbedding(model_name=SPARSE_MODEL)
    out: list[dict[str, list]] = []
    for emb in encoder.embed(texts):
        out.append({"indices": emb.indices.tolist(), "values": emb.values.tolist()})
    return out


# ── Qdrant writer (Step 5 + 6) ──────────────────────────────────────────────

_FILTER_KEYS = ("regulation", "kind", "ref", "obligations",
                "entity_types", "risk_classes", "source_file")


def _qdrant_client() -> Any:
    """Construct a Qdrant client from QDRANT_URL / QDRANT_API_KEY env vars."""
    qmod = _require("qdrant_client")
    url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    api_key = os.environ.get("QDRANT_API_KEY") or None
    return qmod.QdrantClient(url=url, api_key=api_key, prefer_grpc=False)


def ensure_corpus_collection(client: Any, name: str, reset: bool = False) -> None:
    """Create the hybrid (dense + sparse) collection and payload indexes."""
    qmodels = _require("qdrant_client.models")
    exists = client.collection_exists(name)
    if exists and reset:
        client.delete_collection(name)
        exists = False
    if not exists:
        client.create_collection(
            collection_name=name,
            vectors_config={
                "dense": qmodels.VectorParams(
                    size=DENSE_DIM, distance=qmodels.Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                "sparse": qmodels.SparseVectorParams(
                    index=qmodels.SparseIndexParams(on_disk=False),
                ),
            },
        )
    for key in _FILTER_KEYS:
        try:
            client.create_payload_index(
                collection_name=name,
                field_name=key,
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )
        except Exception:  # pragma: no cover - index already exists
            pass


def ensure_obligations_collection(client: Any, name: str, reset: bool = False) -> None:
    """Create the dense-only obligations_index collection."""
    qmodels = _require("qdrant_client.models")
    exists = client.collection_exists(name)
    if exists and reset:
        client.delete_collection(name)
        exists = False
    if not exists:
        client.create_collection(
            collection_name=name,
            vectors_config=qmodels.VectorParams(
                size=DENSE_DIM, distance=qmodels.Distance.COSINE,
            ),
        )
    for key in ("section_id", "question_id", "refs", "obligations",
                "entity_types", "risk_classes"):
        try:
            client.create_payload_index(
                collection_name=name,
                field_name=key,
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )
        except Exception:  # pragma: no cover
            pass


def upsert_corpus_chunks(
    client: Any,
    collection: str,
    chunks: list[Chunk],
    dense_vectors: list[list[float]],
    sparse_vectors: list[dict[str, list]],
) -> int:
    """Upsert chunks into the hybrid collection in batches; returns count written."""
    qmodels = _require("qdrant_client.models")
    written = 0
    for batch in _batched(list(range(len(chunks))), UPSERT_BATCH):
        points = []
        for i in batch:
            sv = sparse_vectors[i]
            points.append(qmodels.PointStruct(
                id=chunks[i].point_id,
                payload={**chunks[i].payload, "text": chunks[i].text},
                vector={
                    "dense": dense_vectors[i],
                    "sparse": qmodels.SparseVector(
                        indices=sv["indices"], values=sv["values"],
                    ),
                },
            ))
        client.upsert(collection_name=collection, points=points, wait=True)
        written += len(points)
    return written


def upsert_obligation_questions(
    client: Any,
    collection: str,
    questions: list[dict[str, Any]],
    dense_vectors: list[list[float]],
) -> int:
    """Upsert one point per compliance-checker question."""
    qmodels = _require("qdrant_client.models")
    written = 0
    for batch in _batched(list(range(len(questions))), UPSERT_BATCH):
        points = []
        for i in batch:
            q = questions[i]
            qid = q.get("question_id", "") or f"q{i}"
            d = hashlib.sha256(qid.encode("utf-8")).hexdigest()
            point_id = f"{d[0:8]}-{d[8:12]}-{d[12:16]}-{d[16:20]}-{d[20:32]}"
            points.append(qmodels.PointStruct(
                id=point_id,
                payload=q,
                vector=dense_vectors[i],
            ))
        client.upsert(collection_name=collection, points=points, wait=True)
        written += len(points)
    return written


# ── CLI + main() (Step 7) ───────────────────────────────────────────────────

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Ingest the regulatory corpus into Qdrant (hybrid dense + sparse).",
    )
    p.add_argument(
        "--corpus", type=Path, default=DEFAULT_CORPUS_DIR,
        help="directory of HTML/PDF regulations",
    )
    p.add_argument(
        "--checker", type=Path, default=DEFAULT_CHECKER_PATH,
        help="path to eu_ai_act_compliance_checker.json",
    )
    p.add_argument(
        "--collection", default=DEFAULT_COLLECTION,
        help="Qdrant corpus collection name",
    )
    p.add_argument(
        "--obligations-collection", default=DEFAULT_OBLIGATIONS_COLLECTION,
        help="Qdrant obligations index collection name",
    )
    p.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    p.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    p.add_argument("--dry-run", action="store_true",
                   help="parse + chunk + log counts only; no embedding calls, no Qdrant writes")
    p.add_argument("--reset", action="store_true",
                   help="drop and recreate both collections before ingest")
    p.add_argument("--skip-obligations", action="store_true",
                   help="skip the obligations_index collection")
    p.add_argument("--force-reembed", action="store_true",
                   help="re-embed and overwrite ALL chunks even if they already exist in Qdrant "
                        "(default: skip chunks whose SHA-256 ID is already present)")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
    )


def _load_all_units(corpus_dir: Path) -> list[Unit]:
    """Discover the corpus directory and dispatch to the right loader."""
    units: list[Unit] = []
    for path, regulation, kind in discover_corpus(corpus_dir):
        loaded = load_units_for_path(path, regulation)
        if loaded:
            _ok(f"loaded {len(loaded):4d} units from {path.name} ({regulation})")
        else:
            _warn(f"loaded    0 units from {path.name} ({regulation}) — check parser/format")
        units.extend(loaded)
    return units


def _question_point_id(question_id: str) -> str:
    """Return the deterministic UUID string used for an obligation question point."""
    d = hashlib.sha256(question_id.encode("utf-8")).hexdigest()
    return f"{d[0:8]}-{d[8:12]}-{d[12:16]}-{d[16:20]}-{d[20:32]}"


def _filter_new_questions(
    questions: list[dict[str, Any]], existing_ids: set[str]
) -> list[dict[str, Any]]:
    """Return only questions whose point ID is not already in *existing_ids*."""
    return [
        q for q in questions
        if _question_point_id(q.get("question_id", "") or "") not in existing_ids
    ]


def _fetch_existing_ids(client: Any, collection: str) -> set[str]:
    """Return the set of all point IDs already stored in *collection*.

    Uses ``scroll`` with no filter to page through every record.  Only the ID
    is fetched (``with_payload=False``, ``with_vectors=False``) so this is
    fast and cheap even for large collections.
    Returns an empty set if the collection does not yet exist.
    """
    try:
        existing: set[str] = set()
        offset = None
        while True:
            result, next_offset = client.scroll(
                collection_name=collection,
                offset=offset,
                limit=1000,
                with_payload=False,
                with_vectors=False,
            )
            for point in result:
                existing.add(str(point.id))
            if next_offset is None:
                break
            offset = next_offset
        return existing
    except Exception:  # collection missing or connection error  # pragma: no cover
        return set()


def _summarise(chunks: list[Chunk]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in chunks:
        key = f"{c.payload['regulation']}/{c.payload['kind']}"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _ingest_corpus(args: Any, client: Any, chunks: list[Chunk]) -> None:
    """Steps 4–5: embed and upsert corpus chunks, skipping already-present ones."""
    ensure_corpus_collection(client, args.collection, reset=args.reset)

    if args.force_reembed:
        new_chunks = chunks
        _warn("--force-reembed: embedding ALL chunks (ignoring existing Qdrant points)")
    else:
        existing_ids = _fetch_existing_ids(client, args.collection)
        new_chunks = [c for c in chunks if c.point_id not in existing_ids]
        skipped = len(chunks) - len(new_chunks)
        if skipped:
            _ok(f"skip {skipped} chunks already in Qdrant "
                f"(re-run with --force-reembed to overwrite)")
        if not new_chunks:
            _ok("all chunks already present — nothing to embed")

    dense: list[list[float]] = []
    sparse: list[dict[str, list]] = []
    if new_chunks:
        chunk_texts = [c.text for c in new_chunks]
        dense = dense_embed(chunk_texts)
        _ok(f"dense vectors: {len(dense)} × {len(dense[0]) if dense else 0}")
        sparse = sparse_embed(chunk_texts)
        _ok(f"sparse vectors: {len(sparse)}")

    written = upsert_corpus_chunks(client, args.collection, new_chunks, dense, sparse)
    _ok(f"upserted {written} new points into '{args.collection}'")


def _ingest_obligations(args: Any, client: Any, checker: "CheckerLookup") -> None:
    """Step 6: embed and upsert obligation questions, skipping already-present ones."""
    ensure_obligations_collection(client, args.obligations_collection, reset=args.reset)

    if args.force_reembed:
        new_questions = checker.questions
    else:
        existing_q_ids = _fetch_existing_ids(client, args.obligations_collection)
        new_questions = _filter_new_questions(checker.questions, existing_q_ids)
        if len(new_questions) < len(checker.questions):
            _ok(f"skip {len(checker.questions) - len(new_questions)} obligation questions "
                "already in Qdrant")

    q_dense: list[list[float]] = []
    if new_questions:
        q_texts = [
            f"{q['question_id']} ({q['source']}): {q['text']}" for q in new_questions
        ]
        q_dense = dense_embed(q_texts)

    n_q = upsert_obligation_questions(
        client, args.obligations_collection, new_questions, q_dense,
    )
    _ok(f"upserted {n_q} obligation-question points into '{args.obligations_collection}'")


def _run_coverage_probes(client: Any, collection: str) -> None:
    """Warn when the newly-added standards cannot be retrieved from Qdrant."""
    from qdrant_client import models as qmodels

    dense_vectors = dense_embed(COVERAGE_PROBE_QUERIES)
    sparse_vectors = sparse_embed(COVERAGE_PROBE_QUERIES)
    for query, dense_vec, sparse_vec in zip(
        COVERAGE_PROBE_QUERIES, dense_vectors, sparse_vectors, strict=True,
    ):
        try:
            response = client.query_points(
                collection_name=collection,
                prefetch=[
                    qmodels.Prefetch(query=dense_vec, using="dense", limit=16),
                    qmodels.Prefetch(
                        query=qmodels.SparseVector(
                            indices=sparse_vec["indices"], values=sparse_vec["values"],
                        ),
                        using="sparse",
                        limit=16,
                    ),
                ],
                query=qmodels.FusionQuery(fusion=qmodels.Fusion.RRF),
                limit=3,
                with_payload=True,
            )
            if not response.points:
                logger.warning("coverage probe returned zero results: %s", query)
        except Exception as exc:  # pragma: no cover - operational warning only
            logger.warning("coverage probe failed for %r: %s", query, exc)


def main(argv: list[str] | None = None) -> int:
    """End-to-end ingestion: load → chunk → embed → upsert."""
    args = _parse_args(argv)
    _setup_logging(args.verbose)
    total_steps = 6

    # Eagerly import heavy optional deps so they're cached in sys.modules before
    # any long corpus-loading work begins.  This avoids a cold-import delay
    # happening mid-run (which can appear as a silent hang or SIGINT delivery
    # from a watching process).
    print("  warming up imports …", end=" ", flush=True)
    # llama_index SentenceSplitter lazily loads NLTK → sklearn → numpy on first
    # *use*, not on first import.  Trigger that chain now so it's cached.
    # sklearn's array_api_compat does `from numpy import *` which is slow on
    # macOS cold-start; pre-importing numpy caches it so the wildcard import
    # is fast.
    try:
        import numpy   # noqa: F401
        import sklearn  # noqa: F401
        import nltk    # noqa: F401
    except ImportError:
        pass
    _require("llama_index.core.node_parser")
    if not args.dry_run:
        _require("qdrant_client")
        _require("openai")
        _require("fastembed")
    print("ok", flush=True)

    _step(1, total_steps, "Building compliance-checker lookup")
    checker = build_checker_lookup(args.checker)
    _ok(f"indexed {len(checker.by_article)} refs · "
        f"{len(checker.obligations_catalogue)} obligations · "
        f"{len(checker.questions)} questions")

    _step(2, total_steps, f"Loading corpus from {args.corpus}")
    units = _load_all_units(args.corpus)
    if not units:
        _err("no units parsed — aborting")
        return 1

    _step(3, total_steps, "Chunking units (per-unit SentenceSplitter)")
    chunks = chunk_units(
        units, checker,
        chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap,
    )
    for key, n in sorted(_summarise(chunks).items()):
        _ok(f"{key:40s} → {n} chunks")
    _ok(f"total chunks: {len(chunks)}")

    if args.dry_run:
        _warn("--dry-run: skipping embeddings and Qdrant writes")
        return 0

    client = _qdrant_client()

    _step(4, total_steps, "Computing dense + sparse embeddings (skipping existing)")
    _step(5, total_steps, "Upserting corpus chunks into Qdrant")
    _ingest_corpus(args, client, chunks)

    if args.skip_obligations:
        _warn("--skip-obligations: skipping obligations_index collection")
        return 0

    _step(6, total_steps, "Upserting obligations_index from compliance-checker")
    _ingest_obligations(args, client, checker)
    _run_coverage_probes(client, args.collection)

    return 0


if __name__ == "__main__":
    sys.exit(main())
