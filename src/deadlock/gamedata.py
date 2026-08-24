"""Flatten one decompiled KV3 game-data file into git-trackable JSONL leaves.

    python -m deadlock.gamedata < scripts/heroes.vdata

Each scalar becomes one line: ``{"path": ..., "value": ...}`` where ``path`` is
the dotted/indexed location within the file (e.g.
``hero_inferno.m_flStaminaCooldown``). One stat per line means a balance patch
shows up in ``git diff`` as exactly the lines that changed. The source file is
not repeated per record — each output file covers exactly one vdata (see
``data/gamedata.flat/default.jsonl.do``), so the filename carries it.

Output is unsorted; sort the stream (e.g. ``sort``) for a stable, diff-friendly
ordering.
"""

import sys
from collections.abc import Iterator, Mapping

from . import jsonl, kv3
from .flatten import leaves


def records(root: Mapping[str, object]) -> Iterator[dict[str, object]]:
    """One ``{path, value}`` record per leaf scalar in ``root``."""
    for path, value in leaves(jsonl.to_jsonable(root)):
        yield {"path": path, "value": value}


def main() -> None:
    _ = sys.stdout.writelines(jsonl.dump_lines(records(kv3.load(sys.stdin))))


if __name__ == "__main__":
    main()
