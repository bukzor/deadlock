"""Find a DLL's path from its basename, via ``data/dlls.list``.

``dlls.list`` holds one path per line, relative to ``game/``, and its basenames
are unique, so a basename (``server.dll``) names a DLL everywhere below it. Every
``data/dlls/<facet>/default.json.do`` atom turns its ``$2`` into the DLL's path
with this CLI, which also guards the atom: a name not in the list fails.

    dll=$("$py" -m deadlock.dlls_list server.dll <"$root/data/dlls.list")
"""

import sys
from collections.abc import Iterable
from pathlib import PurePosixPath

from . import paths


def relpath(listing: Iterable[str], basename: str) -> str:
    """The ``dlls.list`` entry whose basename is ``basename``.

    >>> relpath(["bin/win64/tier0.dll\\n"], "tier0.dll")
    'bin/win64/tier0.dll'
    """
    entries = (line.rstrip("\n") for line in listing)
    matches = [entry for entry in entries if PurePosixPath(entry).name == basename]
    assert len(matches) == 1, (basename, "not exactly once in dlls.list", matches)
    return matches[0]


def main(argv: list[str] | None = None) -> None:
    """Print the DLL's path under ``game/``, reading ``dlls.list`` on stdin."""
    [basename] = (sys.argv if argv is None else argv)[1:]
    _ = sys.stdout.write(f"{paths.game_dir() / relpath(sys.stdin, basename)}\n")


if __name__ == "__main__":
    main()
