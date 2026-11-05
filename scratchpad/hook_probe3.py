"""Probe: placeholder-interface factory, controlled Init, then read tier0's registry back.

Windows Python only. Builds on hook_probe2.py (icvar-hook.md):

1. Factory: tier0 serves what it can; every other name gets its own placeholder
   object whose vtable slots are stubs that record (this, slot) and execute
   `ud2`. The first use of a missing dependency stops the call with an exception
   that names it, instead of a null read somewhere later.
2. Connect + Init the DLL under the hooked cvar; the stop surfaces as OSError.
3. Restore tier0's vtable and walk its registry with its own iteration slots
   (FindFirst/FindNext + Get...Data), then compare it with the DLL's queue.

usage: hook_probe3.py DLL IFACE  -> summary on stdout, registry to registry_<dll>.jsonl
"""

import ctypes
import json
import os
import struct
import sys
from collections import Counter

from convar_probe import BIN, CITADEL_BIN, ConnectFn, CreateInterfaceFn, SlotLog, image_range, k32, read_ptr, say
from convar_scan import peek, qword
from hook_probe2 import STRIDES, queue_entries

N_SLOTS = 512
STUB = 64
TYPES = "bool int8 uint8 int16 uint16 int32 uint32 int64 uint64 float32 float64 string color vector2 vector3 vector4 qangle vectorws".split()
SCALAR = dict(zip(TYPES[:11], "?bBhHiIqQfd"))  # int8/uint8: binary differs from s2sdk here (6854)
FLOATS = dict(vector2=2, vector3=3, vector4=4, qangle=3)


class Placeholders:
    """One placeholder object per name; all share a vtable of recording `ud2` stubs."""

    def __init__(self) -> None:
        # cell: [0] this, [1] slot of the trap; [2] mode (0: record and return 0, 1: trap); [3] calls; [4..] call log
        self.cell = (ctypes.c_uint64 * (4 + 2 * 65536))()
        code = k32.VirtualAlloc(None, STUB * N_SLOTS, 0x3000, 0x40)
        cell = ctypes.addressof(self.cell)
        for i in range(N_SLOTS):
            slot = struct.pack("<i", i)
            stub = (b"\x49\xbb" + struct.pack("<Q", cell)  # mov r11, &cell
                    + b"\x49\x83\x7b\x10\x00"  # cmp qword [r11+16], 0
                    + b"\x75\x1e"  # jne trap
                    + b"\x49\x8b\x43\x18"  # mov rax, [r11+24]      (n = calls)
                    + b"\x49\xff\x43\x18"  # inc qword [r11+24]
                    + b"\x48\xc1\xe0\x04"  # shl rax, 4             (16 bytes per call)
                    + b"\x4c\x01\xd8"  # add rax, r11
                    + b"\x48\x89\x48\x20"  # mov [rax+32], rcx
                    + b"\x48\xc7\x40\x28" + slot  # mov qword [rax+40], slot
                    + b"\x31\xc0\xc3"  # xor eax, eax; ret
                    # trap:
                    + b"\x49\x89\x0b"  # mov [r11], rcx
                    + b"\x49\xc7\x43\x08" + slot  # mov qword [r11+8], slot
                    + b"\x0f\x0b")  # ud2
            assert len(stub) <= STUB, len(stub)
            ctypes.memmove(code + STUB * i, stub.ljust(STUB, b"\xcc"), STUB)
        self.vtbl = (ctypes.c_void_p * N_SLOTS)(*(code + STUB * i for i in range(N_SLOTS)))
        self.objs: dict[int, tuple[str, ctypes.Array]] = {}

    def arm(self) -> None:
        self.cell[2] = 1

    def calls(self) -> list[tuple[str, int]]:
        n = min(self.cell[3], 65536)
        return [(self.objs.get(self.cell[4 + 2 * i], ("?",))[0], self.cell[5 + 2 * i]) for i in range(n)]

    def make(self, name: str) -> int:
        obj = (ctypes.c_void_p * 16)(ctypes.addressof(self.vtbl))  # zeroed fields after the vptr
        self.objs[ctypes.addressof(obj)] = (name, obj)
        return ctypes.addressof(obj)

    def tripped(self) -> dict[str, object] | None:
        this, slot = self.cell[0], self.cell[1]
        return dict(iface=self.objs[this][0], slot=slot) if this in self.objs else None


