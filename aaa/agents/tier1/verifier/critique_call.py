"""One critique call to the model, and the reply parsed into a verdict."""
from __future__ import annotations

import logging
from typing import Any

from aaa.agents.base.json_utils import _loads_lenient

logger = logging.getLogger(__name__)


async def _critique_once(agent: Any, messages: list, phase_id: str,
                         template_id: str) -> dict[str, Any]:
    """Ask for the critique, and ask again if the reply cannot be read.
    A provider can truncate a completion mid-JSON — on 2026-09-11 a T03 critique
    came back at 81 completion tokens, cut off inside ``"issues":[{"``. Lenient
    parsing cannot rescue that: the object never closes. It became ``unverified``
    on the first attempt, and Art. 6 and Annex III lost their verdicts, which is
    precisely the loss the lenient parser was introduced to stop after the
    2026-09-10 GLM run.
    Truncation is transient, so it is retried once before the deterministic
    fallback — which is not a judgement and should be the last resort, not the
    response to one short reply.
    :param agent: The Verifier.
    :param messages: The critique prompt.
    :param phase_id: Phase being verified.
    :param template_id: Artefact being verified.
    :returns: The parsed critique.
    :raises ValueError: When both attempts are unreadable.
    """
    last: Exception | None = None
    for attempt in (1, 2):
        resp = await agent.acompletion(
            messages=messages, response_format={"type": "json_object"})
        reply = resp.choices[0].message.content or ""
        try:
            raw = _loads_lenient(reply)
            if not str(raw.get("verdict") or "").strip():
                raise ValueError("critique carries no verdict")
            return raw
        except Exception as exc:  # noqa: BLE001 — retried, then surfaced
            last = exc
            logger.warning(
                "Critique for %s/%s unreadable on attempt %d (%s; %d chars). %s",
                phase_id, template_id, attempt, exc, len(reply),
                "Re-asking once." if attempt == 1 else "Falling back.")
    raise ValueError(f"critique unreadable after 2 attempts: {last}")
__all__ = ["_critique_once"]
