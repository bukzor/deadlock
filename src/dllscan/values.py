"""The binary's `EConVarType` table, and a `CVValue_t` decoded by it into a JSON
value (`docs/dev/cvar-dump.kb/registration-flow.md`, "The convar entry's
layout", fitted on 6860).

A `CVValue_t` is `SIZE` bytes; a type uses the first `TYPES[type]` of them. Every
type decodes, so bytes that don't fit their type raise `ShapeError(what, ...)`:
the queue already fit, so a misfit is a bug or a layout change. The caller adds
the entry address.

>>> decode(Memory(lambda addr, n: None), "color", 1, bytes([255, 128, 0, 7]).ljust(16, b"\\0"))
[255, 128, 0, 7]
"""

import ctypes
import math
import struct
from collections.abc import Mapping

from .convar_h import CVValue_t
from .document import ConVarValue
from .memory import Memory
from .shape import ShapeError

SIZE = ctypes.sizeof(CVValue_t)

TYPES: Mapping[str, int] = {
    "bool": 1,
    "int8": 1,
    "uint8": 1,
    "int16": 2,
    "uint16": 2,
    "int32": 4,
    "uint32": 4,
    "int64": 8,
    "uint64": 8,
    "float32": 4,
    "float64": 8,
    "string": 8,
    "color": 4,
    "vector2": 8,
    "vector3": 12,
    "vector4": 16,
    "qangle": 12,
    "vectorws": 12,
}
"""Type name → byte size, in code order: the rows of tier0's type-traits table
(`.data`, RVA `0x398610` on 6860). s2sdk's enum is stale: it lacks int8, uint8."""

_INTS = frozenset(("int8", "int16", "int32", "int64"))
_UINTS = frozenset(("uint8", "uint16", "uint32", "uint64"))
_FLOAT32S: Mapping[str, int] = {"vector2": 2, "vector3": 3, "vector4": 4, "qangle": 3, "vectorws": 3}


def type_name(code: int) -> str:
    """The `EConVarType` named by `code`."""
    if not 0 <= code < len(TYPES):
        raise ShapeError("convar type", code)
    return list(TYPES)[code]


def decode(mem: Memory, type: str, has: int, raw: bytes) -> ConVarValue | None:
    """The `CVValue_t` `raw` of a `type` convar, or None if its has-byte `has`
    is 0. A `string` dereferences its `CUtlString` through `mem`."""
    assert len(raw) == SIZE, raw
    if has not in (0, 1):
        raise ShapeError("convar has-byte", has)
    if not has:
        if any(raw):
            raise ShapeError("convar absent value", raw.hex())
        return None
    size = TYPES[type]
    if any(raw[size:]):
        raise ShapeError("convar value tail", type, raw.hex())
    return _present(mem, type, raw[:size])


def _present(mem: Memory, type: str, raw: bytes) -> ConVarValue:
    if type == "bool":
        if raw[0] not in (0, 1):
            raise ShapeError("convar bool", raw.ljust(SIZE, b"\0").hex())
        return bool(raw[0])
    if type in _INTS | _UINTS:
        return int.from_bytes(raw, "little", signed=type in _INTS)
    if type == "float32":
        return _float32(type, raw)
    if type == "float64":
        return _finite(type, raw, struct.unpack("<d", raw)[0])
    if type == "string":
        return _string(mem, int.from_bytes(raw, "little"))
    if type == "color":
        return list(raw)
    if type in _FLOAT32S:
        return [_float32(type, raw[i : i + 4]) for i in range(0, len(raw), 4)]
    raise AssertionError(type)


def _string(mem: Memory, pointer: int) -> str:
    """A `CUtlString`'s text; null reads as `""`, as `CUtlString::Get` returns."""
    if not pointer:
        return ""
    text = mem.cstr_in(pointer, 0, 1 << 64)
    if text is None:
        raise ShapeError("convar string", hex(pointer))
    return text


def _float32(type: str, raw: bytes) -> float:
    """The shortest decimal that reads back as the same float32 (`0.02`, not
    `0.019999999552965164`): what the engine was given, as a JSON number."""
    value = _finite(type, raw, struct.unpack("<f", raw)[0])
    for digits in range(1, 10):
        short = float(f"{value:.{digits}g}")
        if _pack_float32(short) == raw:
            return short
    raise AssertionError(raw.hex())


def _pack_float32(value: float) -> bytes | None:
    """`value` as a float32, or None if it rounds past float32's range."""
    try:
        return struct.pack("<f", value)
    except OverflowError:
        return None


def _finite(type: str, raw: bytes, value: float) -> float:
    """`value`, unless JSON can't hold it (NaN, ±inf); none occurs on 6860."""
    if not math.isfinite(value):
        raise ShapeError("convar float", type, raw.hex())
    return value
