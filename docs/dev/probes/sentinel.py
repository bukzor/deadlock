"""Probe: what is `*m_pConVarData` before registration (one value per type, 6860)?

For each convar type in the DLL's queue: where the target lives (module,
section, RVA), and the target read as s2sdk's `ConVarData` (`bukzor_dllscan.registry`):
its name, its `m_eVarType` against the entries' type code, and its value
pointers. Also each target's qwords classified, in case it points at tier0's
type-traits table.

usage: copy into trash/winpy/ (bin/winpy's cwd; siblings import each other), then bin/winpy sentinel DLL DIR...
"""

import ctypes
import json
import ntpath
import sys

from bukzor_dllscan import reglist, win32
from bukzor_dllscan.convar_h import ConVarRegList_Entry_t, offset_of
from bukzor_dllscan.image import read_image
from bukzor_dllscan.memory import Memory
from bukzor_dllscan.registry import ConVarData

PD = offset_of(ConVarRegList_Entry_t, "m_pConVarData")
TY = offset_of(ConVarRegList_Entry_t, "m_Info.m_valueInfo.m_eVarType")


def main(dll: str, dirs: list[str]) -> None:
    win32.add_dll_directories(dirs)
    mem = Memory(win32.read)
    image = read_image(mem, win32.load_library(dll))
    modules = {n: read_image(mem, win32.module_handle(n)) for n in win32.module_names() if n in ("tier0.dll", ntpath.basename(dll).lower())}

    def where(addr: int) -> str:
        for name, img in modules.items():
            for s in img.sections:
                if addr in s.span:
                    return f"{name}:{s.name}+{addr - img.span.start:#x}"
        return "heap" if addr else "null"

    (q,) = reglist.find_queues(mem, image, "convars")
    by_type: dict[int, int] = {}
    for e in q.entries:
        code, target = mem.u16(e + TY), mem.u64(mem.u64(e + PD))
        assert by_type.setdefault(code, target) == target, code
    out = {}
    for code, target in sorted(by_type.items()):
        raw = mem.read(target, 0x60)
        assert raw is not None
        data = ConVarData.from_buffer_copy(raw)
        out[code] = {
            "at": where(target),
            "name": mem.cstr_in(data.m_pszName, 0, 1 << 64) if data.m_pszName else None,
            "m_eVarType": data.m_eVarType,
            "type_matches_code": data.m_eVarType == code,
            "version": data.m_Version,
            "default/min/max": [where(p) for p in (data.m_defaultValue, data.m_minValue, data.m_maxValue)],
            "qwords": [where(int.from_bytes(raw[i : i + 8], "little")) if int.from_bytes(raw[i : i + 8], "little") > 0xFFFFFFFF else hex(int.from_bytes(raw[i : i + 8], "little")) for i in range(0, 0x60, 8)],
        }
    (c0, t0), (c1, t1) = sorted(by_type.items())[:2]
    step = (t1 - t0) // (c1 - c0)
    base = t0 - c0 * step
    assert all(t == base + c * step for c, t in by_type.items()), "not one array"
    length = 0  # walk the array past the used types, while each element is element `length` of its type
    while (raw := mem.read(base + length * step, ctypes.sizeof(ConVarData))) is not None:
        data = ConVarData.from_buffer_copy(raw)
        if data.m_eVarType != length or (mem.cstr_in(data.m_pszName, 0, 1 << 64) if data.m_pszName else None) != "<undefined>":
            break
        length += 1
    traits = []  # the 88-byte rows just before the array: name pointer, then size?
    for i in range(length):
        row = base - (length - i) * 88
        traits.append([mem.cstr_in(mem.u64(row) or 0, 0, 1 << 64), mem.u32(row + 8), where(row)])
    from bukzor_dllscan.values import TYPES
    print(json.dumps({"traits_match_TYPES": [(n, s) for n, s, _ in traits] == list(TYPES.items()), "traits": traits}))
    after = ConVarData.from_buffer_copy(mem.read(base + length * step, ctypes.sizeof(ConVarData)) or bytes(ctypes.sizeof(ConVarData)))
    print(json.dumps({"dll": ntpath.basename(dll), "array": {"at": where(base), "step": step, "length": length,
                      "next_m_eVarType": after.m_eVarType, "next_at": where(base + length * step)},
                      "types": out, "ConVarData_size": ctypes.sizeof(ConVarData)}))


if __name__ == "__main__":
    try:
        main(sys.argv[1], sys.argv[2:])
    except BaseException:
        import traceback

        traceback.print_exc()
        win32.hard_exit(1)
    win32.hard_exit(0)
