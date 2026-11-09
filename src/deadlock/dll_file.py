"""The ``file`` facet: one DLL's bytes on disk, as size and sha256.

    python -m deadlock.dll_file /path/to/game/citadel/bin/win64/server.dll

The output is formatted as the scanner's documents are (``dllscan.facets.dumps``;
a test holds the two equal), so every facet diffs alike. That function is not
imported here: ``facets`` pulls in the whole scanner, and this facet's atoms
would then re-run on every scanner change.
"""

import hashlib
import json
import sys
from pathlib import Path

from dllscan.document import FileDocument


def document(data: bytes) -> FileDocument:
    """The ``file`` document of a DLL whose bytes are ``data``."""
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main(argv: list[str] | None = None) -> None:
    """Print the ``file`` document of the DLL at the given path."""
    [dll] = (sys.argv if argv is None else argv)[1:]
    doc = document(Path(dll).read_bytes())
    _ = sys.stdout.write(json.dumps(doc, indent=2) + "\n")


if __name__ == "__main__":
    main()
