"""A loaded PE32+/AMD64 image's layout, read through `Memory` from the base
address `LoadLibraryExW` returned: the image's address range and each section's.

Only what the loaded image needs (no imports, exports or the like: those are the
WSL-side `pe` facet). Headers that don't fit raise `ShapeError`; there is no
partial layout.

>>> from .image_fake import FakeSection, loaded
>>> image = read_image(Memory(loaded(0x10000, [FakeSection(".data", 0x1000, WRITE, bytes(8))])), 0x10000)
>>> image.span, [s.name for s in image.writable]
(range(65536, 73728), ['.data'])
"""

import struct
from dataclasses import dataclass

from .memory import Memory
from .shape import ShapeError

WRITE = 0x80000000
"""`IMAGE_SCN_MEM_WRITE`: the section is writable once loaded."""

_MZ = 0x5A4D
_PE = 0x00004550
_AMD64 = 0x8664
_PE32_PLUS = 0x20B
_OPT_FIXED = 112
"""PE32+ optional header up to its data directories; `SizeOfImage` is at +56."""
_SECTION = struct.Struct("<8sIII16xI")
"""`IMAGE_SECTION_HEADER`: Name, VirtualSize, VirtualAddress, SizeOfRawData, Characteristics."""


@dataclass(frozen=True)
class Section:
    """One section as loaded: `span` is absolute addresses."""

    name: str
    span: range
    characteristics: int

    @property
    def writable(self) -> bool:
        return bool(self.characteristics & WRITE)


@dataclass(frozen=True)
class Image:
    """`span` is `[base, base + SizeOfImage)`; `sections` in table order."""

    span: range
    sections: tuple[Section, ...]

    @property
    def writable(self) -> tuple[Section, ...]:
        return tuple(s for s in self.sections if s.writable)


def read_image(mem: Memory, base: int) -> Image:
    """The layout of the image loaded at `base`, or `ShapeError`."""
    _expect("DOS signature", base, mem.u16(base), _MZ)
    nt = base + _readable("e_lfanew", base + 0x3C, mem.u32(base + 0x3C))
    _expect("PE signature", nt, mem.u32(nt), _PE)
    _expect("Machine", nt + 4, mem.u16(nt + 4), _AMD64)
    count = _readable("NumberOfSections", nt + 6, mem.u16(nt + 6))
    opt_size = _readable("SizeOfOptionalHeader", nt + 0x14, mem.u16(nt + 0x14))
    opt = nt + 0x18
    _expect("optional header Magic", opt, mem.u16(opt), _PE32_PLUS)
    if opt_size < _OPT_FIXED:
        raise ShapeError("SizeOfOptionalHeader", hex(nt + 0x14), opt_size)
    span = range(base, base + _readable("SizeOfImage", opt + 56, mem.u32(opt + 56)))
    table = mem.read(opt + opt_size, _SECTION.size * count)
    if table is None:
        raise ShapeError("section table unreadable", hex(opt + opt_size), count)
    return Image(span, tuple(_section(span, table[i : i + _SECTION.size]) for i in range(0, len(table), _SECTION.size)))


def _section(image: range, header: bytes) -> Section:
    fields: tuple[bytes, int, int, int, int] = _SECTION.unpack(header)
    raw_name, vsize, rva, raw_size, characteristics = fields
    name = raw_name.rstrip(b"\0").decode("latin-1")
    if not (name.isascii() and name.isprintable()):
        raise ShapeError("section name", raw_name)
    span = range(image.start + rva, image.start + rva + (vsize or raw_size))
    if span.stop > image.stop:
        raise ShapeError("section outside image", name, span, image)
    return Section(name, span, characteristics)


def _readable(what: str, addr: int, value: int | None) -> int:
    if value is None:
        raise ShapeError(f"{what} unreadable", hex(addr))
    return value


def _expect(what: str, addr: int, value: int | None, want: int) -> None:
    if _readable(what, addr, value) != want:
        raise ShapeError(what, hex(addr), value, want)
