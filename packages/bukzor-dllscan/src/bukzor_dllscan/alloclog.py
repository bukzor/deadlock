"""Find a DLL's reg-list queues from the allocations that built them
(`docs/dev/cvar-dump.kb/capture-approach.kb/allocator-hook.md`).

Each queue block is one call into tier0's allocator, `g_pMemAlloc`'s `Alloc`
slot, made by the DLL's static initializers while it loads. `load` loads
tier0, points its allocator object at a copy of its vtable whose `Alloc` slot
is `stub`, loads the DLL, and puts the vtable back. The stub logs (size,
caller, block) for every allocation of a block's size. `locate` then finds a
queue by equality, not search: its head is the one writable qword of the DLL
that holds the newest block the DLL allocated, and the chain from it must
close over exactly the blocks the DLL allocated.

tier0's own queues are allocated before `g_pMemAlloc` is set, so no hook can
see them: `load` reports that case as no log, and the caller falls back to
the shape scan (`reglist.find_queues`).

Everything native is in `load`; the rest is pure over `Memory`.
"""

import ntpath
import os
import struct
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from . import win32
from .image import Image, read_image
from .memory import Memory
from .reglist import BLOCK, ENTRIES, REF_TESTS, STRIDES, Queue, walk
from .shape import ShapeError

SIZES = {kind: ENTRIES + BLOCK * stride + 8 for kind, stride in STRIDES.items()}
"""A block's allocation size per queue kind: `m_nSize` padded, the entries, `m_pPrev`."""

RECORD = 32
"""A log record: (unused, size, caller, block), u64 each. Record 0 is the header:
the next record's index, so the count is that minus 1."""
RECORDS = 1 << 12
"""Log capacity; a load that fills it fails, it is never truncated."""

TIER0 = "tier0.dll"
EXECUTE = 0x20000000
"""`IMAGE_SCN_MEM_EXECUTE`."""


@dataclass(frozen=True)
class Alloc:
    """One logged allocation: its `size`, the `caller`'s return address, the `block` returned."""

    size: int
    caller: int
    block: int


def alloc_slot(code: bytes, func: int, var: int) -> int:
    """The vtable slot tier0's `MemAlloc_AllocFunc` (at `func`, `code` its
    first 17 bytes) jumps through: `mov rdx, rcx; mov rcx, [rip+var]; mov rax,
    [rcx]; jmp [rax+8*slot]`, `var` being `g_pMemAlloc`. `ShapeError` if the
    code is anything else.

    >>> alloc_slot(bytes.fromhex("488bd1488b0dbee82700488b0148ff6008"), 0x12dd50, 0x3ac618)
    1
    """
    if len(code) != 17 or code[:6] != b"\x48\x8b\xd1\x48\x8b\x0d" or code[10:16] != b"\x48\x8b\x01\x48\xff\x60":
        raise ShapeError("MemAlloc_AllocFunc", code.hex())
    (rel,) = struct.unpack_from("<i", code, 6)
    if func + 10 + rel != var or code[16] % 8:
        raise ShapeError("MemAlloc_AllocFunc", code.hex(), hex(func + 10 + rel), hex(var))
    return code[16] // 8


def _claim(log: int, body: bytes) -> bytes:
    """`body` run with r11 = log + RECORD * (atomic post-increment of the
    header), skipped if the log is full."""
    return b"".join((
        b"\x49\xba" + log.to_bytes(8, "little"),  # mov r10, log
        b"\x41\xbb\x01\x00\x00\x00",  # mov r11d, 1
        b"\xf0\x4d\x0f\xc1\x1a",  # lock xadd [r10], r11
        b"\x49\x81\xfb" + RECORDS.to_bytes(4, "little"),  # cmp r11, RECORDS
        b"\x73" + bytes([7 + len(body)]),  # jae past body
        b"\x49\xc1\xe3\x05",  # shl r11, 5      (RECORD)
        b"\x4d\x01\xd3",  # add r11, r10
        body,
    ))  # fmt: skip


def stub(log: int, orig: int, sizes: Iterable[int]) -> bytes:
    """`Alloc(this, size)` that tail-jumps to `orig` unless `size` is one of
    `sizes`; for those, it calls `orig` and logs (size, caller, block) at `log`."""
    passthrough = b"\x49\xba" + orig.to_bytes(8, "little") + b"\x41\xff\xe2"  # mov r10, orig; jmp r10
    tests = b""
    for size in reversed(list(sizes)):
        rest = len(tests) + len(passthrough)
        tests = b"\x48\x81\xfa" + size.to_bytes(4, "little") + b"\x74" + bytes([rest]) + tests  # cmp rdx, size; je log
    call = b"".join((
        b"\x48\x83\xec\x38",  # sub rsp, 0x38
        b"\x48\x89\x54\x24\x20",  # mov [rsp+0x20], rdx      (size)
        b"\x48\x8b\x44\x24\x38",  # mov rax, [rsp+0x38]      (return address)
        b"\x48\x89\x44\x24\x28",  # mov [rsp+0x28], rax
        b"\x48\xb8" + orig.to_bytes(8, "little"),  # mov rax, orig
        b"\xff\xd0",  # call rax
    ))  # fmt: skip
    record = b"".join((
        b"\x48\x8b\x54\x24\x20",  # mov rdx, [rsp+0x20]
        b"\x49\x89\x53\x08",  # mov [r11+8], rdx
        b"\x48\x8b\x54\x24\x28",  # mov rdx, [rsp+0x28]
        b"\x49\x89\x53\x10",  # mov [r11+16], rdx
        b"\x49\x89\x43\x18",  # mov [r11+24], rax
    ))  # fmt: skip
    return tests + passthrough + call + _claim(log, record) + b"\x48\x83\xc4\x38\xc3"  # add rsp, 0x38; ret


