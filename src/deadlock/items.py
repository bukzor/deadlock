"""Recompile ``items.tsv`` — the shop item economy — from data.

Source: the committed, flattened ``data/gamedata.jsonl``. Shop items live in
``scripts/abilities.vdata`` (an item is an ability with an ``m_iItemTier``).
Their soul cost is *not* stored per item: it is derived from the item's tier via
the global ``m_nItemPricePerTier`` table in ``scripts/generic_data.vdata``
(tiers 1..4 = 800/1600/3200/6400 souls). Resolving that join is this table's
value-add over the raw data.

One row per item, sorted by name:

- ``tier``        — integer tier (``EModTier_N`` → ``N``).
- ``cost``        — souls, ``m_nItemPricePerTier[tier]``.
- ``slot``        — ``Weapon`` | ``Armor`` | ``Tech`` (``EItemSlotType_`` stripped).
- ``shop_filter`` — shop category (``EShopFilter`` stripped), blank if unset.
- ``disabled``    — ``true`` for legacy/removed items still defined in the data
  (``m_bDisabled``, which serializes inconsistently as bool/``"true"``/``1``).
- ``components``  — comma-joined component items this upgrades from, in order.

All tiered items are emitted (including disabled and internal infrastructure
items) rather than editorially filtered, so a patch that enables/disables an
item shows as a single ``disabled`` cell change.

    python -m deadlock.items data/gamedata.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

ABILITIES_FILE = "scripts/abilities.vdata"
GENERIC_FILE = "scripts/generic_data.vdata"
_PRICE = re.compile(r"^m_nItemPricePerTier\[(\d+)\]$")
_ENTITY = re.compile(r"^(\w+)\.(.+)$")
_COMPONENT = re.compile(r"^m_vecComponentItems\[(\d+)\]$")


@dataclass(frozen=True)
class Item:
    """One emitted ``items.tsv`` row: an item with its resolved cost and metadata."""

    name: str
    tier: int
    cost: int
    slot: str
    shop_filter: str
    disabled: bool
    components: tuple[str, ...]


def prices(records: Iterable[Mapping[str, object]]) -> dict[int, int]:
    """The ``{tier: souls}`` cost table from ``generic_data.vdata``."""
    result: dict[int, int] = {}
    for record in records:
        if record["file"] != GENERIC_FILE:
            continue
        match = _PRICE.match(_str(record["path"]))
        if match:
            result[int(match.group(1))] = _int(record["value"])
    return result


def items(records: Iterable[Mapping[str, object]], prices: Mapping[int, int]) -> list[Item]:
    """Items joined to their tier cost, sorted by name; assert every tier is priced."""
    fields: dict[str, dict[str, object]] = {}
    components: dict[str, dict[int, str]] = {}
    for record in records:
        if record["file"] != ABILITIES_FILE:
            continue
        entity = _ENTITY.match(_str(record["path"]))
        if not entity:
            continue
        name, field = entity.group(1), entity.group(2)
        component = _COMPONENT.match(field)
        if component:
            components.setdefault(name, {})[int(component.group(1))] = _str(record["value"])
        else:
            fields.setdefault(name, {})[field] = record["value"]
    result: list[Item] = []
    for name, item in fields.items():
        if "m_iItemTier" not in item:
            continue
        tier = int(_str(item["m_iItemTier"]).removeprefix("EModTier_"))
        assert tier in prices, (name, tier)
        result.append(
            Item(
                name=name,
                tier=tier,
                cost=prices[tier],
                slot=_str(item.get("m_eItemSlotType", "")).removeprefix("EItemSlotType_"),
                shop_filter=_str(item.get("m_eShopFilters", "")).removeprefix("EShopFilter"),
                disabled=_truthy(item.get("m_bDisabled")),
                components=tuple(c for _, c in sorted(components.get(name, {}).items())),
            )
        )
    return sorted(result, key=lambda item: item.name)


def render(items: Iterable[Item]) -> str:
    """Render items as a tab-separated table with a header line."""
    body = "".join(
        f"{i.name}\t{i.tier}\t{i.cost}\t{i.slot}\t{i.shop_filter}\t"
        f"{'true' if i.disabled else 'false'}\t{','.join(i.components)}\n"
        for i in items
    )
    return "item\ttier\tcost\tslot\tshop_filter\tdisabled\tcomponents\n" + body


def _truthy(value: object) -> bool:
    """Normalize ``m_bDisabled``, which serializes as bool, ``"true"``, or ``1``."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        assert value in ("true", "false"), value
        return value == "true"
    raise AssertionError(value)


def _str(value: object) -> str:
    assert isinstance(value, str), value
    return value


def _int(value: object) -> int:
    assert isinstance(value, int), value
    return value


def main(argv: list[str]) -> None:
    [source] = argv[1:]
    records = list(json.loads(line) for line in Path(source).read_text().splitlines())
    sys.stdout.write(render(items(records, prices(records))))


if __name__ == "__main__":
    main(sys.argv)
