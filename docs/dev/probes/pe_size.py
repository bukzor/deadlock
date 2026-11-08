"""Measure how big a 'lossless' static PE dump of each DLL would be, two ways."""
import hashlib, json, sys, time
from pathlib import Path
import pefile

def fix(o):
    if isinstance(o, dict): return {(k.decode("latin1") if isinstance(k, bytes) else k): fix(v) for k, v in o.items()}
    if isinstance(o, list): return [fix(v) for v in o]
    return o

def structured(pe: pefile.PE, data: bytes) -> dict:
    """Everything pefile parses that names something, minus relocations' per-entry list."""
    d = pe.dump_dict()
    for k in ("Base relocations",):  # per-fixup lists: big, pure linker noise
        d.pop(k, None)
    return d

game = Path(sys.argv[1])
rows = []
for p in sorted(game.rglob("*.dll")):
    data = p.read_bytes()
    t = time.perf_counter()
    pe = pefile.PE(data=data, fast_load=False)
    full = json.dumps(fix(pe.dump_dict()), default=str)
    slim = json.dumps(fix(structured(pe, data)), default=str)
    dt = time.perf_counter() - t
    imports = sorted({e.dll.decode().lower() for e in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])})
    nexp = len(getattr(getattr(pe, "DIRECTORY_ENTRY_EXPORT", None), "symbols", []) or [])
    rows.append((p.relative_to(game).as_posix(), len(data), len(full), len(slim), nexp, "tier0.dll" in imports, dt))
tot = [sum(r[i] for r in rows) for i in (1, 2, 3)]
print(f"dlls={len(rows)} bytes={tot[0]:,} full_json={tot[1]:,} no_reloc_json={tot[2]:,} secs={sum(r[6] for r in rows):.1f}")
print("tier0 importers:", sum(r[5] for r in rows))
names = [r[0].rsplit('/', 1)[1].lower() for r in rows]
print("dup basenames:", sorted({n for n in names if names.count(n) > 1}))
for r in sorted(rows, key=lambda r: -r[2])[:8]:
    print(f"{r[0]:55} dll={r[1]:>11,} full={r[2]:>10,} noreloc={r[3]:>9,} exports={r[4]}")
