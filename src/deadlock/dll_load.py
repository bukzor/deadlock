"""The ``load`` facet's WSL side: the DLLs never to load, and the guard that
load-time facets (``concommands``, …) run only on a DLL whose load is ``ok``.

    python -m deadlock.dll_load excluded helpsystem.dll  # its record, or nothing
    python -m deadlock.dll_load ok data/dlls/load/server.dll.json  # or fails

Every other DLL's ``load`` document comes from ``bin/winpy dllscan load``. A
load that *fails* (``LoadLibraryExW: 126``) is data, a ``failed`` document, not
an exclusion. Output is formatted as the scanner's documents are
(``dllscan.facets.dumps``; a test holds the two equal), but not imported from
it: ``facets`` pulls in the whole scanner, which an excluded DLL's atom
never runs and so should not depend on.
"""

import json
import sys
from collections.abc import Mapping
from pathlib import Path

import typed_json

from dllscan.document import LoadExcluded

from .types import is_str_mapping

_HANGS = "LoadLibrary hangs and leaves an unkillable process (build 6851)"

EXCLUDED: Mapping[str, str] = {
    "assetpreview.dll": _HANGS,
    "helpsystem.dll": _HANGS,
    "propertyeditor.dll": _HANGS,
    "toolframework2.dll": _HANGS,
}
"""DLL basename (as in ``data/dlls.list``) → why it is never loaded. A load
also loads the imports, so a DLL importing one of these would hang too; on
6860 the static + delay-import closure of every DLL reaches none of them but
themselves (unit 007). A new hang fails its atom on the timeout: add it here."""


def excluded(basename: str) -> LoadExcluded | None:
    """The ``excluded`` record of ``basename``, or None if it is to be loaded."""
    reason = EXCLUDED.get(basename)
    return None if reason is None else LoadExcluded(outcome="excluded", reason=reason)


def require_ok(document: object) -> None:
    """Assert that a ``load`` document says ``ok``, naming its outcome if not."""
    assert is_str_mapping(document), document
    outcome = document.get("outcome")
    assert outcome == "ok", ("load outcome", outcome)


def main(argv: list[str] | None = None) -> None:
    """``excluded NAME``: print NAME's record if excluded, else nothing.
    ``ok PATH``: fail unless the ``load`` document at PATH says ``ok``."""
    [subcommand, arg] = (sys.argv if argv is None else argv)[1:]
    match subcommand:
        case "excluded":
            doc = excluded(arg)
            if doc is not None:
                _ = sys.stdout.write(json.dumps(doc, indent=2) + "\n")
        case "ok":
            document = typed_json.loads(Path(arg).read_text())
            require_ok(document)
        case _:
            raise AssertionError(subcommand)


if __name__ == "__main__":
    main()
