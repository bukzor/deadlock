"""Recompile ``levels.tsv`` — the player level / souls / ability curve — from data.

Source: the committed, flattened ``data/gamedata.flat/scripts/heroes.jsonl``. The game stores, per
level 1..36 under each hero's ``m_mapLevelInfo``:

- ``m_unRequiredGold`` — cumulative souls *earned* to reach the level.
- ``m_mapBonusCurrencies`` — ``EAbilityUnlocks`` (an ability slot) or
  ``EAbilityPoints`` (one ability point), exactly one per level.

The table is emitted in the hand-built original's display conventions:

- ``level``   = game level − 1 (indexed from 00).
- ``souls``   = ``m_unRequiredGold`` + 600 (net worth, including the 600 souls a
  match starts with).
- ``delta``   = souls gained since the previous level.
- ``ability`` = cumulative ``EAbilityUnlocks`` (1..4).
- ``AP``      = cumulative ``EAbilityPoints``.

Every hero shares one curve; that invariant is asserted (``canonical``) so a
patch diverging a single hero fails loudly instead of silently mis-representing
the rest.

    python -m deadlock.levels < data/gamedata.flat/scripts/heroes.jsonl
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from . import jsonl

STARTING_SOULS = 600
_PATH = re.compile(r"^(hero_\w+)\.m_mapLevelInfo\.(\d+)\.(.+)$")
_BONUS = {"m_mapBonusCurrencies.EAbilityUnlocks": "unlock", "m_mapBonusCurrencies.EAbilityPoints": "ap"}


@dataclass(frozen=True)
class Level:
    """One row of a hero's ``m_mapLevelInfo``: souls earned and the bonus granted."""

    gold: int
    bonus: str  # "unlock" | "ap"


@dataclass(frozen=True)
class Row:
    """One emitted ``levels.tsv`` row, in display conventions (see module doc)."""

    level: int
    souls: int
    delta: int
    ability: int
    ap: int


def curves(records: Iterable[Mapping[str, object]]) -> dict[str, dict[int, Level]]:
    """Per-hero ``{level: Level}`` maps, parsed from heroes.jsonl leaf records."""
    gold: dict[str, dict[int, int]] = {}
    bonus: dict[str, dict[int, str]] = {}
    for record in records:
        match = _PATH.match(_str(record["path"]))
        if not match:
            continue
        hero, level, field = match.group(1), int(match.group(2)), match.group(3)
        if field == "m_unRequiredGold":
            gold.setdefault(hero, {})[level] = _int(record["value"])
        elif field in _BONUS:
            bonus.setdefault(hero, {})[level] = _BONUS[field]
    return {
        hero: {level: Level(g, bonus[hero][level]) for level, g in sorted(levels.items())}
        for hero, levels in gold.items()
    }


def canonical(curves: Mapping[str, Mapping[int, Level]]) -> Mapping[int, Level]:
    """The single curve shared by every hero; assert uniformity, return ``hero_base``."""
    base = curves["hero_base"]
    for hero, curve in curves.items():
        assert curve == base, hero
    return base


def rows(curve: Mapping[int, Level]) -> list[Row]:
    """Apply the display conventions: +600 souls, renumber from 0, accumulate."""
    result: list[Row] = []
    ability = ap = 0
    previous: int | None = None
    for level in sorted(curve):
        info = curve[level]
        souls = info.gold + STARTING_SOULS
        match info.bonus:
            case "unlock":
                ability += 1
            case "ap":
                ap += 1
            case other:
                raise AssertionError(other)
        delta = 0 if previous is None else souls - previous
        result.append(Row(level - 1, souls, delta, ability, ap))
        previous = souls
    return result


def render(rows: Iterable[Row]) -> str:
    """Render rows as the zero-padded, tab-separated table (with header line)."""
    body = "".join(
        f"{r.level:02d}\t{r.souls:05d}\t{r.delta:04d}\t{r.ability}\t{r.ap:02d}\n" for r in rows
    )
    return "level\tsouls\tdelta\tability\tAP\n" + body


def _str(value: object) -> str:
    assert isinstance(value, str), value
    return value


def _int(value: object) -> int:
    assert isinstance(value, int), value
    return value


def main() -> None:
    records = jsonl.load_lines(sys.stdin)
    _ = sys.stdout.write(render(rows(canonical(curves(records)))))


if __name__ == "__main__":
    main()
