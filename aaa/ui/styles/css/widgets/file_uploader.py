"""File uploader — part of the widgets cascade layer."""
from __future__ import annotations

FILE_UPLOADER = """
/* ---- file uploader ---------------------------------------------------- */
.stApp [data-testid="stFileUploaderDropzone"] {
  background: var(--brand-soft);
  border: 1.5px dashed var(--brand-line);
  border-radius: var(--r-lg);
  transition: background var(--dur-1) var(--ease), border-color var(--dur-1) var(--ease);
}
.stApp [data-testid="stFileUploaderDropzone"]:hover { border-color: var(--brand); background: var(--surface-2); }
.stApp [data-testid="stFileUploaderDropzoneInstructions"] svg { color: var(--brand); }
.stApp [data-testid="stFileUploaderFile"] {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  padding: 0.5rem 0.6rem;
}
"""

__all__ = ["FILE_UPLOADER"]
