"""Recompile ``abilities.tsv`` — each live hero's four signature abilities — from data.

Source: the flattened ``data/gamedata.flat/scripts/{heroes,abilities}.jsonl``, read as nested trees.
Heroes bind abilities to slots via ``m_mapBoundAbilities``; the abilities are
defined in ``scripts/abilities.vdata``. This table resolves
that join for the four ``ESlot_Signature_*`` slots — the upgradeable, hero-
defining kit.

Scope is the *live* roster (``m_bDisabled`` false). In-development heroes are
excluded because their abilities aren't shipped in ``abilities.vdata`` at all
(or are borrowed placeholders) — emitting them would fabricate rows. The weapon
and movement slots are deliberately omitted: weapons aren't abilities with these
stats, and the movement kit is shared.

One row per (hero, slot), sorted:

- ``ability``  — the bound ability entity name.
- ``type``     — ``m_eAbilityType`` (``EAbilityType_`` stripped); the 4th slot
  is the ``Ultimate``, the rest ``Signature``.
- ``cooldown`` — ``AbilityCooldown`` in seconds; a space-separated list when the
  cooldown scales per upgrade level (e.g. ``40 30 20``).
- ``charges``  — ``AbilityCharges`` (0 = single cast on cooldown).

(``m_iMaxLevel`` and the upgrade-tier count are intentionally absent: both are
constant across every ability, so they carry no information.)

Every live hero must bind four signatures that all resolve and carry these base
stats; that invariant is asserted so a dangling binding on a shipped hero fails
loudly.

    python -m deadlock.abilities abilities.jsonl < heroes.jsonl
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from . import flatten, jsonl
from .types import dig, is_str_mapping

_SLOT_PREFIX = "ESlot_"
_SIGNATURE = "Signature_"
SIGNATURE_SLOTS = 4


@dataclass(frozen=True)
class Ability:
    """An ability's joined base facts, keyed by entity name."""

    type: str
    cooldown: str
    charges: str


@dataclass(frozen=True)
class Bound:
    """One emitted ``abilities.tsv`` row: a live hero's signature ability."""

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


def signatures(entity: object) -> dict[str, str]:
    """A hero's ``{slot: ability}`` for the ``ESlot_Signature_*`` bindings."""
    slots = dig(entity, "m_mapBoundAbilities")
    if not is_str_mapping(slots):
        return {}
    prefix = _SLOT_PREFIX + _SIGNATURE
    return {slot.removeprefix(_SLOT_PREFIX): _str(ability) for slot, ability in slots.items() if slot.startswith(prefix)}


def bound(heroes: Mapping[str, object], defs: Mapping[str, object]) -> list[Bound]:
    """Live heroes' signature bindings joined to ability stats; assert each resolves.

    ``heroes`` and ``defs`` are the nested trees of ``heroes.vdata`` and
    ``abilities.vdata`` (see ``deadlock.flatten.tree``).
    """
    defined = abilities(defs)
    result: list[Bound] = []
    for hero, entity in heroes.items():
        slots = signatures(entity)
        if not slots or _bool(dig(entity, "m_bDisabled")):
            continue
        assert len(slots) == SIGNATURE_SLOTS, (hero, sorted(slots))
        for slot, ability in slots.items():
            assert ability in defined, (hero, slot, ability)
            stats = defined[ability]
            result.append(Bound(hero, slot, ability, stats.type, stats.cooldown, stats.charges))
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
    heroes = flatten.tree(jsonl.load_lines(sys.stdin))
    with Path(abilities_source).open() as defs_lines:
        defs = flatten.tree(jsonl.load_lines(defs_lines))
    _ = sys.stdout.write(render(bound(heroes, defs)))


if __name__ == "__main__":
    main(sys.argv)
