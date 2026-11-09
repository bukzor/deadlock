"""A synthetic DLL with reg-list queues, for tests of `reglist` and its
consumers: an image (`image_fake`) whose `.rdata` holds names and whose `.data`
holds head slots and refs, plus heap blocks outside it.

>>> from .reglist import find_queues
>>> fake = Fake()
>>> head, blocks = fake.queue(64, [fake.entry(b"sv_x"), fake.entry(b"sv_y")])
>>> mem, image = fake.load()
>>> [(q.head == head, len(q.entries)) for q in find_queues(mem, image, "concommands")]
[(True, 2)]
"""

import struct

from .image import Image, read_image
from .image_fake import FakeSection, loaded
from .memory import Memory
from .reglist import BLOCK, UNREGISTERED

BASE = 0x180000000
RDATA = BASE + 0x1000
DATA = BASE + 0x10000
SECTION_SIZE = 0x8000
HEAP = 0x10000000

type Entry = tuple[int, int, int]
"""(name pointer, help pointer, trailing ref): the fields `walk` checks."""


class Fake:
    """An image at `BASE`: `.rdata` holds strings, `.data` holds head slots and
    the refs entries point back to. Reg-list blocks live on a heap outside it."""

    def __init__(self) -> None:
        self.rdata: bytearray = bytearray(8)
        self.data: bytearray = bytearray(8)
        self.heap: dict[int, bytearray] = {}

    def string(self, text: bytes) -> int:
        addr = RDATA + len(self.rdata)
        self.rdata += text + b"\0"
        return addr

    def qword(self, value: int = 0) -> int:
        """A new qword in `.data`: a head slot, or a ref's target."""
        addr = DATA + len(self.data)
        self.data += struct.pack("<Q", value)
        return addr

    def entry(self, name: bytes = b"sv_x", help: bytes | None = None, ref: int | None = None) -> Entry:
        """An entry whose ref, by default, is a static unregistered ref in
        `.data`: one that passes every kind's ref test."""
        ref = self.qword(UNREGISTERED) if ref is None else ref
        return (self.string(name), 0 if help is None else self.string(help), ref)

    def heap_ref(self, value: int = UNREGISTERED) -> int:
        """A ref outside the image (a heap-owned `ConCommand`) holding `value`."""
        addr = HEAP - 0x1000 * (1 + sum(b < HEAP for b in self.heap))
        self.heap[addr] = bytearray(struct.pack("<Q", value))
        return addr

    def queue(self, stride: int, entries: list[Entry]) -> tuple[int, list[int]]:
        """Blocks holding `entries` in replay order, and a head slot pointing at
        the first (the root, the only partial one): (slot, block addresses)."""
        first = len(entries) % BLOCK or BLOCK
        chunks = [entries[:first]] + [entries[i : i + BLOCK] for i in range(first, len(entries), BLOCK)]
        blocks = [HEAP + 0x100000 * (len(self.heap) + i) for i in range(len(chunks))]
        for block, prev, chunk in zip(blocks, [*blocks[1:], 0], chunks):
            raw = bytearray(8 + BLOCK * stride + 8)
            struct.pack_into("<I", raw, 0, len(chunk))
            for i, (name, help, ref) in enumerate(chunk):
                struct.pack_into("<QQ", raw, 8 + i * stride, name, help)
                struct.pack_into("<Q", raw, 8 + i * stride + stride - 8, ref)
            struct.pack_into("<Q", raw, 8 + BLOCK * stride, prev)
            self.heap[block] = raw
        return self.qword(blocks[0]), blocks

    def poke(self, addr: int, fmt: str, value: int) -> None:
        (base,) = (b for b, raw in self.heap.items() if b <= addr < b + len(raw))
        struct.pack_into(fmt, self.heap[base], addr - base, value)

    def load(self) -> tuple[Memory, Image]:
        sections = [
            FakeSection(".rdata", RDATA - BASE, 0x40000040, bytes(self.rdata), virtual_size=SECTION_SIZE),
            FakeSection(".data", DATA - BASE, 0xC0000040, bytes(self.data), virtual_size=SECTION_SIZE),
        ]
        segments = loaded(BASE, sections)
        segments.update((base, bytes(raw)) for base, raw in self.heap.items())
        mem = Memory(segments)
        return mem, read_image(mem, BASE)
