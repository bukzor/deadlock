"""Probe: does connecting server.dll replay its convar queue into a hooked ICvar?

Runs under *Windows* Python (the DLLs are win64). Design:
docs/dev/cvar-dump.kb/capture-approach.kb/icvar-hook.md (declined on this result).

1. Load tier0, take its cvar system, Connect it.
2. Point the cvar object at a private vtable whose every slot is a logging stub
   that appends (slot, rdx, r8) to a buffer and tail-jumps to the original.
3. Load server.dll, Connect its app system through a factory that serves tier0's
   interfaces and logs every request.
4. Find the registration slots by the stride fingerprint.
"""

import ctypes
import json
import re
import os
import struct
import sys
from collections import Counter, defaultdict
from ctypes import wintypes as wt

GAME = r"C:\Program Files (x86)\Steam\steamapps\common\Deadlock\game"
BIN = rf"{GAME}\bin\win64"
CITADEL_BIN = rf"{GAME}\citadel\bin\win64"
CVAR_PREFIX = b"VEngineCvar"
LOG_ENTRIES = 1 << 16
STUB_SIZE = 48  # 44 bytes of code, padded

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.VirtualAlloc.restype = ctypes.c_void_p
k32.VirtualAlloc.argtypes = (ctypes.c_void_p, ctypes.c_size_t, wt.DWORD, wt.DWORD)

CreateInterfaceFn = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)
)
ConnectFn = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)


def say(**kw: object) -> None:
    print(json.dumps(kw), flush=True)


def read_ptr(addr: int) -> int:
    return ctypes.c_void_p.from_address(addr).value or 0


def image_range(dll: ctypes.WinDLL) -> range:
    base = dll._handle
    nt = base + ctypes.c_uint32.from_address(base + 0x3C).value
    size = ctypes.c_uint32.from_address(nt + 0x50).value  # SizeOfImage
    return range(base, base + size)


def stub(cursor: int, slot: int, target: int) -> bytes:
    code = b"".join([
        b"\x49\xbb" + struct.pack("<Q", cursor),  # mov r11, &cursor
        b"\x4d\x8b\x13",  # mov r10, [r11]
        b"\x49\xc7\x02" + struct.pack("<i", slot),  # mov qword [r10], slot
        b"\x49\x89\x52\x08",  # mov [r10+8], rdx
        b"\x4d\x89\x42\x10",  # mov [r10+16], r8
        b"\x49\x83\x03\x18",  # add qword [r11], 24
        b"\x48\xb8" + struct.pack("<Q", target),  # mov rax, target
        b"\xff\xe0",  # jmp rax
    ])
    assert len(code) <= STUB_SIZE, len(code)
    return code.ljust(STUB_SIZE, b"\xcc")


class SlotLog:
    """Logging vtable installed over a live object; keeps its memory alive."""

    def __init__(self, obj: int, code_range: range) -> None:
        vtbl = read_ptr(obj)
        n = 0
        while read_ptr(vtbl + 8 * n) in code_range:
            n += 1
        self.n_slots = n
        self.buf = (ctypes.c_uint64 * (3 * LOG_ENTRIES))()
        self.cursor = ctypes.c_uint64(ctypes.addressof(self.buf))
        code = k32.VirtualAlloc(None, STUB_SIZE * n, 0x3000, 0x40)  # RWX
        assert code, ctypes.get_last_error()
        cursor_addr = ctypes.addressof(self.cursor)
        for i in range(n):
            ctypes.memmove(code + STUB_SIZE * i, stub(cursor_addr, i, read_ptr(vtbl + 8 * i)), STUB_SIZE)
        # slot -1 is MSVC's RTTI locator; keep it so dynamic_cast still works
        self.vtbl = (ctypes.c_void_p * (n + 1))(read_ptr(vtbl - 8), *(code + STUB_SIZE * i for i in range(n)))
        ctypes.c_void_p.from_address(obj).value = ctypes.addressof(self.vtbl) + 8
        self.obj, self.orig_vtbl = obj, vtbl

    def restore(self) -> None:
        ctypes.c_void_p.from_address(self.obj).value = self.orig_vtbl

    def entries(self) -> list[tuple[int, int, int]]:
        count = (self.cursor.value - ctypes.addressof(self.buf)) // 24
        assert count < LOG_ENTRIES, count
        b = self.buf
        return [(b[3 * i], b[3 * i + 1], b[3 * i + 2]) for i in range(count)]


