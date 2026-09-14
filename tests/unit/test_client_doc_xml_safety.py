"""Client-uploaded DOCX must not be able to drive XML entity expansion."""
from __future__ import annotations

import io
import zipfile

import pytest

from aaa.tools.client_doc_ingest.extract import _extract_docx_pages
from aaa.tools.client_doc_ingest.xml_safety import UnsafeXMLError, reject_dtd

_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_BOMB = b"""<?xml version="1.0"?><!DOCTYPE lolz [
 <!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
]><w:document xmlns:w="%s"><w:t>&lol2;</w:t></w:document>""" % _NS.encode()

_BENIGN = b"""<?xml version="1.0"?><w:document xmlns:w="%s">
 <w:t>Annex III high-risk classification</w:t></w:document>""" % _NS.encode()


def _docx(document_xml: bytes) -> bytes:
    """Build a minimal in-memory DOCX around *document_xml*."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
    return buf.getvalue()


def test_reject_dtd_raises_on_doctype():
    """A DTD declaration is refused rather than expanded."""
    with pytest.raises(UnsafeXMLError):
        reject_dtd(_BOMB)


def test_reject_dtd_allows_plain_xml():
    """XML without a DTD passes through untouched."""
    assert reject_dtd(_BENIGN) is None


def test_docx_with_dtd_is_rejected(monkeypatch):
    """The raw-XML fallback refuses an entity-bomb DOCX."""
    monkeypatch.setitem(__import__("sys").modules, "docx", None)
    with pytest.raises(UnsafeXMLError):
        _extract_docx_pages(_docx(_BOMB))


def test_benign_docx_still_extracts(monkeypatch):
    """A DTD-free DOCX still yields its text through the fallback."""
    monkeypatch.setitem(__import__("sys").modules, "docx", None)
    pages = _extract_docx_pages(_docx(_BENIGN))
    assert "Annex III high-risk classification" in pages[0][1]
