"""EUR-Lex HTML loader (EU AI Act, GDPR)."""
from __future__ import annotations

from pathlib import Path

from scripts.ingest_regulatory_corpus import config
from scripts.ingest_regulatory_corpus.deps import require
from scripts.ingest_regulatory_corpus.models import Unit, normalise_text


def load_html_units(path: Path, regulation: str) -> list[Unit]:
    """Parse an EUR-Lex HTML regulation into structural Units.

    :param path: HTML file exported from EUR-Lex.
    :param regulation: Regulation label recorded on each unit.
    :returns: Article, recital and annex units.
    """
    bs4 = require("bs4", "beautifulsoup4")
    soup = bs4.BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    units: list[Unit] = []
    source_file = path.name

    for div in soup.find_all("div", class_=config.EURLEX_ARTICLE_DIV, id=True):
        div_id = div.get("id", "")
        if not div_id.startswith(config.EURLEX_ARTICLE_ID_PREFIX):
            continue
        title_p = div.find("p", class_=config.EURLEX_ARTICLE_TITLE)
        if not title_p:
            continue
        ref = normalise_text(title_p.get_text(" ", strip=True))
        sub_p = div.find("p", class_=config.EURLEX_ARTICLE_SUBTITLE)
        title = normalise_text(sub_p.get_text(" ", strip=True)) if sub_p else ""
        text = normalise_text(div.get_text(" ", strip=True))
        if not text or len(text) < 20:
            continue
        units.append(Unit(regulation=regulation, kind="article", ref=ref, title=title,
                          text=text, source_file=source_file, extra={"html_id": div_id}))

    for div in soup.find_all("div", class_="eli-subdivision", id=True):
        div_id = div.get("id", "")
        if not div_id.startswith(config.EURLEX_RECITAL_ID_PREFIX):
            continue
        num = div_id.removeprefix(config.EURLEX_RECITAL_ID_PREFIX)
        text = normalise_text(div.get_text(" ", strip=True))
        if not text:
            continue
        units.append(Unit(regulation=regulation, kind="recital", ref=f"Recital {num}",
                          title="", text=text, source_file=source_file,
                          extra={"html_id": div_id}))

    for div in soup.find_all(id=True):
        div_id = div.get("id", "")
        if not div_id.startswith(config.EURLEX_ANNEX_ID_PREFIX):
            continue
        num = div_id.removeprefix(config.EURLEX_ANNEX_ID_PREFIX)
        text = normalise_text(div.get_text(" ", strip=True))
        if len(text) < 50:
            continue
        units.append(Unit(regulation=regulation, kind="annex", ref=f"Annex {num}",
                          title="", text=text, source_file=source_file,
                          extra={"html_id": div_id}))
    return units
