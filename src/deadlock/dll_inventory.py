"""``dlls.list``: every DLL under the install's ``game/`` dir, membership only.

One path per line, relative to ``game/``, byte-sorted. Nothing that varies
within a patch goes here (no size, no hash): every per-DLL target depends on
this list, so it changes only when a DLL is added, removed or renamed.
"""

from __future__ import annotations

import os
import posixpath
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path

from . import paths


def dlls(game: Path) -> list[str]:
    """Every ``*.dll`` (suffix in any case) under ``game``, relative to it, byte-sorted.

    Symlinked dirs aren't followed. Basenames must be unique, ignoring case as
    Windows does: a basename keys every per-DLL target.
    """
    found = sorted(
        (Path(dirpath) / name).relative_to(game).as_posix()
        for dirpath, _, names in os.walk(game)
        for name in names
        if name.lower().endswith(".dll")
    )
    duplicates = basename_duplicates(found)
    assert not duplicates, duplicates
    return found


def basename_duplicates(relpaths: Iterable[str]) -> Mapping[str, list[str]]:
    """Lowercased basename -> its paths, for each basename seen more than once."""
    by_basename: dict[str, list[str]] = {}
    for relpath in relpaths:
        by_basename.setdefault(posixpath.basename(relpath).lower(), []).append(relpath)
    return {name: found for name, found in by_basename.items() if len(found) > 1}


def main(argv: list[str] | None = None) -> None:
    """Print ``dlls.list``: ``python -m deadlock.dll_inventory``."""
    [] = (sys.argv if argv is None else argv)[1:]
    _ = sys.stdout.write("".join(f"{relpath}\n" for relpath in dlls(paths.game_dir())))


if __name__ == "__main__":
    main()
