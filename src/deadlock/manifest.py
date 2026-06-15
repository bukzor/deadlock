"""CLI: write a deterministic VPK manifest to stdout.

    python -m deadlock.manifest [--jsonl] [pak01_dir.vpk] > data/manifest.tsv

The manifest (sorted ``path\tcrc32\tsize`` lines, or ``--jsonl`` records) is the
unit of patch-diffing: diff two versions' manifests to see exactly what changed.
"""

import sys
from pathlib import Path

from . import jsonl, paths
from .archive import manifest, manifest_records, read_entries


def main(argv: list[str]) -> None:
    args = argv[1:]
    as_jsonl = "--jsonl" in args
    rest = [a for a in args if a != "--jsonl"]
    vpk_dir_file = Path(rest[0]) if rest else paths.vpk_dir_file()
    entries = read_entries(vpk_dir_file)
    if as_jsonl:
        sys.stdout.write(jsonl.dump_lines(manifest_records(entries)))
    else:
        sys.stdout.write(manifest(entries))


if __name__ == "__main__":
    main(sys.argv)
