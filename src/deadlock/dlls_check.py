"""The store's checks that no atom owns (``docs/dev/convar-dump.kb/validation.md``),
run by ``data/dlls.check/*.do``. Each fails with an ``AssertionError`` naming
what is wrong, which fails the build.

    python -m deadlock.dlls_check strides STRIDES.json         # no output
    python -m deadlock.dlls_check concommands concommands.tsv  # the anchor rows

- ``strides``: ``server.dll``'s ``dllscan strides`` output labels each pinned
  kind on exactly one queue. ``dllscan`` already fails if the strides moved or
  an anchor sits in the other kind's queue; this adds that the anchors are
  there at all, since they decide which stride is which.
- ``concommands``: each command anchor is in its DLL's queue, every copy with
  the flags it must have, and each of ``QUEUE_DLLS`` has a command queue.
"""

import sys
from collections.abc import Mapping
from pathlib import Path

import typed_json

from dllscan.reglist import STRIDES

from .dlls_tsv import unlist_cell
from .sparse import Table, parse, render
from .types import is_sequence, is_str_mapping

COMMAND_ANCHORS: Mapping[tuple[str, str], frozenset[str]] = {
    ("server.dll", "bot_kick_all"): frozenset(),
    ("server.dll", "citadel_bot_kick"): frozenset({"developmentonly"}),
    ("tier0.dll", "find"): frozenset(),
}
"""(module, name) → the flags every copy must have. Anchors and flags as
``validation.md`` states them; ``bot_kick_all`` has no stated flags."""

QUEUE_DLLS = ("client.dll", "engine2.dll", "server.dll")
"""The DLLs that must each yield a command queue (``validation.md``, Coverage)."""

_HEADER = ["module", "name", "flags", "help"]


def check_strides(learned: object) -> None:
    """``learned`` (``dllscan strides`` output) labels each ``STRIDES`` kind once."""
    assert is_sequence(learned), learned
    kinds: list[object] = []
    for queue in learned:
        assert is_str_mapping(queue), queue
        kinds.append(queue["kind"])
    assert sorted(map(str, kinds)) == sorted(STRIDES), ("each kind's anchors label one queue", kinds, STRIDES)


def check_concommands(table: Table) -> Table:
    """The anchor rows of ``concommands.tsv``, in its order, help dropped;
    asserts the anchors and the coverage."""
    header, rows = table
    assert header == _HEADER, header
    modules = {row[0] for row in rows}
    assert modules >= set(QUEUE_DLLS), ("no command queue", sorted(set(QUEUE_DLLS) - modules))
    anchors = [row[:3] for row in rows if (row[0], row[1]) in COMMAND_ANCHORS]
    assert {(row[0], row[1]) for row in anchors} == set(COMMAND_ANCHORS), ("anchors missing", anchors)
    for module, name, flags in anchors:
        required = COMMAND_ANCHORS[module, name]
        assert required <= set(unlist_cell(flags)), (module, name, "lacks", sorted(required), flags)
    return _HEADER[:3], anchors


def main() -> None:
    match sys.argv[1:]:
        case ["strides", path]:
            check_strides(typed_json.loads(Path(path).read_text()))
        case ["concommands", path]:
            _ = sys.stdout.write(render(check_concommands(parse(Path(path).read_text()))))
        case argv:
            raise AssertionError("usage: dlls_check {strides|concommands} PATH", argv)


if __name__ == "__main__":
    main()
