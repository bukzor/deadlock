"""The store's checks that no atom owns (``docs/dev/convar-dump.kb/validation.md``),
run by ``data/dlls.check/*.do``. Each fails with an ``AssertionError`` naming
what is wrong, which fails the build.

    python -m deadlock.dlls_check strides STRIDES.json         # no output
    python -m deadlock.dlls_check concommands concommands.tsv  # the anchor rows
    python -m deadlock.dlls_check convars convars.tsv          # the anchor rows

- ``strides``: ``server.dll``'s ``dllscan strides`` output labels each pinned
  kind on exactly one queue. ``dllscan`` already fails if the strides moved or
  an anchor sits in the other kind's queue; this adds that the anchors are
  there at all, since they decide which stride is which.
- ``concommands``, ``convars``: each anchor of that kind is in its DLL's
  queue, every copy with the flags it must have, and each of ``QUEUE_DLLS``
  has a queue of that kind.
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

CONVAR_ANCHORS: Mapping[tuple[str, str], frozenset[str]] = {
    ("server.dll", "citadel_lane_swap_available_duration_prematch"): frozenset({"replicated", "cheat"}),
}
"""The same for convars (``validation.md``)."""

QUEUE_DLLS = ("client.dll", "engine2.dll", "server.dll")
"""The DLLs that must each yield a queue of each kind (``validation.md``, Coverage)."""

_HEADERS = {
    "concommands": ["module", "name", "flags", "help"],
    "convars": ["module", "name", "type", "version", "default", "min", "max", "flags", "help"],
}


def check_strides(learned: object) -> None:
    """``learned`` (``dllscan strides`` output) labels each ``STRIDES`` kind once."""
    assert is_sequence(learned), learned
    kinds: list[object] = []
    for queue in learned:
        assert is_str_mapping(queue), queue
        kinds.append(queue["kind"])
    assert sorted(map(str, kinds)) == sorted(STRIDES), ("each kind's anchors label one queue", kinds, STRIDES)


def check_concommands(table: Table) -> Table:
    """The anchor rows of ``concommands.tsv``, in its order, as ``module name
    flags``; asserts the anchors and the coverage."""
    return _check_queue(table, _HEADERS["concommands"], COMMAND_ANCHORS)


def check_convars(table: Table) -> Table:
    """``check_concommands`` for ``convars.tsv`` and ``CONVAR_ANCHORS``."""
    return _check_queue(table, _HEADERS["convars"], CONVAR_ANCHORS)


def _check_queue(table: Table, expected: list[str], anchors: Mapping[tuple[str, str], frozenset[str]]) -> Table:
    header, rows = table
    assert header == expected, header
    modules = {row[0] for row in rows}
    assert modules >= set(QUEUE_DLLS), ("no queue", sorted(set(QUEUE_DLLS) - modules))
    flags = header.index("flags")
    found = [[row[0], row[1], row[flags]] for row in rows if (row[0], row[1]) in anchors]
    assert {(row[0], row[1]) for row in found} == set(anchors), ("anchors missing", found)
    for module, name, names in found:
        required = anchors[module, name]
        assert required <= set(unlist_cell(names)), (module, name, "lacks", sorted(required), names)
    return ["module", "name", "flags"], found


def main() -> None:
    match sys.argv[1:]:
        case ["strides", path]:
            check_strides(typed_json.loads(Path(path).read_text()))
        case ["concommands", path]:
            _ = sys.stdout.write(render(check_concommands(parse(Path(path).read_text()))))
        case ["convars", path]:
            _ = sys.stdout.write(render(check_convars(parse(Path(path).read_text()))))
        case argv:
            raise AssertionError("usage: dlls_check {strides|concommands|convars} PATH", argv)


if __name__ == "__main__":
    main()
