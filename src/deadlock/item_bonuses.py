"""Recompile ``item_bonuses.tsv`` — the stat bonuses each shop item grants — from data.

Source: ``data/gamedata.json/scripts/abilities.json``. This is the
"what does it do" companion to ``deadlock.items`` (which gives cost/tier/slot).
An item's passive stat bonuses are the ``m_mapAbilityProperties`` entries that
carry an ``m_eProvidedPropertyType`` (the engine modifier they provide) — which
distinguishes a real bonus from the internal ability params (``AbilityCooldown``,
``ChannelMoveSpeed``, …) present on every item.

One row per (item, bonus), sorted:

- ``property`` — the item-local property name (``BonusHealth``); what tooltips
  reference.
- ``stat``     — the engine modifier provided, ``MODIFIER_VALUE_`` stripped
  (``HEALTH_MAX``); the ground-truth effect.
- ``value``    — the base ``m_strValue`` (verbatim; may carry a unit like ``15m``).

Scope is *passive provided-stat* bonuses. Active/proc effects (on-cast damage,
triggered buffs) aren't expressed as a provided stat and are out of scope here.
A provided property with no base ``m_strValue`` (its value comes only from
per-level upgrades) is skipped — a bonus needs a value. Zero-valued bonuses are
dropped too: nearly every item inherits ``WeaponPower``/``TechPower`` provided
stats defaulting to 0, which would otherwise be ~46% noise.

    python -m deadlock.item_bonuses < data/gamedata.json/scripts/abilities.json
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from . import gamedata
from .types import dig, is_str_mapping

_MODIFIER_PREFIX = "MODIFIER_VALUE_"


@dataclass(frozen=True)
class Bonus:
    """One emitted ``item_bonuses.tsv`` row: a stat an item provides."""

    item: str
    property: str
    stat: str
    value: str


def bonuses(abilities: Mapping[str, object]) -> list[Bonus]:
    """Provided-stat bonuses for every tiered item, sorted by (item, property).

    ``abilities`` is the nested tree of ``abilities.vdata`` (see ``deadlock.gamedata``).
    """
    result: list[Bonus] = []
    for item, entity in abilities.items():
        if dig(entity, "m_iItemTier") is None:
            continue
        props = dig(entity, "m_mapAbilityProperties")
        if not is_str_mapping(props):
            continue
        for prop, sub in props.items():
            provided, raw = dig(sub, "m_eProvidedPropertyType"), dig(sub, "m_strValue")
            if provided is None or raw is None:
                continue
            value = _value(raw)
            if value == "0":
                continue
            result.append(Bonus(item, prop, _str(provided).removeprefix(_MODIFIER_PREFIX), value))
    return sorted(result, key=lambda b: (b.item, b.property))


def render(bonuses: Iterable[Bonus]) -> str:
    """Render bonuses as a tab-separated table with a header line."""
    body = "".join(f"{b.item}\t{b.property}\t{b.stat}\t{b.value}\n" for b in bonuses)
    return "item\tproperty\tstat\tvalue\n" + body


def _value(value: object) -> str:
    """Render an ``m_strValue``: a bare number loses a trailing ``.0``; a string
    (which may carry a unit suffix like ``15m``) is kept verbatim."""
    if isinstance(value, bool):
        raise AssertionError(value)
    if isinstance(value, (int, float)):
        return str(int(value)) if value == int(value) else str(value)
    return _str(value)


def _str(value: object) -> str:
    assert isinstance(value, str), value
    return value


def main() -> None:
    abilities = gamedata.load(sys.stdin)
    _ = sys.stdout.write(render(bonuses(abilities)))


if __name__ == "__main__":
    main()
