"""Every literal key read from a dossier names a property of that dossier's contract.

Builders read Stage A, Stage B, T01a and T01b by string literal. Nothing checked
the literal against ``templates/``, so 28 reads of 27 keys no contract defines
shipped silently: ``training_dataset_size`` made T06 report ``num_instances: 0``
for every engagement, and ``annex_i_section_a_acts`` kept every declared Annex I
Section A product away from Art. 43 §3 (T-20260913-009, -016, -017).

The check is by variable name, which is how the codebase names these payloads.
A new name for a dossier belongs in ``_CONTRACTS``.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

_STAGE_A = "templates/T01a_stage_a_triage.json"
_STAGE_B = "templates/T01b_annex_iv_dossier.json"
_CONTRACTS = {"t01a": _STAGE_A, "stage_a": _STAGE_A, "stage_a_payload": _STAGE_A,
              "t01b": _STAGE_B, "stage_b": _STAGE_B}


def _keys(path: str) -> set[str]:
    """Top-level properties plus one level of nested object properties."""
    props = json.loads(Path(path).read_text(encoding="utf-8"))["properties"]
    keys = set(props)
    for node in props.values():
        keys |= set((node.get("properties") or {}) if isinstance(node, dict) else {})
    return keys


def _dead_reads() -> list[str]:
    """``file:line name.get("key")`` for every read of a key its contract lacks."""
    known = {name: _keys(path) for name, path in _CONTRACTS.items()}
    dead = []
    for module in sorted(Path("aaa").rglob("*.py")):
        for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "get" and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in known and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)):
                continue
            if node.args[0].value not in known[node.func.value.id]:
                dead.append(f"{module}:{node.lineno} {node.func.value.id}.get"
                            f"({node.args[0].value!r})")
    return dead


def test_no_dossier_read_names_a_key_its_contract_does_not_define() -> None:
    """A read that can only ever return its default is a defect, not a fallback."""
    dead = _dead_reads()
    assert not dead, "\n".join(dead)


def test_the_guard_can_see_a_dead_read(tmp_path: Path, monkeypatch) -> None:
    """The scan itself works: a planted dead read is reported."""
    (tmp_path / "aaa").mkdir()
    (tmp_path / "aaa" / "m.py").write_text('def f(t01b):\n    return t01b.get("no_such_key")\n',
                                           encoding="utf-8")
    for contract in (_STAGE_A, _STAGE_B):
        (tmp_path / contract).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / contract).write_text(Path(contract).read_text(encoding="utf-8"),
                                         encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert _dead_reads() == ["aaa/m.py:2 t01b.get('no_such_key')"]
