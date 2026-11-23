"""A synthetic loaded PE32+/AMD64 image, for tests of `image` and its consumers.

Headers are laid out at fixed offsets (below) so a test can corrupt one field.
Each section loads as its own segment at `base + rva`, its data zero-padded to
the loaded size, so a consumer's test can plant bytes in `.data`; add segments
(heap blocks) to the returned `Segments` as needed.

>>> from .image import WRITE, read_image
>>> from .memory import Memory
>>> fake = loaded(0x10000, [FakeSection(".data", 0x1000, WRITE, b"head")])
>>> read_image(Memory(fake), 0x10000).writable[0].span
range(69632, 69636)
>>> fake(0x11000, 4)
b'head'
"""

import struct
from collections.abc import Sequence
from dataclasses import dataclass

from .memory import Segments

NT = 0x40
"""`e_lfanew`: offset of the `PE\\0\\0` signature."""
OPT = NT + 0x18
"""Offset of the optional header (its `Magic`; `SizeOfImage` at +56)."""
OPT_SIZE = 0xF0
"""`SizeOfOptionalHeader`: PE32+ with all 16 data directories."""
TABLE = OPT + OPT_SIZE
"""Offset of the section table, 40 bytes per section."""
ALIGN = 0x1000


@dataclass(frozen=True)
class FakeSection:
    """One section. `virtual_size` and `raw_size` default to `len(data)`."""

    name: str
    rva: int
    characteristics: int
    data: bytes = b""
    virtual_size: int | None = None
    raw_size: int | None = None

    @property
    def sizes(self) -> tuple[int, int]:
        """(`VirtualSize`, `SizeOfRawData`) as the header records them."""
        vsize, raw = self.virtual_size, self.raw_size
        return (len(self.data) if vsize is None else vsize, len(self.data) if raw is None else raw)

    @property
    def loaded_size(self) -> int:
        vsize, raw = self.sizes
        return vsize or raw


def headers(sections: Sequence[FakeSection], size_of_image: int) -> bytearray:
    """DOS, NT and section headers for these sections, mutable for corrupting."""
    out = bytearray(TABLE + 40 * len(sections))
    out[0:2] = b"MZ"
    struct.pack_into("<I", out, 0x3C, NT)
    struct.pack_into("<4sHH12xH", out, NT, b"PE\0\0", 0x8664, len(sections), OPT_SIZE)
    struct.pack_into("<H", out, OPT, 0x20B)
    struct.pack_into("<I", out, OPT + 56, size_of_image)
    for i, s in enumerate(sections):
        vsize, raw = s.sizes
        struct.pack_into("<8sIII16xI", out, TABLE + 40 * i, s.name.encode(), vsize, s.rva, raw, s.characteristics)
    return out


def loaded(base: int, sections: Sequence[FakeSection], size_of_image: int | None = None) -> Segments:
    """The image as loaded at `base`: headers, then each section's data.
    `size_of_image` defaults to the last section's end, page-aligned."""
    if size_of_image is None:
        end = max([TABLE + 40 * len(sections), *(s.rva + s.loaded_size for s in sections)])
        size_of_image = -(-end // ALIGN) * ALIGN
    out = Segments({base: bytes(headers(sections, size_of_image))})
    for s in sections:
        assert len(s.data) <= s.loaded_size, (s.name, len(s.data), s.loaded_size)
        out[base + s.rva] = s.data.ljust(s.loaded_size, b"\0")
    return out
