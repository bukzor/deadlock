"""Probe: find each DLL's convar/concommand queue by its data shape, no code signature.

Windows Python only. After LoadLibrary, each queue head (s_pRoot) is a pointer in a
writable section to a heap block {u32 m_nSize; Entry_t m_Entries[100]; block* m_pPrev}
whose entries start with a name pointer into the DLL's own image. The Entry_t stride is
unknown: try each, and require every entry of every block to fit.
"""

import ctypes
import json
import os
import re
import struct
import sys

from convar_probe import BIN, CITADEL_BIN, QUEUE_SIG, image_range, read_ptr

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.ReadProcessMemory.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t))
k32.GetCurrentProcess.restype = ctypes.c_void_p
PROC = k32.GetCurrentProcess()
NAME = re.compile(rb"[\x21-\x7e]{1,127}\x00")
BLOCK = 100


def peek(addr: int, n: int) -> bytes | None:
    buf = ctypes.create_string_buffer(n)
    got = ctypes.c_size_t()
    if not k32.ReadProcessMemory(PROC, addr, buf, n, ctypes.byref(got)) or got.value != n:
        return None
    return buf.raw


def qword(addr: int) -> int | None:
    b = peek(addr, 8)
    return None if b is None else struct.unpack("<Q", b)[0]


def writable_sections(base: int) -> list[range]:
    nt = base + ctypes.c_uint32.from_address(base + 0x3C).value
    nsec = ctypes.c_uint16.from_address(nt + 6).value
    opt = ctypes.c_uint16.from_address(nt + 0x14).value
    out = []
    for i in range(nsec):
        sh = nt + 0x18 + opt + 40 * i
        vsize, rva = struct.unpack_from("<II", ctypes.string_at(sh + 8, 8))
        chars = ctypes.c_uint32.from_address(sh + 36).value
        if chars & 0x80000000:  # IMAGE_SCN_MEM_WRITE
            out.append(range(base + rva, base + rva + vsize))
    return out


def name_at(addr: int, image: range) -> bytes | None:
    p = qword(addr)
    if p is None or p not in image:
        return None
    m = NAME.match(ctypes.string_at(p, 128))
    return m.group()[:-1] if m else None


def walk(block: int, stride: int, image: range) -> list[bytes] | None:
    """All names in the queue from this block back, or None if any entry misfits."""
    names: list[bytes] = []
    seen = 0
    while block:
        size = peek(block, 4)
        if size is None:
            return None
        (n,) = struct.unpack("<I", size)
        if not 0 < n <= BLOCK or (seen and n != BLOCK):
            return None
        for i in range(n):
            entry = block + 8 + i * stride
            name = name_at(entry, image)
            help_ptr = qword(entry + 8)
            if name is None or help_ptr is None or (help_ptr and name_at(entry + 8, image) is None and help_ptr not in image):
                return None
            names.append(name)
        prev = qword(block + 8 + BLOCK * stride)
        if prev is None:
            return None
        block, seen = prev, seen + 1
    return names


def find_queues(dll: ctypes.WinDLL) -> list[dict[str, object]]:
    image = image_range(dll)
    found = []
    for sec in writable_sections(image.start):
        data = ctypes.string_at(sec.start, len(sec))
        for off in range(0, len(data) - 7, 8):
            (p,) = struct.unpack_from("<Q", data, off)
            if p < 0x10000 or p in image or p % 8:
                continue
            if name_at(p + 8, image) is None:
                continue
            fits = [(s, names) for s in range(16, 1024, 8) if (names := walk(p, s, image))]
            fits = [(s, names) for s, names in fits if len(names) > BLOCK]
            if len(fits) == 1:
                s, names = fits[0]
                found.append({"head_at": hex(sec.start + off), "stride": s, "entries": len(names), "first": [n.decode() for n in names[:3]]})
            elif len(fits) > 1:
                found.append({"head_at": hex(sec.start + off), "ambiguous_strides": [s for s, _ in fits]})
    return found


def signature_head(dll: ctypes.WinDLL) -> str:
    r = image_range(dll)
    m = QUEUE_SIG.search(ctypes.string_at(r.start, len(r)))
    assert m
    (disp,) = struct.unpack("<i", m.group(1))
    return hex(r.start + m.start() + 7 + disp)


def main() -> None:
    os.add_dll_directory(BIN)
    os.add_dll_directory(CITADEL_BIN)
    for path in sys.argv[1:]:
        dll = ctypes.WinDLL(path)
        print(json.dumps({"dll": os.path.basename(path), "signature_convar_head_at": signature_head(dll), "scan": find_queues(dll)}), flush=True)


if __name__ == "__main__":
    main()