def fingerprint(entries: list[tuple[int, int, int]]) -> list[dict[str, object]]:
    """Slots whose rdx or r8 advances by one constant stride, call after call."""
    by_slot: defaultdict[int, list[tuple[int, int]]] = defaultdict(list)
    for slot, rdx, r8 in entries:
        by_slot[slot].append((rdx, r8))
    found: list[dict[str, object]] = []
    for slot, args in sorted(by_slot.items()):
        for reg, idx in (("rdx", 0), ("r8", 1)):
            diffs = Counter(b[idx] - a[idx] for a, b in zip(args, args[1:]))
            if not diffs:
                continue
            stride, hits = diffs.most_common(1)[0]
            if 0 < stride < 4096 and hits >= 50:
                found.append({"slot": slot, "reg": reg, "stride": stride, "hits": hits, "calls": len(args)})
    return found


QUEUE_SIG = re.compile(rb"\x4c\x8b\x0d(....)\x4d\x85\xc9\x74.\x45\x8b\x01\x41\x83\xf8\x64", re.S)


def queue_heads(dll: ctypes.WinDLL) -> list[int]:
    """Diagnostic only (DumpSource2's signature): m_nSize of each convar queue head."""
    r = image_range(dll)
    image = ctypes.string_at(r.start, len(r))
    heads: list[int] = []
    for m in QUEUE_SIG.finditer(image):
        (disp,) = struct.unpack("<i", m.group(1))
        root = read_ptr(r.start + m.start() + 7 + disp)
        heads.append(ctypes.c_uint32.from_address(root).value if root else -1)
    return heads


def call_init(dll: ctypes.WinDLL, iface: bytes) -> int:
    obj = CreateInterfaceFn(("CreateInterface", dll))(iface, None)
    return ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p)(read_ptr(read_ptr(obj) + 8 * 3))(obj)


def connect(dll: ctypes.WinDLL, iface: bytes, factory: object) -> bool:
    create = CreateInterfaceFn(("CreateInterface", dll))
    obj = create(iface, None)
    assert obj, iface
    return ConnectFn(read_ptr(read_ptr(obj)))(obj, ctypes.cast(factory, ctypes.c_void_p).value)


def main() -> None:
    os.add_dll_directory(BIN)
    os.add_dll_directory(CITADEL_BIN)
    tier0 = ctypes.WinDLL(rf"{BIN}\tier0.dll")
    tier0_create = CreateInterfaceFn(("CreateInterface", tier0))

    cvar_name = next(n for n in (CVAR_PREFIX + b"%03d" % v for v in range(1, 20)) if tier0_create(n, None))
    cvar = tier0_create(cvar_name, None)
    say(step="tier0", cvar=cvar_name.decode(), connect=bool(ConnectFn(read_ptr(read_ptr(cvar)))(cvar, ctypes.cast(tier0_create, ctypes.c_void_p).value)))

    log = SlotLog(cvar, image_range(tier0))
    say(step="hooked", slots=log.n_slots)

    requests: list[tuple[str, bool]] = []

    @CreateInterfaceFn
    def factory(name: bytes, rc: "ctypes._Pointer[ctypes.c_int]") -> int:
        found = tier0_create(name, None) or 0
        requests.append((name.decode(), bool(found)))
        if rc:
            rc[0] = 0 if found else 1
        return found

    server = ctypes.WinDLL(rf"{CITADEL_BIN}\server.dll")
    say(step="loaded", dll="server", calls_so_far=len(log.entries()), queue_heads=queue_heads(server))
    ok = connect(server, b"Source2ServerConfig001", factory)
    entries = log.entries()
    say(step="connected", dll="server", ok=ok, calls=len(entries), slots_called=sorted(Counter(e[0] for e in entries).items()))
    say(step="requests", served=[n for n, ok in requests if ok], unserved=len([n for n, ok in requests if not ok]))
    say(step="fingerprint", found=fingerprint(entries), queue_heads=queue_heads(server))
    if "init" in sys.argv:
        say(step="init", rc=call_init(server, b"Source2ServerConfig001"))
        entries = log.entries()
        say(step="after-init", calls=len(entries), fingerprint=fingerprint(entries), queue_heads=queue_heads(server))


if __name__ == "__main__":
    assert sys.platform == "win32", sys.platform
    main()
