"""Recompile ``levels.tsv`` — the player level / souls / ability curve — from data.

Source: ``data/gamedata.json/scripts/heroes.json``. The game stores, per
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

    python -m deadlock.levels < data/gamedata.json/scripts/heroes.json
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from . import gamedata
from .types import dig, is_str_mapping

STARTING_SOULS = 600
_BONUS = {"EAbilityUnlocks": "unlock", "EAbilityPoints": "ap"}


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


def curves(heroes: Mapping[str, object]) -> dict[str, dict[int, Level]]:
    """Per-hero ``{level: Level}`` maps, from the ``heroes.vdata`` tree (see ``deadlock.gamedata``)."""
    result: dict[str, dict[int, Level]] = {}
    for hero, entity in heroes.items():
        levels = dig(entity, "m_mapLevelInfo")
        if levels is None:
            continue
        assert is_str_mapping(levels), hero
        result[hero] = {int(level): _level(hero, info) for level, info in sorted(levels.items(), key=_by_level)}
    return result


def _by_level(item: tuple[str, object]) -> int:
    return int(item[0])


def _level(hero: str, info: object) -> Level:
    currencies = dig(info, "m_mapBonusCurrencies")
    assert is_str_mapping(currencies), hero
    assert len(currencies) == 1, (hero, sorted(currencies))  # exactly one bonus per level
    [currency] = currencies
    return Level(_int(dig(info, "m_unRequiredGold")), _BONUS[currency])


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


def _int(value: object) -> int:
    assert isinstance(value, int), value
    return value


def main() -> None:
    heroes = gamedata.load(sys.stdin)
    _ = sys.stdout.write(render(rows(canonical(curves(heroes)))))


if __name__ == "__main__":
    main()
