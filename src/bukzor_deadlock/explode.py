"""CLI: explode raw files out of one VPK into a directory, byte for byte.

    python -m bukzor_deadlock.explode <pak01_dir.vpk> <out_dir> [<dir>]

``out_dir`` becomes the pak's directory ``<dir>`` (the whole pak when omitted):
a VPK file ``<dir>/a/b.ext`` lands at ``out_dir/a/b.ext``. No decompiling;
every file's CRC32 is checked against the VPK index as it is written. It
refuses to start when the files would leave less than ``RESERVE`` bytes free
under ``paths.free_space_dir()``.

The ``vpk`` library parses the index, but its per-file reader reopens the data
archive for every file, which over the WSL 9P mount of the install ran ~9x
slower than one open per archive with reads in offset order.
"""

from __future__ import annotations

import shutil
import sys
import zlib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path

from . import paths
from .archive import Entry, read_entries

# archive index meaning "the data follows the index, inside pak01_dir.vpk";
# the vpk library already rebases such entries' offsets onto the dir file
EMBEDDED = 0x7FFF

# bytes that must stay free after a write: on a WSL host, filling the Windows
# drive under the growable virtual disk crashes everything running
RESERVE = 20 * 10**9


def check_room(need: int, free: int) -> None:
    """Refuse a write of ``need`` bytes that would leave less than RESERVE free."""
    assert need + RESERVE <= free, ("need", need, "+ reserve", RESERVE, "> free", free)


@dataclass(frozen=True)
class Member:
    """A VPK entry chosen for output, and its path below the output dir."""

    entry: Entry
    rel: str


def select(entries: Iterable[Entry], under: str) -> list[Member]:
    """The entries below directory ``under`` (``""``: all), in archive read order.

    Asserts at least one matches: a mistyped dir should not build an empty tree.
    """
    prefix = f"{under}/" if under else ""
    members = [
        Member(entry=e, rel=e.path[len(prefix) :])
        for e in entries
        if e.path.startswith(prefix)
    ]
    for m in members:
        assert m.entry.preload_length == 0, (m.entry.path, m.entry.preload_length)
    assert members, ("no VPK entries under", under)
    return sorted(
        members, key=lambda m: (m.entry.archive_index, m.entry.archive_offset)
    )


def archive_file(dir_file: Path, index: int) -> Path:
    """The file holding an entry's bytes: ``pak01_NNN.vpk``, or the dir file."""
    if index == EMBEDDED:
        return dir_file
    else:
        return dir_file.with_name(dir_file.name.replace("_dir.", f"_{index:03d}."))


def write_tree(dir_file: Path, members: Sequence[Member], out: Path) -> None:
    """Write each member's bytes to ``out/<rel>``, opening each archive once.

    Members come in ``select`` order, so each archive's run is contiguous.
    """
    for index, run in groupby(members, key=lambda m: m.entry.archive_index):
        with archive_file(dir_file, index).open("rb") as archive:
            for member in run:
                entry = member.entry
                _ = archive.seek(entry.archive_offset)
                data = archive.read(entry.file_length)
                assert zlib.crc32(data) == entry.crc32, (entry.path, entry.crc32)
                target = out / member.rel
                target.parent.mkdir(parents=True, exist_ok=True)
                _ = target.write_bytes(data)


def main(argv: list[str]) -> None:
    dir_file, out, *rest = argv[1:]
    [under] = rest or [""]
    members = select(read_entries(Path(dir_file)), under)
    need = sum(m.entry.file_length for m in members)
    check_room(need, shutil.disk_usage(paths.free_space_dir()).free)
    write_tree(Path(dir_file), members, Path(out))


if __name__ == "__main__":
    main(sys.argv)
