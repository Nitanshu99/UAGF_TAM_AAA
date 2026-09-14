"""Construction of individual conditional-field status entries.

``present`` carries a deliberately wide meaning: *the dossier is correct on
this point*. For a required field that means the value is there; for a
forbidden one it means the value is correctly absent. Encoding both this way
lets a single ``applicable and not present`` reading flag either kind of
defect, without widening :class:`ConditionalFieldStatus`.
"""
from __future__ import annotations

from typing import Any

from aaa.tools.annex_iv_validator.schema_path import ConditionalFieldStatus


def filled(value: Any) -> bool:
    """True when *value* is a meaningful, non-empty declaration.

    :param value: Any dossier value.
    :type value: Any
    :returns: Whether the field carries content.
    :rtype: bool
    """
    return value is not None and value != "" and value != []


def make_status(field: str, condition: str, applicable: bool,
                value: Any) -> ConditionalFieldStatus:
    """Build a status entry for a field that must be *present*.

    :param field: Dossier field name.
    :param condition: Human-readable applicability condition.
    :param applicable: Whether the condition holds for this dossier.
    :param value: Current field value.
    :returns: The populated status entry.
    :rtype: ConditionalFieldStatus
    """
    return ConditionalFieldStatus(field=field, condition=condition,
                                  applicable=applicable, present=filled(value))


def make_absence_status(field: str, condition: str, applicable: bool,
                        value: Any) -> ConditionalFieldStatus:
    """Build a status entry for a field that must be *absent*.

    :param field: Dossier field name.
    :param condition: Human-readable applicability condition.
    :param applicable: Whether the prohibition applies to this dossier.
    :param value: Current field value.
    :returns: Status whose ``present`` means "correctly absent".
    :rtype: ConditionalFieldStatus
    """
    return ConditionalFieldStatus(field=field, condition=condition,
                                  applicable=applicable, present=not filled(value))
