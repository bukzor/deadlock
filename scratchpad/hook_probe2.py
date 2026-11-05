"""Probe, with controls: does connecting a DLL replay its convar queue?

Windows Python only. Re-runs convar_probe.py's experiment (icvar-hook.md) with
what it lacked:

- positive control: a known call (IAppSystem::GetTier, slot 7) through the
  hooked cvar object must show up in the slot log;
- the full interface-request log, and whether the cvar the DLL asked for was
  our hooked object;
- a hook-independent replay detector: each queue entry's last qword points at
  the slot RegisterConVar/RegisterConCommand writes its result into
  (`*pCvarData = ...`, `*cmd.m_Command = ...`). Snapshot those slots before and
  after; any change means registration ran, whatever the hook saw.

usage: hook_probe2.py DLL IFACE [init]
"""

import ctypes
import json
import os
import struct
import sys
from collections import Counter

from convar_probe import BIN, CITADEL_BIN, ConnectFn, CreateInterfaceFn, SlotLog, fingerprint, image_range, read_ptr, say
from convar_scan import qword, walk, writable_sections

STRIDES = {160: "convar", 64: "command"}
BLOCK = 100
REGS = "rax rcx rdx rbx rsp rbp rsi rdi r8 r9 r10 r11 r12 r13 r14 r15".split()
VEH = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.AddVectoredExceptionHandler.restype = ctypes.c_void_p
k32.AddVectoredExceptionHandler.argtypes = (ctypes.c_ulong, VEH)
k32.RemoveVectoredExceptionHandler.argtypes = (ctypes.c_void_p,)


def queue_entries(dll: ctypes.WinDLL) -> dict[str, list[int]]:
    """Per kind, the address of every queue entry, in queue order."""
    image = image_range(dll)
    wsecs = writable_sections(image.start)
    out: dict[str, list[int]] = {}
    for sec in wsecs:
        data = ctypes.string_at(sec.start, len(sec))
        for off in range(0, len(data) - 7, 8):
            (p,) = struct.unpack_from("<Q", data, off)
            if p < 0x10000 or p in image or p % 8:
                continue
            for stride, kind in STRIDES.items():
                if not walk(p, stride, image):
                    continue
                entries: list[int] = []
                block = p
                while block:
                    (n,) = struct.unpack("<I", ctypes.string_at(block, 4))
                    entries += [block + 8 + i * stride for i in range(n)]
                    block = qword(block + 8 + BLOCK * stride) or 0
                if all(any((qword(e + stride - 8) or 0) in w for w in wsecs) for e in entries):
                    assert kind not in out, kind
                    out[kind] = entries
    return out


def queue_slots(dll: ctypes.WinDLL) -> dict[str, list[int]]:
    """Per kind, the address each entry's last qword points at (the result slot)."""
    stride = {kind: s for s, kind in STRIDES.items()}
    return {k: [qword(e + stride[k] - 8) or 0 for e in v] for k, v in queue_entries(dll).items()}


def snapshot(slots: dict[str, list[int]]) -> dict[str, list[int]]:
    return {k: [qword(s) or 0 for s in v] for k, v in slots.items()}


def classify(values: list[int], image: range) -> dict[str, int]:
    return dict(Counter("null" if not v else "in-image" if v in image else "other" for v in values))


