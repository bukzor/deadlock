"""The game DLLs a load pulled in: a load-time atom's dependencies beyond its
own DLL's file.

    python -m deadlock.dll_closure data/dlls/load/server.dll.json <data/dlls.list

A load-time atom (``data/dlls/{load,concommands,convars}``) loads its DLL in a
Windows process, and the load loads the DLL's import closure too, so the
document depends on every DLL in it. An ``ok`` load document's ``modules``
names that closure. This prints the paths of the ones in ``data/dlls.list``,
one per line, for the atom to ``redo-ifchange``. The others (system DLLs) stay
untracked. ``modules`` holds Windows' lowercased names and ``dlls.list`` the
files' case, so a basename matches ignoring case.
"""

import sys
from collections.abc import Iterable
from pathlib import Path, PurePosixPath

import typed_json

from . import paths
from .types import is_sequence, is_str_mapping


def closure(listing: Iterable[str], document: object) -> list[str]:
    """The ``dlls.list`` entries of the modules a ``load`` document's load
    added, in listing order. None for a ``failed`` load: it stopped before
    reporting what it added."""
    assert is_str_mapping(document), document
    match document.get("outcome"):
        case "ok":
            modules = document["modules"]
            assert is_sequence(modules), modules
            assert all(isinstance(m, str) for m in modules), modules
            names = {str(m).lower() for m in modules}
        case "failed":
            return []
        case outcome:
            raise AssertionError("load outcome", outcome)
    entries = (line.rstrip("\n") for line in listing)
    return [entry for entry in entries if PurePosixPath(entry).name.lower() in names]


def main(argv: list[str] | None = None) -> None:
    """Print the closure's DLL paths under ``game/``, reading ``dlls.list`` on
    stdin, for the ``load`` document at the one argument."""
    [load] = (sys.argv if argv is None else argv)[1:]
    document = typed_json.loads(Path(load).read_text())
    game = paths.game_dir()
    _ = sys.stdout.write("".join(f"{game / e}\n" for e in closure(sys.stdin, document)))


if __name__ == "__main__":
    main()
