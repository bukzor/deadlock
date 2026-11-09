"""Compile ``data/dlls/load.tsv``, the ``load`` facet's aggregate, from its documents.

    python -m deadlock.dlls_load data/dlls/load/<dll>.json ... > data/dlls/load.tsv
    python -m deadlock.dlls_load --ok data/dlls/load/<dll>.json ...  # the DLLs that loaded

One row per DLL, sorted by basename: ``dll``, ``outcome`` (``ok``, ``failed``
or ``excluded``), then ``detail``, whose meaning the outcome sets: the modules
the load added (space-separated, sorted), the error, or the exclusion reason.
One row per DLL, not per module, so the table reads as one line per DLL; a
module added to one DLL's load changes that one line by one word
(``git diff --word-diff``). Cells as ``deadlock.dlls_tsv``.

``--ok`` prints the basenames whose load is ``ok``, one per line, sorted: the
DLLs a load-time facet covers (``data/dlls/default.tsv.do``).
"""

import sys
from collections.abc import Mapping
from typing import TypeGuard, assert_never

from dllscan.document import LoadDocument

from . import dlls_tsv
from .sparse import Table, render
from .types import is_str_mapping


def is_load_document(value: object) -> TypeGuard[LoadDocument]:
    if not is_str_mapping(value):
        return False
    match value.get("outcome"):
        case "ok":
            return set(value) == {"outcome", "modules"} and dlls_tsv.is_str_sequence(value["modules"])
        case "failed":
            return set(value) == {"outcome", "error"} and isinstance(value["error"], str)
        case "excluded":
            return set(value) == {"outcome", "reason"} and isinstance(value["reason"], str)
        case _:
            return False


def _detail(document: LoadDocument) -> str:
    if document["outcome"] == "ok":
        return dlls_tsv.list_cell(document["modules"])
    elif document["outcome"] == "failed":
        return dlls_tsv.cell(document["error"])
    elif document["outcome"] == "excluded":
        return dlls_tsv.cell(document["reason"])
    else:
        assert_never(document)


def table(documents: Mapping[str, LoadDocument]) -> Table:
    rows = [[dll, d["outcome"], _detail(d)] for dll, d in sorted(documents.items())]
    return ["dll", "outcome", "detail"], rows


def ok(documents: Mapping[str, LoadDocument]) -> list[str]:
    return sorted(dll for dll, d in documents.items() if d["outcome"] == "ok")


def main() -> None:
    match sys.argv[1:]:
        case ["--ok", *paths]:
            _ = sys.stdout.write("".join(f"{dll}\n" for dll in ok(dlls_tsv.load_documents(paths, is_load_document))))
        case paths:
            _ = sys.stdout.write(render(table(dlls_tsv.load_documents(paths, is_load_document))))


if __name__ == "__main__":
    main()
