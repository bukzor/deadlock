"""Recompile ``items.tsv`` — the shop item economy — from data.

Source: the flattened ``data/gamedata.flat/scripts/{abilities,generic_data}.jsonl``, read as nested trees.
Shop items live in
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

    python -m deadlock.items generic_data.jsonl < abilities.jsonl
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from . import flatten, jsonl
from .types import dig, is_sequence


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


def prices(generic: Mapping[str, object]) -> dict[int, int]:
    """The ``{tier: souls}`` cost table from the ``generic_data.vdata`` tree."""
    table = generic["m_nItemPricePerTier"]
    assert is_sequence(table), table
    return {tier: _int(price) for tier, price in enumerate(table)}


def items(abilities: Mapping[str, object], prices: Mapping[int, int]) -> list[Item]:
    """Items joined to their tier cost, sorted by name; assert every tier is priced.

    ``abilities`` is the nested tree of ``abilities.vdata`` (see ``deadlock.flatten.tree``).
    """
    result: list[Item] = []
    for name, item in abilities.items():
        tier_name = dig(item, "m_iItemTier")
        if tier_name is None:
            continue
        tier = int(_str(tier_name).removeprefix("EModTier_"))
        assert tier in prices, (name, tier)
        result.append(
            Item(
                name=name,
                tier=tier,
                cost=prices[tier],
                slot=_str(dig(item, "m_eItemSlotType") or "").removeprefix("EItemSlotType_"),
                shop_filter=_str(dig(item, "m_eShopFilters") or "").removeprefix("EShopFilter"),
                disabled=_truthy(dig(item, "m_bDisabled")),
                components=tuple(_str(c) for c in _list(dig(item, "m_vecComponentItems"))),
            )
        )
    return sorted(result, key=lambda item: item.name)


def _list(value: object) -> Sequence[object]:
    """``value`` as a sequence; empty when absent."""
    if value is None:
        return ()
    assert is_sequence(value), value
    return value


def render(items: Iterable[Item]) -> str:
    """Render items as a tab-separated table with a header line."""
    body = "".join(
        "\t".join(
            (
                i.name,
                str(i.tier),
                str(i.cost),
                i.slot,
                i.shop_filter,
                "true" if i.disabled else "false",
                ",".join(i.components),
            )
        )
        + "\n"
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
    [generic_source] = argv[1:]
    abilities = flatten.tree(jsonl.load_lines(sys.stdin))
    with Path(generic_source).open() as generic_lines:
        generic = flatten.tree(jsonl.load_lines(generic_lines))
    _ = sys.stdout.write(render(items(abilities, prices(generic))))


if __name__ == "__main__":
    main(sys.argv)
