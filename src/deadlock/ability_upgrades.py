"""Recompile ``ability_upgrades.tsv`` — what each signature ability upgrade does — from data.

Source: ``data/gamedata.json/scripts/{heroes,abilities}.json``. Each ability's three upgrades (bought with ability points) live in ``m_vecAbilityUpgrades[tier]``,
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

    python -m deadlock.ability_upgrades heroes.json < abilities.json
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from . import gamedata
from .abilities import SIGNATURE, bound
from .types import dig, is_sequence

_NAME_KEYS = ("m_strPropertyName", "m_StrPropertyNAme")  # the second is a typo shipped in the data


@dataclass(frozen=True)
class Upgrade:
    """One emitted ``ability_upgrades.tsv`` row: one tier's bonus to one property."""

    ability: str
    tier: int
    property: str
    bonus: str


def upgrades(defs: Mapping[str, object], abilities: frozenset[str] | set[str]) -> list[Upgrade]:
    """Named property upgrades for the requested abilities, sorted by (ability, tier, property).

    ``defs`` is the nested tree of ``abilities.vdata`` (see ``deadlock.gamedata``).
    """
    result: list[Upgrade] = []
    for ability in abilities:
        for tier, tier_upgrades in enumerate(_list(dig(defs, ability, "m_vecAbilityUpgrades"))):
            for entry in _list(dig(tier_upgrades, "m_vecPropertyUpgrades")):
                name = next((n for n in (dig(entry, k) for k in _NAME_KEYS) if n is not None), None)
                bonus = dig(entry, "m_strBonus")
                if name is None or bonus is None:
                    continue
                result.append(Upgrade(ability, tier + 1, _str(name), _value(bonus)))
    return sorted(result, key=lambda u: (u.ability, u.tier, u.property))


def _list(value: object) -> Sequence[object]:
    """``value`` as a sequence; empty when absent."""
    if value is None:
        return ()
    assert is_sequence(value), value
    return value


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
    [heroes_source] = argv[1:]
    defs = gamedata.load(sys.stdin)
    with Path(heroes_source).open() as heroes_file:
        heroes = gamedata.load(heroes_file)
    signatures = {b.ability for b in bound(heroes, defs) if b.slot.startswith(SIGNATURE)}
    _ = sys.stdout.write(render(upgrades(defs, signatures)))


if __name__ == "__main__":
    main(sys.argv)
