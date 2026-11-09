"""Compile ``data/dlls/convars.tsv``, the ``convars`` facet's aggregate.

    python -m deadlock.dlls_convars data/dlls/convars/<dll>.json ... > data/dlls/convars.tsv

One row per convar declaration, duplicates kept: ``module`` (the document's
own), ``name``, ``type`` (the binary's ``EConVarType`` name), ``version``,
``default``, ``min``, ``max``, ``flags`` (space-separated names), ``help``.
Cells as ``deadlock.dlls_tsv``; rows sorted and ordered as
``deadlock.dlls_concommands`` (a row's ordinal among its module's rows is its
queue index).

A value cell is read by its row's ``type`` (``TYPES``): ``\\N`` is an absent
value (``null``); ``true``/``false``; an integer or float as Python spells it
(``repr``, so a float reads back to the identical float: ``0.02``, ``1.0``);
a string escaped as any other cell (``""`` is an empty cell); a ``color`` or
vector as its numbers, space-separated (``255 0 16 255``).
"""

import sys
from collections.abc import Callable, Mapping
from typing import Literal, TypeGuard

from dllscan.document import ConVar, ConVarsDocument, ConVarValue

from . import dlls_tsv
from .sparse import Table, render
from .types import is_sequence, is_str_mapping

type _Kind = Literal["bool", "int", "float", "str", "ints", "floats"]

TYPES: Mapping[str, _Kind] = {
    "bool": "bool",
    **dict.fromkeys(["int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"], "int"),
    "float32": "float",
    "float64": "float",
    "string": "str",
    "color": "ints",
    **dict.fromkeys(["vector2", "vector3", "vector4", "qangle", "vectorws"], "floats"),
}
"""Each ``EConVarType`` name, in code order (``registration-flow.md``), → the
JSON kind of its values."""

_HEADER = ["module", "name", "type", "version", "default", "min", "max", "flags", "help"]
_KEYS = {"name", "help", "flags", "type", "version", "default", "min", "max"}


def _is_int(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_float(value: object) -> TypeGuard[float]:
    return isinstance(value, float)


_FITS: Mapping[_Kind, Callable[[object], bool]] = {
    "bool": lambda value: isinstance(value, bool),
    "int": _is_int,
    "float": _is_float,
    "str": lambda value: isinstance(value, str),
    "ints": lambda value: is_sequence(value) and all(map(_is_int, value)),
    "floats": lambda value: is_sequence(value) and all(map(_is_float, value)),
}
_PARSE: Mapping[_Kind, Callable[[str], ConVarValue | None]] = {
    "bool": {"true": True, "false": False}.__getitem__,
    "int": int,
    "float": float,
    "str": dlls_tsv.uncell,
    "ints": lambda text: [int(item) for item in dlls_tsv.unlist_cell(text)],
    "floats": lambda text: [float(item) for item in dlls_tsv.unlist_cell(text)],
}


def _number(value: object) -> str:
    return ("true" if value else "false") if isinstance(value, bool) else repr(value)


def value_cell(type: str, value: ConVarValue | None) -> str:
    """``value``'s cell; asserts it is of ``type``'s kind (``KeyError`` on an
    unknown type)."""
    kind = TYPES[type]
    if value is None:
        return dlls_tsv.NULL
    assert _FITS[kind](value), (type, value)
    if isinstance(value, str):
        return dlls_tsv.cell(value)
    if is_sequence(value):
        return dlls_tsv.list_cell([_number(item) for item in value])
    return _number(value)


def uncell_value(type: str, text: str) -> ConVarValue | None:
    """The value ``value_cell(type, ...)`` rendered as ``text``."""
    if text == dlls_tsv.NULL:
        return None
    return _PARSE[TYPES[type]](text)


def _is_convar(value: object) -> TypeGuard[ConVar]:
    return (
        is_str_mapping(value)
        and set(value) == _KEYS
        and isinstance(value["name"], str)
        and (value["help"] is None or isinstance(value["help"], str))
        and dlls_tsv.is_str_sequence(value["flags"])
        and isinstance(type := value["type"], str)
        and type in TYPES
        and _is_int(value["version"])
        and all(v is None or _FITS[TYPES[type]](v) for v in (value["default"], value["min"], value["max"]))
    )


def is_convars_document(value: object) -> TypeGuard[ConVarsDocument]:
    return (
        is_str_mapping(value)
        and set(value) == {"module", "convars"}
        and isinstance(value["module"], str)
        and is_sequence(convars := value["convars"])
        and all(map(_is_convar, convars))
    )


def _row(module: str, c: ConVar) -> list[str]:
    values = [value_cell(c["type"], c[key]) for key in ("default", "min", "max")]
    return [
        module,
        dlls_tsv.cell(c["name"]),
        c["type"],
        str(c["version"]),
        *values,
        dlls_tsv.list_cell(c["flags"]),
        dlls_tsv.cell(c["help"]),
    ]


def table(documents: Mapping[str, ConVarsDocument]) -> Table:
    """``documents`` keyed by the basename in ``data/dlls.list``, which is each
    one's ``module``."""
    for dll, d in documents.items():
        assert d["module"] == dll, (dll, d["module"])
    rows = [
        _row(d["module"], c) for d in sorted(documents.values(), key=lambda d: d["module"]) for c in d["convars"]
    ]
    return _HEADER, rows


def main() -> None:
    _ = sys.stdout.write(render(table(dlls_tsv.load_documents(sys.argv[1:], is_convars_document))))


if __name__ == "__main__":
    main()
