"""Recompile ``heroes.tsv`` — the per-hero base stat sheet — from data.

Source: ``data/gamedata.json/scripts/heroes.json``.
Each hero stores its full ``m_mapStartingStats`` (the compiled
data materializes every stat per hero, not just overrides of ``hero_base``).

One row per hero, one column per stat (``EMaxHealth``, ``EMaxMoveSpeed``,
melee, stamina, …), so heroes read side-by-side. ``hero_base`` is the
reference row, so a column blank for a hero means a *hero-unique* stat the base
doesn't define.

Leading the stats are identity and release-status columns (``ATTRS``), plus the
English ``name``: the codenames the data uses ("familiar", "boho") are opaque,
and most rows are unreleased heroes whose stats churn for reasons a balance
patch never explains. Their flags flipping is itself the interesting diff.

Every hero must define all of ``hero_base``'s stats; that invariant is asserted
so a patch dropping a stat from one hero fails loudly.

    python -m deadlock.heroes <loc-file> < data/gamedata.json/scripts/heroes.json
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path

from . import gamedata, loc
from .types import dig, is_str_mapping


# Which scalar hero fields to surface, and under what column name. Everything
# else on the hero (models, particles, sounds, UI art) is noise in a stat sheet.
ATTRS: Mapping[str, str] = {
    "m_HeroID": "id",
    "m_bDisabled": "disabled",
    "m_bInDevelopment": "in_development",
    "m_bPlayerSelectable": "player_selectable",
    "m_bLimitedTesting": "limited_testing",
    "m_bNeedsTesting": "needs_testing",
    "m_bPrereleaseOnly": "prerelease_only",
    "m_bAssignedPlayersOnly": "assigned_players_only",
    "m_nComplexity": "complexity",
}


def stats(heroes: Mapping[str, object]) -> dict[str, dict[str, object]]:
    """Per-hero ``{stat: value}`` maps, from the ``heroes.vdata`` tree (see ``deadlock.gamedata``)."""
    result: dict[str, dict[str, object]] = {}
    for hero, entity in heroes.items():
        starting = dig(entity, "m_mapStartingStats")
        if is_str_mapping(starting):
            result[hero] = dict(starting)
    return result


def attrs(heroes: Mapping[str, object]) -> dict[str, dict[str, object]]:
    """Per-hero ``{column: value}`` maps for the ``ATTRS`` fields, if present."""
    result: dict[str, dict[str, object]] = {}
    for hero, entity in heroes.items():
        present = {column: dig(entity, field) for field, column in ATTRS.items() if dig(entity, field) is not None}
        if present:
            result[hero] = present
    return result


def columns(stats: Mapping[str, Mapping[str, object]]) -> list[str]:
    """The sorted union of every stat; assert each hero defines all base stats."""
    base = set(stats["hero_base"])
    for hero, hero_stats in stats.items():
        assert base <= set(hero_stats), (hero, base - set(hero_stats))
    return sorted({stat for hero_stats in stats.values() for stat in hero_stats})


def render(
    stats: Mapping[str, Mapping[str, object]],
    attrs: Mapping[str, Mapping[str, object]],
    names: Mapping[str, str],
) -> str:
    """Render the wide sheet: header, then one tab-separated row per hero."""
    heads, cols = list(ATTRS.values()), columns(stats)
    lines = ["hero\tname\t" + "\t".join(heads + cols)]
    for hero in sorted(stats):
        cells = [_cell(loc.look_up(names, hero))]
        cells += [_cell(attrs.get(hero, {}).get(head)) for head in heads]
        cells += [_cell(stats[hero].get(col)) for col in cols]
        lines.append(hero + "\t" + "\t".join(cells))
    return "".join(line + "\n" for line in lines)


def _cell(value: object) -> str:
    """Blank for absent; lowercase for booleans, matching the KV3 source."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def main(argv: list[str]) -> None:
    [names_source] = argv[1:]
    heroes = gamedata.load(sys.stdin)
    with Path(names_source).open(encoding="utf-8-sig") as name_lines:
        names = loc.tokens(name_lines)
    _ = sys.stdout.write(render(stats(heroes), attrs(heroes), names))


if __name__ == "__main__":
    main(sys.argv)
