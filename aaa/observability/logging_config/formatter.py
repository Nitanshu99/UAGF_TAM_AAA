"""One JSON shape for every log record, structlog-native or stdlib.

``configure_logging`` used to hand stdlib records a bare ``%(message)s``
formatter, so ``logging.getLogger(...)`` callers — most of ``aaa.agents`` —
wrote plain text next to structlog's JSON: agents.log held 55,400 text lines
and not one JSON object, and Alloy's ``level`` extraction had nothing to read.
``ProcessorFormatter`` runs stdlib records through the same processor chain,
so every line in every file is one JSON object carrying ``event``, ``level``,
``logger`` and ``timestamp``.
"""
from __future__ import annotations

import logging

import structlog


def shared_processors() -> list:
    """Return the processors applied to structlog events and, as the
    pre-chain, to stdlib records.

    :returns: Processor callables, in order.
    :rtype: list
    """
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]


def json_formatter() -> logging.Formatter:
    """Return a formatter rendering any record as one JSON object per line.

    :returns: A ``ProcessorFormatter`` ending in ``JSONRenderer``.
    :rtype: logging.Formatter
    """
    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors(),
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
