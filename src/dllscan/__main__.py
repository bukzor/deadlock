"""The scanner's CLI, one process per (facet, DLL), run from WSL as

    bin/winpy dllscan SUBCOMMAND DLL [DIR ...]

`DLL` is the DLL's Windows path; each `DIR` (Windows form, e.g. both bin dirs)
is added to the DLL search path before the load. Each subcommand prints one
document (`facets.dumps`, UTF-8, `\\n` line endings) to stdout:

- `load`: `LoadOk` with the modules the load added, or `LoadFailed`; a refused
  load is data (exit 0), not an error.
- `concommands`: the command queue, `ConCommandsDocument`.
- `strides`: the multi-block queues' strides re-learned and labelled; an error
  if they moved from `reglist.STRIDES`.

Any exception prints its traceback on stderr and exits 1, with no document.
Every exit goes through `win32.hard_exit`: a loaded DLL's teardown can hang.
"""

import argparse
import io
import sys
import traceback
from collections.abc import Sequence

from . import facets, win32
from .document import LoadFailed, LoadOk
from .image import Image, read_image
from .memory import Memory


class _Args(argparse.Namespace):
    subcommand: str = ""
    dll: str = ""
    dirs: list[str] = []


def _parse(argv: Sequence[str]) -> _Args:
    parser = argparse.ArgumentParser(prog="dllscan", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    _ = parser.add_argument("subcommand", choices=("load", "concommands", "strides"))
    _ = parser.add_argument("dll", help="the DLL's Windows path")
    _ = parser.add_argument("dirs", nargs="*", metavar="dir", help="a DLL search dir, Windows form")
    return parser.parse_args(argv, namespace=_Args())


def load(dll: str, dirs: Sequence[str]) -> LoadOk | LoadFailed:
    """The `load` document: what loading `dll` added, or why it was refused."""
    win32.add_dll_directories(dirs)
    before = win32.module_names()
    try:
        _ = win32.load_library(dll)
    except win32.Win32Error as error:
        return facets.load_failed(error)
    return facets.load_ok(before, win32.module_names())


def load_image(dll: str, dirs: Sequence[str]) -> tuple[Memory, Image]:
    """Load `dll` into this process; its memory and layout."""
    win32.add_dll_directories(dirs)
    mem = Memory(win32.read)
    return mem, read_image(mem, win32.load_library(dll))


def proc_subcommand(subcommand: str, dll: str, dirs: Sequence[str]) -> object:
    """The document `subcommand` makes of `dll`."""
    match subcommand:
        case "load":
            return load(dll, dirs)
        case "concommands":
            return facets.concommands(*load_image(dll, dirs), dll)
        case "strides":
            return facets.strides(*load_image(dll, dirs))
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