def call(fn_addr: int, restype, *args):  # noqa: ANN001, ANN201 - thin ctypes shim
    return ctypes.CFUNCTYPE(restype, *(ctypes.c_void_p if isinstance(a, int) or a is None else type(a) for a in args))(fn_addr)(*args)


def walk_registry(cvar: int, vtbl: int, first: int, nxt: int, get: int) -> list[tuple[int, int]]:
    """(ref, data pointer) of every item tier0's own iteration yields (hidden return ptr)."""
    ret = ctypes.c_uint64()
    call(read_ptr(vtbl + 8 * first), ctypes.c_void_p, cvar, ctypes.addressof(ret))
    out: list[int] = []
    while ret.value & 0xFFFF != 0xFFFF and len(out) < 100_000:
        out.append((ret.value, call(read_ptr(vtbl + 8 * get), ctypes.c_void_p, cvar, ctypes.c_uint64(ret.value)) or 0))
        prev = ctypes.c_uint64(ret.value)
        call(read_ptr(vtbl + 8 * nxt), ctypes.c_void_p, cvar, ctypes.addressof(ret), prev)
    return out


ITER = {"convar": (12, 13, 41), "command": (18, 19, 44)}  # FindFirst, FindNext, Get...Data


def by_access_index(cvar: int, vtbl: int, get: int) -> list[int]:
    """Data pointer for every access index, hidden ones included, until an invalid one."""
    out: list[int] = []
    for i in range(0xFFFF):
        try:
            d = call(read_ptr(vtbl + 8 * get), ctypes.c_void_p, cvar, ctypes.c_uint64(i)) or 0
        except OSError:
            break
        if not d or d in out[-1:] or cstr(read_ptr(d)) in (None, "<undefined>"):
            break
        out.append(d)
    return out


def cstr(p: int) -> str | None:
    """NUL-terminated string at p, or None if p is null or unreadable (a wrong layout guess must not crash)."""
    if not p or peek(p, 1) is None:
        return None
    out = bytearray()
    while len(out) < 4096 and (c := peek(p + len(out), 1)) not in (None, b"\0"):
        out += c
    return out.decode("utf-8", "replace")


def value(p: int, t: str) -> object:
    if not p:
        return None
    if t in SCALAR:
        return struct.unpack("<" + SCALAR[t], ctypes.string_at(p, struct.calcsize(SCALAR[t])))[0]
    if t == "string":
        return cstr(read_ptr(p))
    if t == "color":
        return list(ctypes.string_at(p, 4))
    if t in FLOATS:
        return list(struct.unpack(f"<{FLOATS[t]}f", ctypes.string_at(p, 4 * FLOATS[t])))
    return ctypes.string_at(p, 24).hex()


def convar_record(d: int) -> dict[str, object]:
    t_idx = ctypes.c_int16.from_address(d + 40).value
    t = TYPES[t_idx] if 0 <= t_idx < len(TYPES) else f"type_{t_idx}"
    return dict(kind="convar", raw=(peek(d, 0x70) or b"").hex(), raw_default=(peek(read_ptr(d + 8), 16) or b"").hex(), name=cstr(read_ptr(d)), type=t, flags=qword(d + 48), default=value(read_ptr(d + 8), t),
                min=value(read_ptr(d + 16), t), max=value(read_ptr(d + 24), t), help=cstr(read_ptr(d + 32)))


def command_record(d: int) -> dict[str, object]:
    return dict(kind="command", name=cstr(read_ptr(d)), flags=qword(d + 16), help=cstr(read_ptr(d + 8)))


