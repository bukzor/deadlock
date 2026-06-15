"""CLI: extract (and decompile) assets from the VPK into a directory.

    python -m deadlock.extract <out_dir> [ext ...]

With no extensions, extracts everything. Each extension (e.g. ``vdata_c``,
``vtex_c``) narrows the set. Compiled ``_c`` resources are decompiled to their
usable form (KV3 text, png, glTF, …), preserving the VPK directory layout.
"""

import sys
from pathlib import Path

from . import paths, s2v


def main(argv: list[str]) -> None:
    out_dir = Path(argv[1])
    extensions = tuple(argv[2:])
    out_dir.mkdir(parents=True, exist_ok=True)
    s2v.run(
        s2v.extract_argv(
            paths.vpk_dir_file(),
            out_dir,
            decompile=True,
            extensions=extensions,
        )
    )


if __name__ == "__main__":
    main(sys.argv)
