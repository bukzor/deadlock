"""Recompile ``item_bonuses.tsv`` — the stat bonuses each shop item grants — from data.

Source: the committed, flattened ``data/gamedata.flat/scripts/abilities.jsonl``. This is the
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

    python -m deadlock.item_bonuses < data/gamedata.flat/scripts/abilities.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

_ENTITY = re.compile(r"^(\w+)\.(.+)$")
_PROP = re.compile(r"^m_mapAbilityProperties\.([^.]+)\.(m_eProvidedPropertyType|m_strValue)$")
_MODIFIER_PREFIX = "MODIFIER_VALUE_"


@dataclass(frozen=True)
class Bonus:
    """One emitted ``item_bonuses.tsv`` row: a stat an item provides."""

    item: str
    property: str
    stat: str
    value: str


def bonuses(records: Iterable[Mapping[str, object]]) -> list[Bonus]:
    """Provided-stat bonuses for every tiered item, sorted by (item, property)."""
    fields: dict[str, dict[str, dict[str, object]]] = {}
    is_item: set[str] = set()
    for record in records:
        entity = _ENTITY.match(_str(record["path"]))
        if not entity:
            continue
        name, rest = entity.group(1), entity.group(2)
        if rest == "m_iItemTier":
            is_item.add(name)
        prop = _PROP.match(rest)
        if prop:
            fields.setdefault(name, {}).setdefault(prop.group(1), {})[prop.group(2)] = record["value"]
    result: list[Bonus] = []
    for item in is_item:
        for prop, sub in fields.get(item, {}).items():
            if "m_eProvidedPropertyType" not in sub or "m_strValue" not in sub:
                continue
            value = _value(sub["m_strValue"])
            if value == "0":
                continue
            stat = _str(sub["m_eProvidedPropertyType"]).removeprefix(_MODIFIER_PREFIX)
            result.append(Bonus(item, prop, stat, value))
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
    records = (json.loads(line) for line in sys.stdin)
    sys.stdout.write(render(bonuses(records)))


if __name__ == "__main__":
    main()
