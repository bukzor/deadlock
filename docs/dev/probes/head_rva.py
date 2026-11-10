"""Probe: where do the two queue heads (s_pRoot) sit relative to the DLL's
per-type placeholder ConVarData array (sentinel.py)?

usage: copy into trash/winpy/ (bin/winpy's cwd), then bin/winpy head_rva DLL DIR...
"""
import json, ntpath, sys
from dllscan import reglist, win32
from dllscan.convar_h import ConVarRegList_Entry_t, offset_of
from dllscan.image import read_image
from dllscan.memory import Memory
dll, *dirs = sys.argv[1:]
win32.add_dll_directories(dirs)
mem = Memory(win32.read)
image = read_image(mem, win32.load_library(dll))
base = image.span.start
def sec(a):
    return next((f"{s.name}+{a - s.span.start:#x}" for s in image.sections if a in s.span), "?")
out = {"dll": ntpath.basename(dll)}
heads = {k: q.head for k in reglist.STRIDES for q in reglist.find_queues(mem, image, k)}
if "convars" in heads:
    e = reglist.find_queues(mem, image, "convars")[0].entries[0]
    code = mem.u16(e + offset_of(ConVarRegList_Entry_t, "m_Info.m_valueInfo.m_eVarType"))
    array = mem.u64(mem.u64(e + offset_of(ConVarRegList_Entry_t, "m_pConVarData"))) - 112 * code
    out["array"] = sec(array)
    out.update({k: [sec(h), h - array] for k, h in heads.items()})
else:
    out.update({k: [sec(h)] for k, h in heads.items()})
print(json.dumps(out)); win32.hard_exit(0)
