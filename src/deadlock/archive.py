"""Read the VPK directory as structured entries, and render it deterministically.

The container layer is handled by the ``vpk`` library; this module gives it a
typed boundary and a stable text manifest. The manifest is the basis for
patch-diffing: sorted ``path\tcrc32\tsize`` lines mean a plain ``diff`` of two
patches' manifests shows exactly which files were added, removed, or changed.
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


def manifest(entries: Iterable[Entry]) -> str:
    """Render entries as a deterministic, path-sorted manifest.

    >>> manifest([Entry("b", 1, 9, 0, 0, 0), Entry("a", 255, 0, 0, 0, 0)])
    'a\\t000000ff\\t0\\nb\\t00000001\\t9\\n'
    """
    lines = sorted(f"{e.path}\t{e.crc32:08x}\t{e.file_length}" for e in entries)
    return "".join(line + "\n" for line in lines)


def manifest_records(entries: Iterable[Entry]) -> list[dict[str, object]]:
    """Path-sorted, JSONL-ready dicts: ``{path, crc32 (hex), size}``."""
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
