"""CLI: write a deterministic VPK manifest to stdout.

    python -m deadlock.manifest [pak01_dir.vpk] > data/manifest.tsv

The manifest (sorted ``path\tcrc32\tsize`` lines) is the unit of patch-diffing:
diff two versions' manifests to see exactly what changed.
"""

import sys
from pathlib import Path

from . import paths
from .archive import manifest, read_entries


def main(argv: list[str]) -> None:
    vpk_dir_file = Path(argv[1]) if len(argv) > 1 else paths.vpk_dir_file()
    sys.stdout.write(manifest(read_entries(vpk_dir_file)))


if __name__ == "__main__":
    main(sys.argv)
