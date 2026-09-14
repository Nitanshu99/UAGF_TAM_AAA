"""``python -m scripts.ingest_regulatory_corpus`` entry point."""
from __future__ import annotations

import sys

from scripts.ingest_regulatory_corpus.main import main

if __name__ == "__main__":
    sys.exit(main())
