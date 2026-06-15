"""CLI: extract (and decompile) assets from the VPK into a directory.

    python -m deadlock.extract [--gltf] <out_dir> [ext ...]

With no extensions, extracts everything. Each extension (e.g. ``vdata_c``,
``vtex_c``, ``vmdl_c``) narrows the set. Compiled ``_c`` resources are decompiled
to their usable form (KV3 text, png, wav/mp3, …), preserving the VPK layout.
``--gltf`` exports models as ``.glb`` for viewing.
"""

import sys
from pathlib import Path

from . import paths, s2v


def main(argv: list[str]) -> None:
    args = argv[1:]
    gltf = "--gltf" in args
    rest = [a for a in args if a != "--gltf"]
    out_dir = Path(rest[0])
    extensions = tuple(rest[1:])
    out_dir.mkdir(parents=True, exist_ok=True)
    s2v.run(
        s2v.extract_argv(
            paths.vpk_dir_file(),
            out_dir,
            decompile=True,
            extensions=extensions,
            gltf=gltf,
        )
    )


if __name__ == "__main__":
    main(sys.argv)
