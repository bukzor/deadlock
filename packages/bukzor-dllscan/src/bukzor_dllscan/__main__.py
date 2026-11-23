"""The scanner's CLI, one process per (facet, DLL), run from WSL as

    bin/winpy bukzor_dllscan SUBCOMMAND DLL [DIR ...]

`DLL` is the DLL's Windows path; each `DIR` (Windows form, e.g. both bin dirs)
is added to the DLL search path before the load. Each subcommand prints one
document (`facets.dumps`, UTF-8, `\\n` line endings) to stdout:

- `load`: `LoadOk` with the install's modules the load added, or
  `LoadFailed`; a refused load is data (exit 0), not an error. The install is
  the deepest dir holding `DLL` and every `DIR`.
- `convars`: the convar queue, `ConVarsDocument`.
- `concommands`: the command queue, `ConCommandsDocument`.
- `registry`: tier0's registry after the DLL's `Init`, `RegistryDocument`
  (`server` and `client` only: `registry.APP_SYSTEMS`).

Any exception prints its traceback on stderr and exits 1, with no document.
Every exit goes through `win32.hard_exit`: a loaded DLL's teardown can hang.
"""

import argparse
import io
import ntpath
import sys
import traceback
from collections.abc import Sequence

from . import alloclog, facets, registry, win32
from .document import LoadFailed, LoadOk


class _Args(argparse.Namespace):
    subcommand: str = ""
    dll: str = ""
    dirs: list[str] = []


def _parse(argv: Sequence[str]) -> _Args:
    parser = argparse.ArgumentParser(prog="bukzor_dllscan", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    _ = parser.add_argument("subcommand", choices=("load", "convars", "concommands", "registry"))
    _ = parser.add_argument("dll", help="the DLL's Windows path")
    _ = parser.add_argument("dirs", nargs="*", metavar="dir", help="a DLL search dir, Windows form")
    return parser.parse_args(argv, namespace=_Args())


def load(dll: str, dirs: Sequence[str]) -> LoadOk | LoadFailed:
    """The `load` document: what loading `dll` added, or why it was refused."""
    win32.add_dll_directories(dirs)
    before = win32.modules()
    try:
        _ = win32.load_library(dll)
    except win32.Win32Error as error:
        return facets.load_failed(error)
    return facets.load_ok(before, win32.modules(), ntpath.commonpath([ntpath.dirname(dll), *dirs]))


def proc_subcommand(subcommand: str, dll: str, dirs: Sequence[str]) -> object:
    """The document `subcommand` makes of `dll`."""
    match subcommand:
        case "load":
            return load(dll, dirs)
        case "convars":
            mem, image, log = alloclog.load(dll, dirs)
            return facets.convars(mem, image, dll, log)
        case "concommands":
            mem, image, log = alloclog.load(dll, dirs)
            return facets.concommands(mem, image, dll, log)
        case "registry":
            return registry.read_back(dll, dirs)
        case _:
            raise AssertionError(subcommand)


def main() -> None:
    args = _parse(sys.argv[1:])
    assert isinstance(sys.stdout, io.TextIOWrapper), sys.stdout
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    try:
        text = facets.dumps(proc_subcommand(args.subcommand, args.dll, args.dirs))
    except Exception:
        traceback.print_exc()
        win32.hard_exit(1)
    _ = sys.stdout.write(text)
    win32.hard_exit(0)


if __name__ == "__main__":
    main()
