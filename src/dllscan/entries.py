"""Decode a reg-list queue entry (an address from `reglist.Queue.entries`) into
the parts of its document known so far: name, help, flags.

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
the base worth dumping (its callback is a pointer), so `decode_concommand` is
complete. A convar entry's value fields (`ConVarValueInfo_t`: type, default,
min, max) are not located yet; `decode_convar` will be
`ConVar(**decode_creation_base(...), type=..., default=..., min=..., max=...)`
and add the type and has-value shape checks.

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

from . import flags
from .document import ConCommand
from .image import Image
from .memory import Memory
from .reglist import name_at
from .shape import ShapeError

_BASE = struct.Struct("<QQQ")
"""`CVarCreationBase_t`: name pointer, help pointer, flags."""


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
