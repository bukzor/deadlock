"""Recompile ``abilities.tsv`` — every ability bound to each live hero — from data.

Source: ``data/gamedata.json/scripts/{heroes,abilities}.json``.
Heroes bind abilities to slots via ``m_mapBoundAbilities``; the abilities are
defined in ``scripts/abilities.vdata``. This table resolves that join for every
bound slot: the four ``Signature_*`` (the upgradeable, hero-defining kit), the
guns and melee (``Weapon_*``; guns are abilities too), the innates, and the
movement kit (``Ability_Jump``, ``Ability_Mantle``, ... — shared entities, so
those rows repeat across heroes). ``bindings`` is the one enumeration of those
``(hero, slot, ability)`` keys; ``ability_profiles.tsv`` is keyed by the same.

Scope is the *live* roster (``m_bDisabled`` false). In-development heroes are
excluded because their abilities aren't shipped in ``abilities.vdata`` at all
(or are borrowed placeholders) — emitting them would fabricate rows.
``hero_base`` is excluded too: it is the inheritance template every hero
``_base``s, not a hero.

One row per (hero, slot), sorted; ``slot`` is the binding key with ``ESlot_``
stripped:

- ``ability``  — the bound ability entity name.
- ``type``     — ``m_eAbilityType`` (``EAbilityType_`` stripped): ``Signature``
  and ``Ultimate`` (the 4th signature), ``Weapon``, ``Melee``, ``Innate``.
- ``cooldown`` — ``AbilityCooldown`` in seconds; a space-separated list when the
  cooldown scales per upgrade level (e.g. ``40 30 20``).
- ``charges``  — ``AbilityCharges`` (0 = single cast on cooldown).

(``m_iMaxLevel`` and the upgrade-tier count are intentionally absent: both are
constant across every ability, so they carry no information.)

Every live hero must bind four signatures, and every binding must resolve and
carry these base stats; that invariant is asserted so a dangling binding on a
shipped hero fails loudly.

    python -m deadlock.abilities abilities.json < heroes.json
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from . import gamedata
from .types import dig, is_str_mapping

TEMPLATE_HERO = "hero_base"
_SLOT_PREFIX = "ESlot_"
SIGNATURE = "Signature_"
SIGNATURE_SLOTS = 4


@dataclass(frozen=True)
class Ability:
    """An ability's joined base facts, keyed by entity name."""

    type: str
    cooldown: str
    charges: str


@dataclass(frozen=True)
class Bound:
    """One emitted ``abilities.tsv`` row: one ability bound to a live hero."""

    hero: str
    slot: str
    ability: str
    type: str
    cooldown: str
    charges: str


def abilities(defs: Mapping[str, object]) -> dict[str, Ability]:
    """Per-ability ``{type, cooldown, charges}``, from the ``abilities.vdata`` tree."""
    result: dict[str, Ability] = {}
    for name, entity in defs.items():
        kind = dig(entity, "m_eAbilityType")
        cooldown = _prop(entity, "AbilityCooldown")
        charges = _prop(entity, "AbilityCharges")
        if kind is None or cooldown is None or charges is None:
            continue
        result[name] = Ability(_str(kind).removeprefix("EAbilityType_"), _value(cooldown), _value(charges))
    return result


def _prop(entity: object, prop: str) -> object:
    return dig(entity, "m_mapAbilityProperties", prop, "m_strValue")


def bindings(heroes: Mapping[str, object]) -> list[tuple[str, str, str]]:
    """Every ``(hero, slot, ability)`` binding of the live roster, ``ESlot_`` stripped."""
    result: list[tuple[str, str, str]] = []
    for hero, entity in heroes.items():
        slots = dig(entity, "m_mapBoundAbilities")
        if not is_str_mapping(slots) or hero == TEMPLATE_HERO or _bool(dig(entity, "m_bDisabled")):
            continue
        result.extend((hero, slot.removeprefix(_SLOT_PREFIX), _str(ability)) for slot, ability in slots.items())
    return result


def bound(heroes: Mapping[str, object], defs: Mapping[str, object]) -> list[Bound]:
    """Live heroes' bindings joined to ability stats; assert each resolves.

    ``heroes`` and ``defs`` are the nested trees of ``heroes.vdata`` and
    ``abilities.vdata`` (see ``deadlock.gamedata``).
    """
    defined = abilities(defs)
    result: list[Bound] = []
    for hero, slot, ability in bindings(heroes):
        assert ability in defined, (hero, slot, ability)
        stats = defined[ability]
        result.append(Bound(hero, slot, ability, stats.type, stats.cooldown, stats.charges))
    for hero in {b.hero for b in result}:
        kit = sorted(b.slot for b in result if b.hero == hero and b.slot.startswith(SIGNATURE))
        assert len(kit) == SIGNATURE_SLOTS, (hero, kit)
    return sorted(result, key=lambda b: (b.hero, b.slot))


def render(bound: Iterable[Bound]) -> str:
    """Render the kit as a tab-separated table with a header line."""
    body = "".join(
        f"{b.hero}\t{b.slot}\t{b.ability}\t{b.type}\t{b.cooldown}\t{b.charges}\n" for b in bound
    )
    return "hero\tslot\tability\ttype\tcooldown\tcharges\n" + body


def _value(value: object) -> str:
    """Render a KV3 ``m_strValue``: a bare number loses a trailing ``.0``; a
    string (possibly a space-separated per-level list) is kept verbatim."""
    if isinstance(value, bool):
        raise AssertionError(value)
    if isinstance(value, (int, float)):
        return str(int(value)) if value == int(value) else str(value)
    return _str(value)


def _str(value: object) -> str:
    assert isinstance(value, str), value
    return value


def _bool(value: object) -> bool:
    assert isinstance(value, bool), value
    return value


def main(argv: list[str]) -> None:
    [abilities_source] = argv[1:]
    heroes = gamedata.load(sys.stdin)
    with Path(abilities_source).open() as defs_file:
        defs = gamedata.load(defs_file)
    _ = sys.stdout.write(render(bound(heroes, defs)))


if __name__ == "__main__":
    main(sys.argv)
