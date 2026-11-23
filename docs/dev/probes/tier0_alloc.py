"""Probe: can tier0's own queue blocks be caught by interposing its allocator?

tier0 allocates its own queues during its own static init, before
`LoadLibrary` returns, so `alloc_trace` hooks too late for it. Here the hook
goes in from a loader notification (`LdrRegisterDllNotification`, LOADED),
which fires once tier0 is mapped and before its initializers run, if by then
`g_pMemAlloc` already points at an object with a vtable. Then the same
comparison as `alloc_trace`: are the scan's blocks exactly the logged
allocations of `16 + 100 * stride` bytes?

usage: copy into trash/winpy/ (bin/winpy's cwd; siblings import each other), then bin/winpy tier0_alloc TIER0 DIR...
"""

import ctypes
import json
import struct
import sys

from alloc_trace import ALLOC, EXECUTE, RECORD, RECORDS, _q, call_through, tail_logger
from bukzor_dllscan import reglist, win32
from bukzor_dllscan.image import read_image
from bukzor_dllscan.memory import Memory

NOTIFY = ctypes.CFUNCTYPE(None, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p)
LOADED = 1


def main(tier0_path: str, dirs: list[str]) -> None:
    win32.add_dll_directories(dirs)
    mem = Memory(win32.read)
    ntdll = ctypes.CDLL("ntdll")
    ntdll.LdrRegisterDllNotification.argtypes = (ctypes.c_uint32, NOTIFY, ctypes.c_void_p, ctypes.c_void_p)
    state: dict[str, object] = {}
    hooked: dict[str, int] = {}

    @NOTIFY
    def on_load(reason: int, data: int, _context: int) -> None:
        if reason != LOADED:
            return
        base_name = mem.u64(data + 16)
        buffer, length = mem.u64(base_name + 8), mem.u16(base_name)
        name = ctypes.wstring_at(buffer, length // 2).lower()
        if name != "tier0.dll":
            return
        base = mem.u64(data + 24)
        var = win32.proc_address(base, "g_pMemAlloc")
        obj = mem.u64(var)
        vtable = mem.u64(obj) if obj else None
        state.update(var_rva=hex(var - base), obj=hex(obj or 0), vtable=hex(vtable or 0))
        if not (obj and vtable):
            return
        image = read_image(mem, base)
        text = [s.span for s in image.sections if s.characteristics & EXECUTE]
        origs: list[int] = []
        while (fn := mem.u64(vtable + 8 * len(origs))) and any(fn in t for t in text):
            origs.append(fn)
        log = win32.alloc_executable(RECORD * RECORDS)
        win32.write(log, _q(1))
        stubs = [call_through(log, i, o) if i == ALLOC else tail_logger(log, i, o) for i, o in enumerate(origs)]
        code = win32.alloc_executable(136 * len(stubs))
        table = code + 128 * len(stubs)
        for i, stub in enumerate(stubs):
            win32.write(code + 128 * i, stub)
            win32.write(table + 8 * i, _q(code + 128 * i))
        win32.write(obj, _q(table))
        hooked.update(obj=obj, vtable=vtable, log=log, slots=len(origs))

    cookie = ctypes.c_void_p()
    status = ntdll.LdrRegisterDllNotification(0, on_load, None, ctypes.byref(cookie))
    assert status == 0, hex(status)
    tier0_base = win32.load_library(tier0_path)
    out: dict[str, object] = {"at_notification": state, "hooked": bool(hooked)}
    if hooked:
        win32.write(hooked["obj"], _q(hooked["vtable"]))
        n = mem.u64(hooked["log"]) - 1
        raw = mem.read(hooked["log"] + RECORD, RECORD * n) or b""
        records = [struct.unpack_from("<8Q", raw, i) for i in range(0, len(raw), RECORD)]
        image = read_image(mem, tier0_base)
        allocs = {r[6]: (r[3], r[5] in image.span) for r in records if r[1] == ALLOC}
        out.update(calls=n, allocs=len(allocs))
        for kind, stride in reglist.STRIDES.items():
            for q in reglist.find_queues(mem, image, kind):
                blocks, b = [], mem.u64(q.head)
                while b:
                    blocks.append(b)
                    b = mem.u64(b + 8 + reglist.BLOCK * stride)
                size = 16 + reglist.BLOCK * stride
                same_size = [p for p, (s, _) in allocs.items() if s == size]
                out[kind] = {"blocks": len(blocks), "logged": [allocs.get(b) for b in blocks],
                             "same_size_allocs": len(same_size), "exact": sorted(same_size) == sorted(blocks)}
    print(json.dumps(out))


if __name__ == "__main__":
    try:
        main(sys.argv[1], sys.argv[2:])
    except BaseException:
        import traceback

        traceback.print_exc()
        win32.hard_exit(1)
    win32.hard_exit(0)
