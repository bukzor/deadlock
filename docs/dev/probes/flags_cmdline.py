"""Probe: do the declared flags depend on the host process's command line?

s2sdk's `SanitiseConVarFlags` (`tier0_perproject/convar.cpp:234`) adds
`developmentonly defensive` to a declaration that carries none of a set of
flags, unless `CommandLine()->HasParm("-tools")`, and runs in each static
initializer. Run this twice, with and without an extra `-tools` argument
(which lands in `GetCommandLineW`), and compare: the sha256 of the convars and
concommands documents and their `developmentonly` counts.

usage: copy into trash/winpy/ (bin/winpy's cwd), then
       bin/winpy flags_cmdline DLL DIR... [-tools]    (arguments starting with - are ignored)
"""

import hashlib
import json
import sys

from dllscan import facets, win32
from dllscan.__main__ import load_image


def main(dll: str, dirs: list[str]) -> None:
    mem, image = load_image(dll, dirs)
    out: dict[str, object] = {"argv_has_tools": "-tools" in sys.argv}
    for name, doc in (("convars", facets.convars(mem, image, dll)), ("concommands", facets.concommands(mem, image, dll))):
        entries = doc[name]
        out[name] = {
            "entries": len(entries),
            "developmentonly": sum("developmentonly" in e["flags"] for e in entries),
            "sha256": hashlib.sha256(facets.dumps(doc).encode()).hexdigest()[:16],
        }
    print(json.dumps(out))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    try:
        main(args[0], args[1:])
    except BaseException:
        import traceback

        traceback.print_exc()
        win32.hard_exit(1)
    win32.hard_exit(0)
