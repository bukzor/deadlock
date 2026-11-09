"""Decode a reg-list queue entry (an address from `reglist.Queue.entries`) into
its document: a `ConCommand` or a `ConVar`.

Both entry kinds lead with their creation struct (`Entry_t{m_Info, ...}`,
`docs/dev/convar-dump.kb/registration-flow.md` step 2), and both creation
structs lead with `CVarCreationBase_t` (s2sdk `deadlock` 18139bdc96f1,
`public/tier0/convar.h:157-167`):

    +0   const char* m_pszName
    +8   const char* m_pszHelpString   (may be null)
    +16  uint64      m_nFlags

The name and help offsets are the ones `docs/dev/probes/convar_scan.py` walks
by; flags at +16 decode to upstream's for every anchor checked on 6848
(`capture-approach.kb/queue-shape-scan.md`). A command entry holds nothing past
the base worth dumping (its callback is a pointer). A convar entry continues
with `ConVarValueInfo_t`, values packed (`registration-flow.md`, "The convar
entry's layout", fitted against tier0's registry on 6860):

    +24  int32       m_Version
    +28  uint8[3]    has-default, has-min, has-max
    +31  CVValue_t   default, then min at +47, max at +63 (16 bytes each)
    +120 int16       m_eVarType

The rest of the 160 bytes is pointers and padding: nothing to dump.

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

import struct
from collections.abc import Sequence
from typing import TypedDict

from . import flags, values
from .document import ConCommand, ConVar, ConVarValue
from .image import Image
from .memory import Memory
from .reglist import STRIDES, name_at
from .shape import ShapeError

_BASE = struct.Struct("<QQQ")
"""`CVarCreationBase_t`: name pointer, help pointer, flags."""

_VERSION = struct.Struct("<i3B")
"""`m_Version`, then the has-default, has-min, has-max bytes, at +24."""
_VALUES = (31, 47, 63)
"""The default, min and max `CVValue_t` offsets."""
_TYPE = 120
"""`m_eVarType`'s offset, an int16."""


class CreationBase(TypedDict):
    """The `CVarCreationBase_t` both entry kinds lead with: a `ConCommand`
    whole, and the first keys of a `ConVar`."""

    name: str
    help: str | None
    flags: Sequence[str]


def decode_creation_base(mem: Memory, addr: int, image: Image) -> CreationBase:
    """Name, help and flag names of the entry at `addr`, or `ShapeError`."""
    raw = mem.read(addr, _BASE.size)
    if raw is None:
        raise ShapeError("entry unreadable", hex(addr))
    fields: tuple[int, int, int] = _BASE.unpack(raw)
    name_p, help_p, flag_word = fields
    name = name_at(mem, name_p, image)
    if name is None:
        raise ShapeError("entry name", hex(addr), hex(name_p))
    help = mem.cstr_in(help_p, image.span.start, image.span.stop) if help_p else None
    if help_p and help is None:
        raise ShapeError("entry help", hex(addr), hex(help_p))
    return CreationBase(name=name, help=help, flags=flags.names(flag_word))


def decode_concommand(mem: Memory, addr: int, image: Image) -> ConCommand:
    """The command entry at `addr` (64 bytes; only its creation base is data)."""
    return decode_creation_base(mem, addr, image)


def decode_convar(mem: Memory, addr: int, image: Image) -> ConVar:
    """The convar entry at `addr` (`reglist.STRIDES["convars"]` bytes)."""
    base = decode_creation_base(mem, addr, image)
    raw = mem.read(addr, STRIDES["convars"])
    if raw is None:
        raise ShapeError("entry unreadable", hex(addr))
    try:
        return ConVar(**base, **_value_info(mem, raw))
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


def _value_info(mem: Memory, raw: bytes) -> _ValueInfo:
    fields: tuple[int, int, int, int] = _VERSION.unpack_from(raw, 24)
    version, *has = fields
    type = values.type_name(int.from_bytes(raw[_TYPE : _TYPE + 2], "little", signed=True))
    default, min, max = (values.decode(mem, type, h, raw[at : at + values.SIZE]) for h, at in zip(has, _VALUES, strict=True))
    return _ValueInfo(type=type, version=version, default=default, min=min, max=max)
