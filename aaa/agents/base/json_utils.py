"""Lenient JSON parsing for LLM responses."""
from __future__ import annotations

import json
import re
from typing import Any

#: Sentinel: a decoded value may itself be falsy ({}, [], 0).
_NOTHING = object()

_FENCE_RE = re.compile(r"^```[a-zA-Z0-9_-]*\s*\n(.*?)\n```$", re.DOTALL)


def _loads_lenient(content: str) -> dict[str, Any]:
    """Parse a JSON object from *content*, tolerating fences / extra data.

    LLM backends sometimes wrap JSON in markdown code fences or append
    trailing prose or a second JSON object (which makes ``json.loads`` raise
    ``Extra data: ...``). This helper:

    1. tries a strict parse first (fast path for well-behaved responses),
    2. strips a surrounding ```` ```json ... ``` ```` fence if present,
    3. falls back to decoding the first balanced JSON value found in the
       string via ``raw_decode``, ignoring any trailing data.

    :param content: Raw LLM reply text.
    :returns: The parsed object (``{}`` for empty input).
    :raises json.JSONDecodeError: When no JSON value can be recovered at all.
    """
    text = (content or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fence = _FENCE_RE.match(text)
    if fence:
        text = fence.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    decoder = json.JSONDecoder()
    widest = -1
    best: Any = _NOTHING
    for start, char in enumerate(text):
        if char not in "{[":
            continue
        try:
            value, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            continue
        # Widest match, not first: a reply whose outer object is malformed
        # otherwise yields an inner one. A GLM-5.3-Flash critique on 2026-09-10
        # decoded to its own `scores` sub-object — five plausible integers and
        # no `verdict`.
        if end - start > widest:
            widest, best = end - start, value
    if best is _NOTHING:
        raise json.JSONDecodeError("No JSON value could be decoded", text, 0)
    # ``best`` may legitimately be a falsy value ({}, [], 0), so "did anything
    # decode?" is asked with a sentinel rather than by truthiness.
    #
    # Whether the widest match is the answer or a fragment of a broken one is
    # not decidable here: both arrive as "an object after an object that would
    # not parse", and only the caller knows which keys make a reply an answer.
    # Refusing on position alone cost a real recovery — a re-emitted critique
    # that decoded cleanly further down the same reply. So the parser returns
    # its best reading and the caller validates; see the Verifier, which treats
    # a critique carrying no verdict as a failure rather than as a verdict.
    return best
