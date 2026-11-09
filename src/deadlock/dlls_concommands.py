"""Compile ``data/dlls/concommands.tsv``, the ``concommands`` facet's aggregate.

    python -m deadlock.dlls_concommands data/dlls/concommands/<dll>.json ... > data/dlls/concommands.tsv

One row per command declaration, duplicates kept: ``module`` (the document's
own), ``name``, ``flags`` (space-separated names), ``help`` (``\\N`` for a null
help pointer, an empty cell for ``""``). Cells as ``deadlock.dlls_tsv``.

Rows are sorted by module, then kept in queue order, so a row's ordinal among
its module's rows is its queue index (``docs/dev/cvar-dump.kb/output-views.md``):
one declaration added early in a DLL is one added row, not a renumbering.
"""

import sys
from collections.abc import Mapping
from typing import TypeGuard

from dllscan.document import ConCommand, ConCommandsDocument

from . import dlls_tsv
from .sparse import Table, render
from .types import is_sequence, is_str_mapping


def _is_concommand(value: object) -> TypeGuard[ConCommand]:
    return (
        is_str_mapping(value)
        and set(value) == {"name", "help", "flags"}
        and isinstance(value["name"], str)
        and (value["help"] is None or isinstance(value["help"], str))
        and dlls_tsv.is_str_sequence(value["flags"])
    )


def is_concommands_document(value: object) -> TypeGuard[ConCommandsDocument]:
    return (
        is_str_mapping(value)
        and set(value) == {"module", "concommands"}
        and isinstance(value["module"], str)
        and is_sequence(commands := value["concommands"])
        and all(_is_concommand(c) for c in commands)
    )


def table(documents: Mapping[str, ConCommandsDocument]) -> Table:
    """``documents`` keyed by the basename in ``data/dlls.list``, which is each
    one's ``module``."""
    for dll, d in documents.items():
        assert d["module"] == dll, (dll, d["module"])
    rows = [
        [d["module"], dlls_tsv.cell(c["name"]), dlls_tsv.list_cell(c["flags"]), dlls_tsv.cell(c["help"])]
        for d in sorted(documents.values(), key=lambda d: d["module"])
        for c in d["concommands"]
    ]
    return ["module", "name", "flags", "help"], rows


def main() -> None:
    _ = sys.stdout.write(render(table(dlls_tsv.load_documents(sys.argv[1:], is_concommands_document))))


if __name__ == "__main__":
    main()
