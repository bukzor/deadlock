"""Recompile ``weapons.tsv`` — each live hero's primary weapon — from data.

Source: the committed, flattened ``data/gamedata.jsonl``. Heroes in
``scripts/heroes.vdata`` bind a primary weapon to ``ESlot_Weapon_Primary``; the
weapon's stats live in that entity's ``m_WeaponInfo`` in
``scripts/abilities.vdata``. This table resolves that join for the live roster.

``hero_base`` is excluded: it is the inheritance template (every hero ``_base``s
it) and binds another hero's weapon as a placeholder, so it isn't a real entry.
Disabled (in-development) heroes are excluded for the same reason as in
``deadlock.abilities`` — their data isn't shipped.

One row per hero, sorted, in raw weapon units:

- ``damage``  — ``m_flBulletDamage`` per bullet.
- ``bullets`` — ``m_iBullets`` fired per shot (>1 for shotgun-like weapons).
- ``clip``    — ``m_iClipSize``.
- ``cycle``   — ``m_flCycleTime``, seconds between shots.
- ``reload``  — ``m_reloadDuration``, seconds.
- ``range``   — ``m_flRange``.
- ``dps``     — derived sustained damage: ``damage * bullets / cycle`` (this is
  *not* in the raw data; it is the table's value-add).

Every live hero's primary must define all six base fields; that invariant is
asserted so a missing field or dangling weapon fails loudly.

    python -m deadlock.weapons data/gamedata.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

HEROES_FILE = "scripts/heroes.vdata"
ABILITIES_FILE = "scripts/abilities.vdata"
TEMPLATE_HERO = "hero_base"
_PRIMARY = re.compile(r"^(hero_\w+)\.m_mapBoundAbilities\.ESlot_Weapon_Primary$")
_DISABLED = re.compile(r"^(hero_\w+)\.m_bDisabled$")
_INFO = re.compile(r"^(\w+)\.m_WeaponInfo\.(\w+)$")
_FIELDS = {
    "damage": "m_flBulletDamage",
    "bullets": "m_iBullets",
    "clip": "m_iClipSize",
    "cycle": "m_flCycleTime",
    "reload": "m_reloadDuration",
    "range": "m_flRange",
}


@dataclass(frozen=True)
class Weapon:
    """One emitted ``weapons.tsv`` row: a live hero's primary weapon stats."""

    hero: str
    weapon: str
    damage: float
    bullets: int
    clip: int
    cycle: float
    reload: float
    range: float
    dps: float


def weapons(records: Iterable[Mapping[str, object]]) -> list[Weapon]:
    """Live heroes' primaries joined to weapon stats, with derived DPS; sorted."""
    primary: dict[str, str] = {}
    disabled: dict[str, bool] = {}
    info: dict[str, dict[str, object]] = {}
    for record in records:
        path = _str(record["path"])
        if record["file"] == HEROES_FILE:
            slot = _PRIMARY.match(path)
            if slot:
                primary[slot.group(1)] = _str(record["value"])
            flag = _DISABLED.match(path)
            if flag:
                disabled[flag.group(1)] = _bool(record["value"])
        elif record["file"] == ABILITIES_FILE:
            field = _INFO.match(path)
            if field:
                info.setdefault(field.group(1), {})[field.group(2)] = record["value"]
    result: list[Weapon] = []
    for hero, weapon in primary.items():
        if hero == TEMPLATE_HERO or disabled[hero]:
            continue
        assert weapon in info, (hero, weapon)
        stats = info[weapon]
        values = {name: _num(stats[key]) for name, key in _resolved(hero, weapon, stats)}
        result.append(_weapon(hero, weapon, values))
    return sorted(result, key=lambda w: w.hero)


def _resolved(hero: str, weapon: str, stats: Mapping[str, object]) -> Iterable[tuple[str, str]]:
    """Yield ``(column, key)`` for the six base fields; assert each is present."""
    for name, key in _FIELDS.items():
        assert key in stats, (hero, weapon, key)
        yield name, key


def _weapon(hero: str, weapon: str, v: Mapping[str, float]) -> Weapon:
    dps = round(v["damage"] * v["bullets"] / v["cycle"], 1) if v["cycle"] else 0.0
    return Weapon(hero, weapon, v["damage"], int(v["bullets"]), int(v["clip"]), v["cycle"], v["reload"], v["range"], dps)


def render(weapons: Iterable[Weapon]) -> str:
    """Render weapons as a tab-separated table with a header line."""
    body = "".join(
        f"{w.hero}\t{w.weapon}\t{_fmt(w.damage)}\t{w.bullets}\t{w.clip}\t"
        f"{_fmt(w.cycle)}\t{_fmt(w.reload)}\t{_fmt(w.range)}\t{w.dps}\n"
        for w in weapons
    )
    return "hero\tweapon\tdamage\tbullets\tclip\tcycle\treload\trange\tdps\n" + body


def _num(value: object) -> float:
    assert isinstance(value, (int, float, str)) and not isinstance(value, bool), value
    return float(value)


def _fmt(value: float) -> str:
    """Render a float without a trailing ``.0`` for whole numbers."""
    return str(int(value)) if value == int(value) else str(value)


def _str(value: object) -> str:
    assert isinstance(value, str), value
    return value


def _bool(value: object) -> bool:
    assert isinstance(value, bool), value
    return value


def main(argv: list[str]) -> None:
    [source] = argv[1:]
    records = (json.loads(line) for line in Path(source).read_text().splitlines())
    sys.stdout.write(render(weapons(records)))


if __name__ == "__main__":
    main(sys.argv)
