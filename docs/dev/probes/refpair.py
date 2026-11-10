"""Probe (read-only): do a DLL's queue entries' refs hold s2sdk's pre-registration
shape? Convar: m_pConVarData == m_pConVar + 8, the ConVarRef's u16 0xFFFF and
int 0; *m_pConVarData one target per type. Command: the ref's first qword 0xFFFF.

usage: copy into trash/winpy/ (bin/winpy's cwd), then bin/winpy refpair DLL DIR...
"""
import collections, json, sys
from dllscan import reglist, win32, values
from dllscan.convar_h import ConCommandRegList_Entry_t, ConVarRegList_Entry_t, offset_of
from dllscan.image import read_image
from dllscan.memory import Memory
dll, *dirs = sys.argv[1:]
win32.add_dll_directories(dirs)
mem = Memory(win32.read)
image = read_image(mem, win32.load_library(dll))
PC, PD = (offset_of(ConVarRegList_Entry_t, f) for f in ("m_pConVar", "m_pConVarData"))
TY = offset_of(ConVarRegList_Entry_t, "m_Info.m_valueInfo.m_eVarType")
CMD = offset_of(ConCommandRegList_Entry_t, "m_Command")
out = {"dll": dll.rsplit("\\", 1)[-1]}
(q,) = reglist.find_queues(mem, image, "convars")
pads = set(); bad = 0; by_type = collections.defaultdict(set); pcs = set()
for e in q.entries:
    pc, pd = mem.u64(e + PC), mem.u64(e + PD)
    bad += not (pd == pc + 8 and mem.u16(pc) == 0xFFFF and mem.u32(pc + 4) == 0)
    pads.add(mem.u16(pc + 2))
    by_type[values.type_name(mem.u16(e + TY))].add(mem.u64(pd)); pcs.add(pc)
out["convars"] = {"entries": len(q.entries), "violations": bad, "distinct_refs": len(pcs), "pad_values": len(pads),
                  "pd_targets_per_type": {t: len(s) for t, s in by_type.items()},
                  "types_sharing_a_target": len(by_type) - len(set().union(*by_type.values()))}
(q,) = reglist.find_queues(mem, image, "concommands")
cs = [mem.u64(e + CMD) for e in q.entries]
out["concommands"] = {"entries": len(cs), "first_qword_not_0xffff": sum(mem.u64(c) != 0xFFFF for c in cs), "distinct_refs": len(set(cs))}
print(json.dumps(out))
win32.hard_exit(0)
