"""Deterministic module-path rewriter for the module/sub-module/file restructure.

Given an old→new dotted-module mapping (JSON), rewrites every occurrence in
``.py`` files under the given roots. Longest paths are applied first so a
mapping for ``pkg.audit_state`` never clobbers ``pkg.audit_state_parts``;
word boundaries keep ``step3`` from matching ``step3_model_meta``.

Usage: ``python scripts/restructure_imports.py mapping.json aaa tests scripts``
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def rewrite_imports(text: str, mapping: dict[str, str]) -> str:
    """Rewrite every dotted-module occurrence of *mapping* keys in *text*.

    :param text: File contents.
    :type text: str
    :param mapping: Old dotted path → new dotted path.
    :type mapping: dict[str, str]
    :returns: The rewritten contents.
    :rtype: str
    """
    for old in sorted(mapping, key=len, reverse=True):
        # Trailing [\w.] excluded: flat modules have no dotted submodules, and
        # this keeps already-rewritten longer paths safe from shorter keys.
        pattern = rf"(?<![\w.]){re.escape(old)}(?![\w.])"
        text = re.sub(pattern, mapping[old], text)
    return text


def main(argv: list[str]) -> int:
    """Apply the mapping file to every ``.py`` file under the given roots.

    :param argv: ``[mapping.json, root, ...]``.
    :type argv: list[str]
    :returns: Process exit code.
    :rtype: int
    """
    if len(argv) < 2:
        print("usage: restructure_imports.py <mapping.json> <root> [...]", file=sys.stderr)
        return 2
    mapping: dict[str, str] = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    changed = 0
    for root in argv[1:]:
        for path in Path(root).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            before = path.read_text(encoding="utf-8")
            after = rewrite_imports(before, mapping)
            if after != before:
                path.write_text(after, encoding="utf-8")
                changed += 1
                print(f"rewrote {path}")
    print(f"{changed} file(s) rewritten")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
