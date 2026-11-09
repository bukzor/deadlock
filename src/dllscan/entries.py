"""Decode a reg-list queue entry (an address from `reglist.Queue.entries`) into
its document: a `ConCommand` or a `ConVar`.

Both entry kinds lead with their creation struct, and both creation structs
lead with `CVarCreationBase_t`: name, help (may be null), flags. A command entry
holds nothing past the base worth dumping (its callback is a pointer); a convar
entry continues with its `ConVarValueInfo_t`. The layout is `convar_h`'s.

What doesn't fit (`docs/dev/convar-dump.kb/validation.md`, "Shape") raises
`ShapeError(what, hex(entry), ...)`: the entry comes from a queue that already
fit, so a misfit is a bug or a layout change. The trailing-ref check needs the
queue's stride and is `reglist.walk`'s. No address goes into the output.

>>> from .image import read_image
>>> from .image_fake import FakeSection, loaded
>>> segments = loaded(0x10000, [FakeSection(".rdata", 0x1000, 0x40000040, b"find\\0")])
>>> segments[0x900000] = (0x11000).to_bytes(8, "little") + bytes(8) + (1 << 14).to_bytes(8, "little")
>>> mem = Memory(segments)
>>> decode_concommand(mem, 0x900000, read_image(mem, 0x10000))
{'name': 'find', 'help': None, 'flags': ('cheat',)}
"""

from collections.abc import Sequence
from ctypes import sizeof
from typing import TypedDict

from . import flags, values
from .convar_h import ConVarRegList_Entry_t, ConVarValueInfo_t, CVarCreationBase_t
from .document import ConCommand, ConVar, ConVarValue
from .image import Image
from .memory import Memory
from .reglist import name_at
from .shape import ShapeError


class CreationBase(TypedDict):
    """The `CVarCreationBase_t` both entry kinds lead with: a `ConCommand`
    whole, and the first keys of a `ConVar`."""

    name: str
    help: str | None
    flags: Sequence[str]


def decode_creation_base(mem: Memory, addr: int, image: Image) -> CreationBase:
    """Name, help and flag names of the entry at `addr`, or `ShapeError`."""
    return _creation_base(mem, addr, _read(mem, addr, sizeof(CVarCreationBase_t)), image)


def decode_concommand(mem: Memory, addr: int, image: Image) -> ConCommand:
    """The command entry at `addr`: only its creation base is data."""
    return decode_creation_base(mem, addr, image)


def decode_convar(mem: Memory, addr: int, image: Image) -> ConVar:
    """The convar entry at `addr`."""
    raw = _read(mem, addr, sizeof(ConVarRegList_Entry_t))
    base = _creation_base(mem, addr, raw, image)
    try:
        return ConVar(**base, **_value_info(mem, ConVarRegList_Entry_t.from_buffer_copy(raw).m_Info.m_valueInfo))
    except ShapeError as error:
        args: tuple[object, ...] = error.args
        what, *detail = args
        raise ShapeError(what, hex(addr), *detail) from None


class _ValueInfo(TypedDict):
    type: str
    version: int
    default: ConVarValue | None
    min: ConVarValue | None
    max: ConVarValue | None


def _read(mem: Memory, addr: int, size: int) -> bytes:
    raw = mem.read(addr, size)
    if raw is None:
        raise ShapeError("entry unreadable", hex(addr))
    return raw


def _creation_base(mem: Memory, addr: int, raw: bytes, image: Image) -> CreationBase:
    """The creation base leading the entry bytes `raw`, read from `addr`."""
    base = CVarCreationBase_t.from_buffer_copy(raw)
    name = name_at(mem, base.m_pszName, image)
    if name is None:
        raise ShapeError("entry name", hex(addr), hex(base.m_pszName))
    help_p = base.m_pszHelpString
    help = mem.cstr_in(help_p, image.span.start, image.span.stop) if help_p else None
    if help_p and help is None:
        raise ShapeError("entry help", hex(addr), hex(help_p))
    return CreationBase(name=name, help=help, flags=flags.names(base.m_nFlags))


def _value_info(mem: Memory, info: ConVarValueInfo_t) -> _ValueInfo:
    type = values.type_name(info.m_eVarType)
    default, min, max = (
        values.decode(mem, type, has, bytes(value))
        for has, value in (
            (info.m_bHasDefault, info.m_defaultValue),
            (info.m_bHasMin, info.m_minValue),
            (info.m_bHasMax, info.m_maxValue),
        )
    )
    return _ValueInfo(type=type, version=info.m_Version, default=default, min=min, max=max)
