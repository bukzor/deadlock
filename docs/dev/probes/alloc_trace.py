"""Probe: does interposing tier0's allocator hand us each reg-list queue block?

Loads tier0, swaps its `g_pMemAlloc` object's vtable for one of logging stubs
(every slot: a tail-jump logger of slot, rcx, rdx, r8, return address; slot
`ALLOC`: a call-through that also logs the returned pointer), then loads the
target DLL. Compares what the log says (allocations made from inside the
target) with the queues the shape scan finds, and tries to locate each queue
from the log alone: the head is the target's writable qword that holds the
newest block of a queue-shaped size, and the chain must close over exactly the
logged blocks of that size.

usage: copy into trash/winpy/ (bin/winpy's cwd; siblings import each other), then bin/winpy alloc_trace DLL DIR...
       python -m alloc_trace --encode    (any host: print the stubs' bytes for a disassembler)
"""

import json
import ntpath
import struct
import sys
from collections import Counter

from bukzor_dllscan import reglist, win32
from bukzor_dllscan.image import Image, read_image
from bukzor_dllscan.memory import Memory

ALLOC = 1
"""`MemAlloc_AllocFunc` (tier0 RVA 0x12dd50 on 6860) is `mov rdx, rcx; mov rcx,
[g_pMemAlloc]; mov rax, [rcx]; jmp [rax+8]`: Alloc(this, size) is slot 1."""
RECORD = 64
RECORDS = 1 << 21
EXECUTE = 0x20000000
_SLOT, _RCX, _RDX, _R8, _RET, _RAX = 8, 16, 24, 32, 40, 48


def _q(v: int) -> bytes:
    return v.to_bytes(8, "little")


def _d(v: int) -> bytes:
    return v.to_bytes(4, "little")


def _claim(log: int, skip: int) -> bytes:
    """r11 = log + RECORD * (atomic post-increment of the counter at log+0), or jump `skip` bytes if full."""
    return b"".join((
        b"\x49\xba" + _q(log),  # mov r10, log
        b"\x41\xbb\x01\x00\x00\x00",  # mov r11d, 1
        b"\xf0\x4d\x0f\xc1\x1a",  # lock xadd [r10], r11
        b"\x49\x81\xfb" + _d(RECORDS),  # cmp r11, RECORDS
        b"\x73" + bytes([skip]),  # jae skip
        b"\x49\xc1\xe3\x06",  # shl r11, 6
        b"\x4d\x01\xd3",  # add r11, r10
    ))  # fmt: skip


def tail_logger(log: int, slot: int, orig: int) -> bytes:
    body = b"".join((
        b"\x49\xc7\x43\x08" + _d(slot),  # mov qword [r11+8], slot
        b"\x49\x89\x4b\x10",  # mov [r11+16], rcx
        b"\x49\x89\x53\x18",  # mov [r11+24], rdx
        b"\x4d\x89\x43\x20",  # mov [r11+32], r8
        b"\x4c\x8b\x14\x24",  # mov r10, [rsp]
        b"\x4d\x89\x53\x28",  # mov [r11+40], r10
    ))  # fmt: skip
    return _claim(log, 7 + len(body)) + body + b"\x49\xba" + _q(orig) + b"\x41\xff\xe2"  # mov r10, orig; jmp r10


def call_through(log: int, slot: int, orig: int) -> bytes:
    head = b"".join((
        b"\x48\x83\xec\x38",  # sub rsp, 0x38
        b"\x48\x89\x54\x24\x20",  # mov [rsp+0x20], rdx      (size)
        b"\x48\x8b\x44\x24\x38",  # mov rax, [rsp+0x38]      (return address)
        b"\x48\x89\x44\x24\x28",  # mov [rsp+0x28], rax
        b"\x48\xb8" + _q(orig),  # mov rax, orig
        b"\xff\xd0",  # call rax
    ))  # fmt: skip
    body = b"".join((
        b"\x49\xc7\x43\x08" + _d(slot),  # mov qword [r11+8], slot
        b"\x48\x8b\x54\x24\x20",  # mov rdx, [rsp+0x20]
        b"\x49\x89\x53\x18",  # mov [r11+24], rdx
        b"\x48\x8b\x54\x24\x28",  # mov rdx, [rsp+0x28]
        b"\x49\x89\x53\x28",  # mov [r11+40], rdx
        b"\x49\x89\x43\x30",  # mov [r11+48], rax
    ))  # fmt: skip
    return head + _claim(log, 7 + len(body)) + body + b"\x48\x83\xc4\x38\xc3"  # add rsp, 0x38; ret


def _module(name: str, mem: Memory) -> Image:
    return read_image(mem, win32.module_handle(name))


