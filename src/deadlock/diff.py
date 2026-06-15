"""Diff two VPK manifests to see exactly what a patch changed.

    python -m deadlock.diff data/old.tsv data/new.tsv

Operates on the manifests produced by ``deadlock.manifest`` (sorted
``path\tcrc32\tsize`` lines). All logic is pure; only ``main`` does I/O.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# path -> (crc32 hex, size)
ManifestMap = Mapping[str, tuple[str, int]]


@dataclass(frozen=True)
class ManifestDiff:
    added: list[str]
    removed: list[str]
    changed: list[str]


def parse_manifest(text: str) -> dict[str, tuple[str, int]]:
    """Parse manifest text into ``{path: (crc32, size)}``.

    >>> parse_manifest("a\\t0000000a\\t42\\n")
    {'a': ('0000000a', 42)}
    """
    result: dict[str, tuple[str, int]] = {}
    for line in text.splitlines():
        if not line:
            continue
        path, crc, size = line.split("\t")
        result[path] = (crc, int(size))
    return result


def diff_manifests(old: ManifestMap, new: ManifestMap) -> ManifestDiff:
    """Compare two manifest maps: added/removed paths, and crc-changed paths."""
    old_paths, new_paths = set(old), set(new)
    changed = [p for p in old_paths & new_paths if old[p][0] != new[p][0]]
    return ManifestDiff(
        added=sorted(new_paths - old_paths),
        removed=sorted(old_paths - new_paths),
        changed=sorted(changed),
    )


def format_diff(result: ManifestDiff) -> str:
    """Render a diff as ``+/-/~`` prefixed, path-sorted lines."""
    lines = (
        [f"+ {p}" for p in result.added]
        + [f"- {p}" for p in result.removed]
        + [f"~ {p}" for p in result.changed]
    )
    return "".join(line + "\n" for line in sorted(lines, key=lambda s: s[2:]))


def main(argv: list[str]) -> None:
    old = parse_manifest(Path(argv[1]).read_text())
    new = parse_manifest(Path(argv[2]).read_text())
    sys.stdout.write(format_diff(diff_manifests(old, new)))


if __name__ == "__main__":
    main(sys.argv)