def main(dll_name: str, iface: bytes) -> None:
    os.add_dll_directory(BIN)
    os.add_dll_directory(CITADEL_BIN)
    tier0 = ctypes.WinDLL(rf"{BIN}\tier0.dll")
    tier0_create = CreateInterfaceFn(("CreateInterface", tier0))
    cvar = tier0_create(b"VEngineCvar007", None)
    ConnectFn(read_ptr(read_ptr(cvar)))(cvar, ctypes.cast(tier0_create, ctypes.c_void_p).value)
    log = SlotLog(cvar, image_range(tier0))
    ph = Placeholders()
    served: Counter[str] = Counter()

    @CreateInterfaceFn
    def factory(name: bytes, rc: "ctypes._Pointer[ctypes.c_int]") -> int:
        found = tier0_create(name, None) or 0
        served["tier0" if found else "placeholder"] += 1
        if rc:
            rc[0] = 0
        return found or ph.make(name.decode())

    path = next(rf"{d}\{dll_name}" for d in (BIN, CITADEL_BIN) if os.path.exists(rf"{d}\{dll_name}"))
    dll = ctypes.WinDLL(path)
    queue = queue_entries(dll)
    obj = CreateInterfaceFn(("CreateInterface", dll))(iface, None)
    for step, slot, args in (("connect", 0, (ctypes.cast(factory, ctypes.c_void_p).value,)), ("init", 3, ())):
        try:
            rc: object = call(read_ptr(read_ptr(obj) + 8 * slot), ctypes.c_int, obj, *args)
        except OSError as e:
            rc = str(e)
        reg_calls = Counter(e[0] for e in log.entries() if e[0] in (38, 42))
        say(step=step, rc=rc, served=dict(served), tripped=ph.tripped(), register_calls=dict(reg_calls),
            placeholder_calls=Counter(f"{n}#{s}" for n, s in ph.calls()))
        if ph.tripped():
            break
        ph.arm()
    log.restore()
    infos = {"convar": [rdx for s, rdx, _ in log.entries() if s == 38], "command": [r8 for s, _, r8 in log.entries() if s == 42]}
    for kind, args in infos.items():
        queued = set(queue.get(kind, []))  # an entry's address is its m_Info's: m_Info leads Entry_t
        extra = [a for a in args if a not in queued]
        names = Counter(cstr(read_ptr(a)) for a in args)
        say(step="calls-vs-queue", kind=kind, calls=len(args), from_queue=len(args) - len(extra), distinct_args=len(set(args)),
            extra=[dict(name=cstr(read_ptr(a)), flags=hex(qword(a + 16) or 0), in_image=a in image_range(dll),
                        order=args.index(a)) for a in extra],
            same_name_twice=[n for n, c in names.items() if c > 1])

    vtbl = read_ptr(cvar)
    walked = {kind: walk_registry(cvar, vtbl, *slots) for kind, slots in ITER.items()}
    say(step="walk", **{k: dict(n=len(v), refs=[hex(r) for r, _ in v[:4]], max_access=max((r & 0xFFFF for r, _ in v), default=None))
                        for k, v in walked.items()})
    by_index = {kind: by_access_index(cvar, vtbl, ITER[kind][2]) for kind in ITER}
    say(step="by-index", **{k: dict(n=len(v), first=v[:3] and [hex(d) for d in v[:3]]) for k, v in by_index.items()})
    reg = [convar_record(d) for d in by_index["convar"]] + [command_record(d) for d in by_index["command"]]
    with open(f"registry_{dll_name}.jsonl", "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in reg)
    compare(reg, queue)


def compare(reg: list[dict[str, object]], queue: dict[str, list[int]]) -> None:
    stride = {kind: s for s, kind in STRIDES.items()}
    for kind in ("convar", "command"):
        mine = {r["name"]: r for r in reg if r["kind"] == kind}
        q = {cstr(read_ptr(e)): qword(e + 16) for e in queue.get(kind, [])}
        flag_xor = Counter(hex((mine[n]["flags"] or 0) ^ f) for n, f in q.items() if n in mine)
        say(step="compare", kind=kind, registry=len(mine), queue=len(q), queue_missing_from_registry=sorted(set(q) - set(mine))[:10],
            registry_only=len(set(mine) - set(q)), registry_flags_xor_queue_flags=dict(flag_xor.most_common(5)),
            types=dict(Counter(r.get("type") for r in mine.values())), stride=stride[kind])


if __name__ == "__main__":
    assert sys.platform == "win32", sys.platform
    main(sys.argv[1], sys.argv[2].encode())
    sys.stdout.flush()
    k32.TerminateProcess(ctypes.c_void_p(-1), 0)  # skip DLL detach: static destructors would call freed placeholders
