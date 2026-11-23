"""Read the VPK directory as structured entries, and render a stable manifest.

The container layer is handled by the ``vpk`` library; this module gives it a
typed boundary and a path-sorted ``{path, crc32, size}`` record per file. Commit
the manifest and regenerate it after a patch: ``git diff`` then shows exactly
which files were added, removed, or changed (one file per line).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

import vpk


@dataclass(frozen=True)
class Entry:
    """One file recorded in the VPK directory tree."""

    path: str
    crc32: int
    file_length: int
    preload_length: int
    archive_index: int
    archive_offset: int


def manifest_records(entries: Iterable[Entry]) -> list[dict[str, object]]:
    """Path-sorted, JSONL-ready dicts: ``{path, crc32 (hex), size}``.

    Path-sorted (not key-sorted) so a file's line keeps its position across
    versions and a content change shows as a single in-place ``git diff`` line.

    >>> manifest_records([Entry("b", 1, 9, 0, 0, 0), Entry("a", 255, 0, 0, 0, 0)])
    [{'path': 'a', 'crc32': '000000ff', 'size': 0}, {'path': 'b', 'crc32': '00000001', 'size': 9}]
    """
    return [
        {"path": e.path, "crc32": f"{e.crc32:08x}", "size": e.file_length}
        for e in sorted(entries, key=lambda e: e.path)
    ]


def read_entries(vpk_dir_file: Path) -> Iterator[Entry]:
    """Yield every entry in a ``pak01_dir.vpk`` (impure: opens the archive)."""
    pak = vpk.open(str(vpk_dir_file))
    for path, meta in pak.read_index_iter():
        _preload, crc32, preload_length, archive_index, archive_offset, file_length = meta
        yield Entry(
            path=path,
            crc32=crc32,
            file_length=file_length,
            preload_length=preload_length,
            archive_index=archive_index,
            archive_offset=archive_offset,
        )
