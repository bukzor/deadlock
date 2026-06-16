"""Recompile ``ability_upgrades.tsv`` — what each signature ability upgrade does — from data.

Source: the committed, flattened ``data/gamedata.jsonl``. Each ability's three
upgrades (bought with ability points) live in ``m_vecAbilityUpgrades[tier]``,
whose ``m_vecPropertyUpgrades`` list each names a property and a flat bonus.
This is the "what does leveling it do" companion to ``deadlock.abilities``,
scoped to the same live signature abilities (via ``abilities.bound``).

One row per (ability, tier, property), sorted:

- ``tier``     — the upgrade tier, 1..3 (the ``m_vecAbilityUpgrades`` index + 1).
- ``property`` — the upgraded property (``Damage``, ``AbilityCooldown``, …).
- ``bonus``    — the flat ``m_strBonus`` (verbatim; may be negative).

Scope is *named property* upgrades. Behavior-only upgrades (a bonus with no
property name, or an ``m_eUpgradeType`` unlock) are out of scope. One ability,
``ability_magician_copyult``, has no upgrades at all. The shipped data contains
a typo'd key, ``m_StrPropertyNAme`` (on yamato's ult); both spellings are
accepted so its upgrade isn't silently dropped.

    python -m deadlock.ability_upgrades data/gamedata.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from .abilities import bound

ABILITIES_FILE = "scripts/abilities.vdata"
_ENTITY = re.compile(r"^(\w+)\.(.+)$")
_UPGRADE = re.compile(
    r"^m_vecAbilityUpgrades\[(\d+)\]\.m_vecPropertyUpgrades\[(\d+)\]\.(m_strPropertyName|m_StrPropertyNAme|m_strBonus)$"
)
_NAME_KEYS = ("m_strPropertyName", "m_StrPropertyNAme")  # the second is a typo shipped in the data


@dataclass(frozen=True)
class Upgrade:
    """One emitted ``ability_upgrades.tsv`` row: one tier's bonus to one property."""

    ability: str
    tier: int
    property: str
    bonus: str


def upgrades(records: Iterable[Mapping[str, object]], abilities: frozenset[str] | set[str]) -> list[Upgrade]:
    """Named property upgrades for the requested abilities, sorted by (ability, tier, property)."""
    # collate each (ability, tier, index) entry's name + bonus before pairing
    entries: dict[tuple[str, int, int], dict[str, object]] = {}
    for record in records:
        if record["file"] != ABILITIES_FILE:
            continue
        entity = _ENTITY.match(_str(record["path"]))
        if not entity or entity.group(1) not in abilities:
            continue
        upgrade = _UPGRADE.match(entity.group(2))
        if upgrade:
            key = (entity.group(1), int(upgrade.group(1)), int(upgrade.group(2)))
            entries.setdefault(key, {})[upgrade.group(3)] = record["value"]
    result: list[Upgrade] = []
    for (ability, tier, _), entry in entries.items():
        name = next((entry[k] for k in _NAME_KEYS if k in entry), None)
        if name is None or "m_strBonus" not in entry:
            continue
        result.append(Upgrade(ability, tier + 1, _str(name), _value(entry["m_strBonus"])))
    return sorted(result, key=lambda u: (u.ability, u.tier, u.property))


def render(upgrades: Iterable[Upgrade]) -> str:
    """Render upgrades as a tab-separated table with a header line."""
    body = "".join(f"{u.ability}\t{u.tier}\t{u.property}\t{u.bonus}\n" for u in upgrades)
    return "ability\ttier\tproperty\tbonus\n" + body


def _value(value: object) -> str:
    """Render an ``m_strBonus``: a bare number loses a trailing ``.0``; else verbatim."""
    if isinstance(value, bool):
        raise AssertionError(value)
    if isinstance(value, (int, float)):
        return str(int(value)) if value == int(value) else str(value)
    return _str(value)


def _str(value: object) -> str:
    assert isinstance(value, str), value
    return value


def main(argv: list[str]) -> None:
    [source] = argv[1:]
    records = [json.loads(line) for line in Path(source).read_text().splitlines()]
    signatures = {b.ability for b in bound(records)}
    sys.stdout.write(render(upgrades(records, signatures)))


if __name__ == "__main__":
    main(sys.argv)