def main(dll: str, dirs: list[str]) -> None:
    win32.add_dll_directories(dirs)
    mem = Memory(win32.read)
    tier0_base = win32.load_library(ntpath.join(dirs[0], "tier0.dll"))
    tier0 = read_image(mem, tier0_base)
    text = [s.span for s in tier0.sections if s.characteristics & EXECUTE]
    var = win32.proc_address(tier0_base, "g_pMemAlloc")
    obj = mem.u64(var)
    vtable = mem.u64(obj)
    assert obj and vtable
    assert any(obj in s.span for s in tier0.writable), ("g_pMemAlloc object not in tier0's writable data", hex(obj))
    origs: list[int] = []
    while (fn := mem.u64(vtable + 8 * len(origs))) and any(fn in t for t in text):
        origs.append(fn)

    log = win32.alloc_executable(RECORD * RECORDS)
    win32.write(log, _q(1))
    stubs = [call_through(log, i, o) if i == ALLOC else tail_logger(log, i, o) for i, o in enumerate(origs)]
    code = win32.alloc_executable(128 * len(stubs) + 8 * len(stubs))
    table = code + 128 * len(stubs)
    for i, stub in enumerate(stubs):
        assert len(stub) <= 128, (i, len(stub))
        win32.write(code + 128 * i, stub)
        win32.write(table + 8 * i, _q(code + 128 * i))
    win32.write(obj, _q(table))  # one aligned store: every thread switches at once

    image = read_image(mem, win32.load_library(dll))
    n = mem.u64(log) - 1
    win32.write(obj, _q(vtable))
    raw = mem.read(log + RECORD, RECORD * min(n, RECORDS - 1))
    assert raw is not None
    records = [struct.unpack_from("<8Q", raw, i) for i in range(0, len(raw), RECORD)]

    def where(addr: int) -> str:
        return "target" if addr in image.span else "tier0" if addr in tier0.span else "other"

    allocs = [(r[3], r[5], r[6]) for r in records if r[1] == ALLOC]  # size, return address, pointer
    from_target = [(size, p) for size, ret, p in allocs if where(ret) == "target"]
    out: dict[str, object] = {
        "dll": ntpath.basename(dll),
        "vtable_slots": len(origs),
        "calls": n,
        "overflow": n >= RECORDS,
        "calls_by_slot": dict(sorted(Counter(r[1] for r in records).items())),
        "alloc_callers": dict(Counter(where(ret) for _, ret, _ in allocs)),
    }

    # Ground truth from the shape scan: each kind's head slot and blocks.
    scanned: dict[str, dict[str, object]] = {}
    block_set: dict[int, str] = {}
    for kind, stride in reglist.STRIDES.items():
        for q in reglist.find_queues(mem, image, kind):
            blocks, b = [], mem.u64(q.head)
            while b:
                blocks.append(b)
                b = mem.u64(b + 8 + reglist.BLOCK * stride)
            block_set.update((blk, kind) for blk in blocks)
            logged = {p: size for size, p in from_target}
            scanned[kind] = {
                "entries": len(q.entries),
                "blocks": len(blocks),
                "blocks_logged_from_target": sum(blk in logged for blk in blocks),
                "logged_sizes": dict(Counter(logged.get(blk) for blk in blocks)),
                "expected_size": 16 + reglist.BLOCK * stride,
            }
    out["scan"] = scanned

    # Same-size allocations from the target that are not blocks (would confuse a size-only rule).
    queue_sizes = {16 + reglist.BLOCK * s for s in reglist.STRIDES.values()}
    out["queue_sized_non_blocks"] = dict(Counter(size for size, p in from_target if size in queue_sizes and p not in block_set))
    out["queue_shaped_sizes"] = dict(Counter(
        size for size, _ in from_target if size > 16 and (size - 16) % 100 == 0 and (size - 16) // 100 % 8 == 0
    ))

    # The method: locate each queue from the log alone, no shape search.
    derived: dict[str, object] = {}
    words = {}
    for sec in image.writable:
        data = mem.read(sec.span.start, len(sec.span))
        assert data is not None
        for i, (v,) in enumerate(struct.iter_unpack("<Q", data[: len(data) // 8 * 8])):
            words.setdefault(v, []).append(sec.span.start + 8 * i)
    by_size: dict[int, list[int]] = {}
    for size, p in from_target:
        by_size.setdefault(size, []).append(p)
    for size, ps in sorted(by_size.items()):
        if not (size > 16 and (size - 16) % 100 == 0 and (size - 16) // 100 % 8 == 0):
            continue
        stride = (size - 16) // 100
        heads = words.get(ps[-1], [])
        chain, b = [], ps[-1]
        while b and len(chain) <= len(ps):
            chain.append(b)
            b = mem.u64(b + 8 + reglist.BLOCK * stride)
        derived[str(size)] = {
            "stride": stride,
            "allocs": len(ps),
            "head_slots": len(heads),
            "chain_closes_over_allocs": sorted(chain) == sorted(ps),
            "agrees_with_scan": bool(heads) and all(block_set.get(blk) is not None for blk in chain),
        }
    out["derived"] = derived
    print(json.dumps(out))


if __name__ == "__main__":
    if sys.argv[1:] == ["--encode"]:
        log, orig = 0x1111111111111111, 0x2222222222222222
        print(json.dumps({"tail": tail_logger(log, 5, orig).hex(), "through": call_through(log, ALLOC, orig).hex()}))
        sys.exit(0)
    try:
        main(sys.argv[1], sys.argv[2:])
    except BaseException:
        import traceback

        traceback.print_exc()
        win32.hard_exit(1)
    win32.hard_exit(0)
