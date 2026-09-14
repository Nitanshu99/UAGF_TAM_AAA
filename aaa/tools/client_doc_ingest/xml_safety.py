"""Guards for parsing XML that arrived from a client upload.

``xml.etree.ElementTree`` refuses *external* entities but still expands
*internal* ones, so a DOCX whose ``word/document.xml`` declares a DTD can drive
quadratic-blowup / billion-laughs expansion inside the ingest worker. Verified
on CPython 3.12.13: a ten-fold nested internal entity expands, while
``SYSTEM "file:///etc/passwd"`` raises ``ParseError: undefined entity``.

A DTD has no legitimate role in the OOXML parts this pipeline reads, so the
document is rejected outright rather than sanitised.
"""
from __future__ import annotations


class UnsafeXMLError(ValueError):
    """Raised when client XML declares a DTD and is refused."""


def reject_dtd(xml: bytes) -> None:
    """Reject *xml* if it declares a document type definition.

    The whole buffer is scanned rather than just the prolog: a DOCTYPE is only
    *valid* before the root element, but scanning everything costs one pass and
    removes any question of a padded prolog slipping past. The cost is that a
    document containing the literal text ``<!DOCTYPE`` in its body is refused
    too — acceptable for OOXML parts, which never legitimately contain it.

    :param xml: Raw XML bytes taken from the uploaded archive.
    :type xml: bytes
    :returns: ``None`` when the document declares no DTD.
    :rtype: None
    :raises UnsafeXMLError: If a ``<!DOCTYPE`` declaration is present.
    """
    if b"<!DOCTYPE" in xml:
        raise UnsafeXMLError(
            "client XML declares a DTD; refusing to parse (entity-expansion risk)"
        )