def read_log(mem: Memory, log: int) -> list[Alloc]:
    """The log's records in the order they were claimed; `ShapeError` if it filled."""
    head = mem.u64(log)
    assert head, hex(log)
    if head > RECORDS:
        raise ShapeError("allocation log full", head - 1, RECORDS - 1)
    raw = mem.read(log + RECORD, RECORD * (head - 1)) if head > 1 else b""
    assert raw is not None, hex(log)
    return [Alloc(*struct.unpack_from("<3Q", raw, i + 8)) for i in range(0, len(raw), RECORD)]


def locate(mem: Memory, image: Image, kind: str, log: Sequence[Alloc]) -> Queue | None:
    """The image's `kind` queue from the blocks it allocated, or None if it
    allocated none. `ShapeError` unless exactly one writable qword holds the
    newest block, the chain from it fits `kind` and it runs back over
    exactly the image's blocks, newest first."""
    blocks = [a.block for a in log if a.size == SIZES[kind] and a.caller in image.span]
    if not blocks:
        return None
    stride = STRIDES[kind]
    heads = _slots_holding(mem, image, blocks[-1])
    if len(heads) != 1:
        raise ShapeError(f"{kind} head slots", hex(blocks[-1]), [hex(h) for h in heads])
    entries = walk(mem, blocks[-1], stride, image, REF_TESTS[kind])
    if entries is None:
        raise ShapeError(f"{kind} queue misfits", hex(heads[0]))
    chain: list[int] = []
    block = blocks[-1]
    while block:  # `walk` read every link, and found no loop
        chain.append(block)
        block = mem.u64(block + ENTRIES + BLOCK * stride) or 0
    if chain != blocks[::-1]:
        raise ShapeError(f"{kind} chain and allocations differ", [hex(b) for b in chain], [hex(b) for b in blocks])
    return Queue(heads[0], stride, entries)


def _slots_holding(mem: Memory, image: Image, value: int) -> list[int]:
    found: list[int] = []
    for section in image.writable:
        data = mem.read(section.span.start, len(section.span))
        if data is None:
            raise ShapeError("writable section unreadable", section.name, hex(section.span.start))
        found += [section.span.start + 8 * i for i, (v,) in enumerate(struct.iter_unpack("<Q", data[: len(data) // 8 * 8])) if v == value]
    return found


def load(dll: str, dirs: Sequence[str]) -> tuple[Memory, Image, list[Alloc] | None]:
    """Load `dll` (a Windows path; each of `dirs` searched) with tier0's
    allocator logged; its memory, layout and log, or no log if `dll` is tier0."""
    win32.add_dll_directories(dirs)
    mem = Memory(win32.read)
    (tier0_path,) = [p for d in dirs if os.path.exists(p := ntpath.join(d, TIER0))]
    tier0_base = win32.load_library(tier0_path)
    tier0 = read_image(mem, tier0_base)
    var = win32.proc_address(tier0_base, "g_pMemAlloc")
    func = win32.proc_address(tier0_base, "MemAlloc_AllocFunc")
    code = mem.read(func, 17)
    assert code is not None, hex(func)
    slot = alloc_slot(code, func, var)
    obj, text = mem.u64(var), [s.span for s in tier0.sections if s.characteristics & EXECUTE]
    vtable = mem.u64(obj) if obj else None
    assert obj and vtable, ("g_pMemAlloc unset after tier0 loaded", hex(var))
    methods: list[int] = []
    while (fn := mem.u64(vtable + 8 * len(methods))) and any(fn in t for t in text):
        methods.append(fn)
    assert slot < len(methods), (slot, len(methods))

    log = win32.alloc_executable(RECORD * RECORDS)
    win32.write(log, (1).to_bytes(8, "little"))
    code_at = win32.alloc_executable(0x100 + 8 * len(methods))
    hook = stub(log, methods[slot], SIZES.values())
    assert len(hook) <= 0x100, len(hook)
    win32.write(code_at, hook)
    table = code_at + 0x100
    win32.write(table, b"".join(fn.to_bytes(8, "little") for fn in methods[:slot] + [code_at] + methods[slot + 1 :]))
    win32.write(obj, table.to_bytes(8, "little"))  # one aligned store: every thread switches at once
    try:
        base = win32.load_library(dll)
    finally:
        win32.write(obj, vtable.to_bytes(8, "little"))
    return mem, read_image(mem, base), None if base == tier0_base else read_log(mem, log)
