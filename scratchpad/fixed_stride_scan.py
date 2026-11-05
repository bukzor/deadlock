"""Experiment: with strides fixed at the 6848 values, do single-block queues
(small DLLs, tier0) show up unambiguously? One DLL per process."""
import ctypes, json, os, struct, sys
from convar_probe import BIN, CITADEL_BIN, image_range
from convar_scan import walk, writable_sections, name_at, qword

STRIDES = {160: "convar", 64: "command"}

def owner_ok(head, stride, n_total, image, wsecs):
    """Fraction of entries whose last qword points into the DLL's writable sections."""
    ok = tot = 0; block = head
    while block and tot < n_total:
        (n,) = struct.unpack("<I", ctypes.string_at(block, 4))
        for i in range(n):
            q = qword(block + 8 + i * stride + stride - 8)
            ok += any(q in w for w in wsecs) if q else 0; tot += 1
        block = qword(block + 8 + 100 * stride)
    return f"{ok}/{tot}"

def main(path):
    os.add_dll_directory(BIN); os.add_dll_directory(CITADEL_BIN)
    try:
        dll = ctypes.WinDLL(path)
    except OSError as e:
        print(json.dumps(dict(dll=os.path.basename(path), load_error=str(e)))); return
    image = image_range(dll)
    wsecs = writable_sections(image.start); hits = []
    for sec in wsecs:
        data = ctypes.string_at(sec.start, len(sec))
        for off in range(0, len(data) - 7, 8):
            (p,) = struct.unpack_from("<Q", data, off)
            if p < 0x10000 or p in image or p % 8 or name_at(p + 8, image) is None:
                continue
            for s, kind in STRIDES.items():
                if names := walk(p, s, image):
                    hits.append(dict(kind=kind, head=hex(sec.start + off), n=len(names),
                                     owner=owner_ok(p, s, len(names), image, wsecs),
                                     first=[x.decode() for x in names[:3]]))
    print(json.dumps(dict(dll=os.path.basename(path), hits=hits)), flush=True)

name = sys.argv[1]
main(next(d + '\\' + name for d in (BIN, CITADEL_BIN) if os.path.exists(d + '\\' + name)))
