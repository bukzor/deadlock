"""Flatten decompiled KV3 game-data into git-trackable JSONL leaf records.

    python -m deadlock.gamedata scripts/heroes.vdata [more.vdata ...]

Each scalar becomes one line: ``{"file": ..., "path": ..., "value": ...}`` where
``path`` is the dotted/indexed location within the file (e.g.
``hero_inferno.m_flStaminaCooldown``). One stat per line means a balance patch
shows up in ``git diff`` as exactly the lines that changed.

Output is unsorted per file; sort the combined stream (e.g. ``sort``) for a
stable, diff-friendly ordering — see ``data/gamedata.jsonl.do``.
"""

import sys
from collections.abc import Iterator, Mapping
from pathlib import Path

from . import jsonl, kv3
from .flatten import leaves


def records(root: Mapping[str, object], source: str) -> Iterator[dict[str, object]]:
    """One ``{file, path, value}`` record per leaf scalar in ``root``."""
    for path, value in leaves(jsonl.to_jsonable(root)):
        yield {"file": source, "path": path, "value": value}


def main(argv: list[str]) -> None:
    for arg in argv[1:]:
        records_for_file = records(kv3.load(Path(arg)), arg)
        sys.stdout.write(jsonl.dump_lines(records_for_file))


if __name__ == "__main__":
    main(sys.argv)
