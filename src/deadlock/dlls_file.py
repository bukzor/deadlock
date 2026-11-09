"""Compile ``data/dlls/file.tsv``, the ``file`` facet's aggregate, from its documents.

    python -m deadlock.dlls_file data/dlls/file/<dll>.json ... > data/dlls/file.tsv

One row per DLL, sorted by basename: ``dll`` (the basename in
``data/dlls.list``), ``size`` in bytes, ``sha256`` in lowercase hex. Cells as
``deadlock.dlls_tsv``.
"""

import sys
from collections.abc import Mapping
from typing import TypeGuard

from dllscan.document import FileDocument

from . import dlls_tsv
from .sparse import Table, render
from .types import is_str_mapping


def is_file_document(value: object) -> TypeGuard[FileDocument]:
    return (
        is_str_mapping(value)
        and set(value) == {"size", "sha256"}
        and type(value["size"]) is int
        and isinstance(value["sha256"], str)
    )


def table(documents: Mapping[str, FileDocument]) -> Table:
    rows = [[dll, str(d["size"]), dlls_tsv.cell(d["sha256"])] for dll, d in sorted(documents.items())]
    return ["dll", "size", "sha256"], rows


def main() -> None:
    _ = sys.stdout.write(render(table(dlls_tsv.load_documents(sys.argv[1:], is_file_document))))


if __name__ == "__main__":
    main()
