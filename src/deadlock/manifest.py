"""CLI: write a path-sorted VPK manifest as JSONL.

    python -m deadlock.manifest [pak01_dir.vpk] > data/manifest.jsonl

One ``{path, crc32, size}`` object per line. Commit it and regenerate after a
patch; ``git diff`` shows precisely which files changed (one file per line).
"""

import sys
from pathlib import Path

from . import jsonl, paths
from .archive import manifest_records, read_entries


def main(argv: list[str]) -> None:
    vpk_dir_file = Path(argv[1]) if len(argv) > 1 else paths.vpk_dir_file()
    sys.stdout.writelines(jsonl.dump_lines(manifest_records(read_entries(vpk_dir_file))))


if __name__ == "__main__":
    main(sys.argv)