def main(dll_name: str, iface: bytes, do_init: bool) -> None:
    os.add_dll_directory(BIN)
    os.add_dll_directory(CITADEL_BIN)
    tier0 = ctypes.WinDLL(rf"{BIN}\tier0.dll")
    tier0_create = CreateInterfaceFn(("CreateInterface", tier0))
    cvar = tier0_create(b"VEngineCvar007", None)
    assert cvar
    say(step="tier0", connect=bool(ConnectFn(read_ptr(read_ptr(cvar)))(cvar, ctypes.cast(tier0_create, ctypes.c_void_p).value)))
    log = SlotLog(cvar, image_range(tier0))

    tier = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p)(read_ptr(read_ptr(cvar) + 8 * 7))(cvar)
    control = log.entries()
    say(step="positive-control", tier=tier, logged=control, ok=[e[0] for e in control] == [7])

    requests: list[dict[str, object]] = []

    @CreateInterfaceFn
    def factory(name: bytes, rc: "ctypes._Pointer[ctypes.c_int]") -> int:
        found = tier0_create(name, None) or 0
        requests.append(dict(name=name.decode(), served=bool(found), is_hooked_cvar=found == cvar))
        if rc:
            rc[0] = 0 if found else 1
        return found

    path = next(rf"{d}\{dll_name}" for d in (BIN, CITADEL_BIN) if os.path.exists(rf"{d}\{dll_name}"))
    dll = ctypes.WinDLL(path)
    image = image_range(dll)
    slots = queue_slots(dll)
    before = snapshot(slots)
    say(step="loaded", calls=len(log.entries()) - len(control), queues={k: len(v) for k, v in slots.items()},
        slot_values={k: classify(v, image) for k, v in before.items()})

    obj = CreateInterfaceFn(("CreateInterface", dll))(iface, None)
    assert obj, iface
    ok = ConnectFn(read_ptr(read_ptr(obj)))(obj, ctypes.cast(factory, ctypes.c_void_p).value)
    report(log, control, slots, before, image, step="connected", ok=ok)
    say(step="requests", n=len(requests), served=[r for r in requests if r["served"]],
        unserved=[r["name"] for r in requests if not r["served"]])
    if do_init:
        faults: list[dict[str, object]] = []
        mods = {"tier0": image_range(tier0), dll_name: image}

        def where(a: int) -> str:
            return next((f"{m}+{a - r.start:#x}" for m, r in mods.items() if a in r), hex(a))

        @VEH
        def on_fault(ptrs: int) -> int:
            rec, ctx = read_ptr(ptrs), read_ptr(ptrs + 8)
            rsp = read_ptr(ctx + 0x98)
            stack = [read_ptr(rsp + 8 * i) for i in range(64)]
            faults.append(dict(code=hex(ctypes.c_uint32.from_address(rec).value), at=where(read_ptr(rec + 16)),
                               addr=hex(read_ptr(rec + 40 + 8)), calls_before=len(log.entries()) - len(control),
                               regs={r: where(read_ptr(ctx + 0x78 + 8 * i)) for i, r in enumerate(REGS)},
                               ret=[where(v) for v in stack if any(v in r for r in mods.values())][:12]))
            return 0  # EXCEPTION_CONTINUE_SEARCH: let ctypes' handler turn it into OSError

        handle = k32.AddVectoredExceptionHandler(1, on_fault)
        try:  # ctypes surfaces an access violation as OSError; the process lives on
            rc: object = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p)(read_ptr(read_ptr(obj) + 8 * 3))(obj)
        except OSError as e:
            rc = str(e)
        k32.RemoveVectoredExceptionHandler(handle)
        report(log, control, slots, before, image, step="init", rc=rc)
        say(step="faults", faults=faults)
    log.restore()  # the DLLs' static destructors call g_pCVar at exit; don't leave them our freed vtable


def report(log: SlotLog, control: list, slots: dict, before: dict, image: range, **kw: object) -> None:
    entries = log.entries()[len(control):]
    after = snapshot(slots)
    changed = {k: sum(a != b for a, b in zip(before[k], after[k])) for k in slots}
    say(**kw, calls=len(entries), slots_called=sorted(Counter(e[0] for e in entries).items()),
        fingerprint=fingerprint(entries), slots_changed=changed,
        slot_values={k: classify(v, image) for k, v in after.items()})


if __name__ == "__main__":
    assert sys.platform == "win32", sys.platform
    main(sys.argv[1], sys.argv[2].encode(), "init" in sys.argv[3:])
