"""Find and walk a DLL's reg-list queues: the per-DLL lists of convar and
concommand creation structs its static initializers queue for `ConVar_Register`
(`docs/dev/cvar-dump.kb/registration-flow.md`, step 2).

A queue is a chain of heap blocks `{u32 m_nSize; Entry_t m_Entries[100];
block* m_pPrev}`, headed by a pointer (`s_pRoot`, the head) in one of the DLL's
writable sections. The root block is the newest and the only partial one; the
walk from it back is the replay order. An entry fits if it starts with a name
pointer and a help pointer into the image and ends with a ref (the `ConVar` or
`ConCommand` that queued it) that passes its kind's `RefTest`.

Two kinds of misfit, kept apart:

- `None`: this candidate is not a queue. The search tries every pointer in the
  writable sections and expects nearly all of them to misfit.
- `ShapeError`: the DLL breaks what the scan relies on, so its result would be
  wrong rather than empty: a writable section unreadable, or a head that more
  than one stride fits.
"""

import re
import struct
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass

from .convar_h import CVarCreationBase_t, offset_of
from .image import Image
from .memory import Memory
from .shape import ShapeError

BLOCK = 100
"""Entries per block (`m_Entries[100]`)."""

_ENTRIES = 8
"""`m_Entries`' offset in a block: `u32 m_nSize`, padded to the entries' 8-byte alignment."""
_NAME, _HELP = (offset_of(CVarCreationBase_t, f) for f in ("m_pszName", "m_pszHelpString"))
"""Where an entry of either kind holds its name and help pointers."""

STRIDES = {"convars": 160, "concommands": 64}
"""`sizeof(Entry_t)` per queue kind, pinned (6848, 6851); `learn_strides` re-derives them."""

CANDIDATE_STRIDES = range(16, 1024, 8)
"""The strides `learn_strides` tries."""

NAME = re.compile(r"[\x21-\x7e]{1,127}")
"""A convar or command name: printable ASCII, no spaces, 1 to 127 bytes."""

UNREGISTERED = 0xFFFF
"""The access index of a `ConCommandRef` not yet registered (s2sdk `convar.h:536`)."""

type RefTest = Callable[[Memory, int, Image], bool]
"""`test(mem, ref, image)`: whether `ref`, an entry's last qword, is a ref its
kind queues. A new kind, or a revised rule for one, is a new `RefTest`."""


def owned_ref(_mem: Memory, ref: int, image: Image) -> bool:
    """`ref` points into the image's writable sections: a global the DLL owns.
    Every convar ref is one (`&ConVar::m_ConVarData`)."""
    return any(ref in section.span for section in image.writable)


def unregistered_command_ref(mem: Memory, ref: int, _image: Image) -> bool:
    """`ref` reads as an unregistered `ConCommandRef`, wherever it lives: a
    command's `ConCommand` can be a member of a heap object
    (`CConCommandMemberAccessor`, `rendersystemdx11`'s `r_textures_evict_all`)."""
    return mem.u16(ref) == UNREGISTERED


REF_TESTS: Mapping[str, RefTest] = {"convars": owned_ref, "concommands": unregistered_command_ref}
"""Each kind's `RefTest`, by `STRIDES` key: `find_queues` applies it."""

_MIN_HEAP = 0x10000
"""Below this no allocation lives (the null page and its neighbours)."""


@dataclass(frozen=True)
class Queue:
    """A queue that fits: `head` is the address of its `s_pRoot` slot;
    `entries` are the entry addresses in replay order (order is position)."""

    head: int
    stride: int
    entries: tuple[int, ...]


def name_at(mem: Memory, addr: int, image: Image) -> str | None:
    """The name at `addr` if it lies in the image and matches `NAME`, else None."""
    text = mem.cstr_in(addr, image.span.start, image.span.stop)
    return text if text is not None and NAME.fullmatch(text) else None


def walk(mem: Memory, root: int, stride: int, image: Image, ref_test: RefTest) -> tuple[int, ...] | None:
    """The entry addresses from block `root` back, in replay order, or None if a
    block's size, a link, or any entry misfits (or the chain loops). An entry's
    ref fits if `ref_test` passes it."""
    entries: list[int] = []
    seen: set[int] = set()
    block = root
    while block:
        size = mem.u32(block)
        if block in seen or size is None or not 0 < size <= BLOCK or (seen and size != BLOCK):
            return None
        seen.add(block)
        for entry in range(block + _ENTRIES, block + _ENTRIES + size * stride, stride):
            if not _fits(mem, entry, stride, image, ref_test):
                return None
            entries.append(entry)
        prev = mem.u64(block + _ENTRIES + BLOCK * stride)
        if prev is None:
            return None
        block = prev
    return tuple(entries)


def _fits(mem: Memory, entry: int, stride: int, image: Image, ref_test: RefTest) -> bool:
    name, help, ref = mem.u64(entry + _NAME), mem.u64(entry + _HELP), mem.u64(entry + stride - 8)
    return (
        name is not None
        and name_at(mem, name, image) is not None
        and help is not None
        and (help == 0 or help in image.span)
        and ref is not None
        and ref_test(mem, ref, image)
    )


def find_queues(mem: Memory, image: Image, kind: str) -> list[Queue]:
    """Every head in the image's writable sections whose queue fits `kind`, a
    `STRIDES` key (its stride and its `REF_TESTS` entry), in address order. A DLL
    has at most one queue per kind: a second one shows up as a second element,
    for the caller to reject."""
    stride, ref_test = STRIDES[kind], REF_TESTS[kind]
    return [Queue(head, stride, e) for head, root in _candidates(mem, image) if (e := walk(mem, root, stride, image, ref_test))]


def learn_strides(mem: Memory, image: Image, strides: Iterable[int] = CANDIDATE_STRIDES) -> list[Queue]:
    """Each head that exactly one stride fits over more than one block, with that
    stride (pass 1 of `queue-shape-scan.md`). A single block can't fix a stride,
    so single-block queues are left out; a head two strides fit is a `ShapeError`.
    No kind is known yet, so every stride gets `owned_ref`, which every entry of
    both kinds' multi-block queues passes (6860). A heap-owned command in such a
    queue would hide it, and the strides check then fails rather than misleads."""
    tried = tuple(strides)
    found: list[Queue] = []
    for head, root in _candidates(mem, image):
        fits = [Queue(head, s, e) for s in tried if (e := walk(mem, root, s, image, owned_ref)) and len(e) > BLOCK]
        if len(fits) > 1:
            raise ShapeError("head fits more than one stride", hex(head), [q.stride for q in fits])
        found += fits
    return found


def _candidates(mem: Memory, image: Image) -> Iterator[tuple[int, int]]:
    """(slot, root) for each aligned qword in a writable section that points
    outside the image at something whose first entry has a name."""
    for section in image.writable:
        data = mem.read(section.span.start, len(section.span))
        if data is None:
            raise ShapeError("writable section unreadable", section.name, hex(section.span.start))
        for i, (root,) in enumerate(struct.iter_unpack("<Q", data[: len(data) // 8 * 8])):
            if root < _MIN_HEAP or root % 8 or root in image.span:
                continue
            name = mem.u64(root + _ENTRIES + _NAME)
            if name is not None and name_at(mem, name, image) is not None:
                yield section.span.start + 8 * i, root
