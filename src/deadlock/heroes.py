"""Recompile ``heroes.tsv`` — the per-hero base stat sheet — from data.

Source: the committed, flattened ``data/gamedata.jsonl``. Each hero in
``scripts/heroes.vdata`` stores its full ``m_mapStartingStats`` (the compiled
data materializes every stat per hero, not just overrides of ``hero_base``).

The output is the wide complement to ``data/gamedata.jsonl``: one row per hero,
one column per stat (``EMaxHealth``, ``EMaxMoveSpeed``, melee, stamina, …), so
heroes read side-by-side. The fine grain (one stat = one line) already lives in
``gamedata.jsonl``; this view exists for human comparison. ``hero_base`` is the
reference row, so a column blank for a hero means a *hero-unique* stat the base
doesn't define.

Every hero must define all of ``hero_base``'s stats; that invariant is asserted
so a patch dropping a stat from one hero fails loudly.

    python -m deadlock.heroes data/gamedata.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path

HEROES_FILE = "scripts/heroes.vdata"
_PATH = re.compile(r"^(hero_\w+)\.m_mapStartingStats\.(\w+)$")


def stats(records: Iterable[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    """Per-hero ``{stat: value}`` maps, parsed from gamedata.jsonl leaf records."""
    result: dict[str, dict[str, object]] = {}
    for record in records:
        if record["file"] != HEROES_FILE:
            continue
        match = _PATH.match(_str(record["path"]))
        if not match:
            continue
        result.setdefault(match.group(1), {})[match.group(2)] = record["value"]
    return result


def columns(stats: Mapping[str, Mapping[str, object]]) -> list[str]:
    """The sorted union of every stat; assert each hero defines all base stats."""
    base = set(stats["hero_base"])
    for hero, hero_stats in stats.items():
        assert base <= set(hero_stats), (hero, base - set(hero_stats))
    return sorted({stat for hero_stats in stats.values() for stat in hero_stats})


def render(stats: Mapping[str, Mapping[str, object]]) -> str:
    """Render the wide stat sheet: header, then one tab-separated row per hero."""
    cols = columns(stats)
    lines = ["hero\t" + "\t".join(cols)]
    for hero in sorted(stats):
        cells = [_cell(stats[hero].get(col)) for col in cols]
        lines.append(hero + "\t" + "\t".join(cells))
    return "".join(line + "\n" for line in lines)


def _cell(value: object) -> str:
    return "" if value is None else str(value)


def _str(value: object) -> str:
    assert isinstance(value, str), value
    return value


def main(argv: list[str]) -> None:
    [source] = argv[1:]
    records = (json.loads(line) for line in Path(source).read_text().splitlines())
    sys.stdout.write(render(stats(records)))


if __name__ == "__main__":
    main(sys.argv)
