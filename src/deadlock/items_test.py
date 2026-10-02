import pytest

from .items import Item, items, prices, render

GENERIC = {"m_nItemPricePerTier": [0, 800, 1600]}
ABILITIES = {
    "upgrade_a": {"m_iItemTier": "EModTier_1", "m_eItemSlotType": "EItemSlotType_Weapon", "m_eShopFilters": "EShopFilterDPS"},
    "upgrade_b": {
        "m_iItemTier": "EModTier_2",
        "m_eItemSlotType": "EItemSlotType_Armor",
        "m_bDisabled": "true",
        "m_vecComponentItems": ["upgrade_a"],
    },
    "not_an_item": {"m_eAbilityType": "EAbilityType_Item"},
    "_include": ["scripts/other.vdata"],
}


class DescribePrices:
    def it_reads_the_tier_price_table(self):
        assert prices(GENERIC) == {0: 0, 1: 800, 2: 1600}


class DescribeItems:
    def it_joins_tier_to_cost_strips_prefixes_and_normalizes_disabled(self):
        assert items(ABILITIES, prices(GENERIC)) == [
            Item("upgrade_a", tier=1, cost=800, slot="Weapon", shop_filter="DPS", disabled=False, components=()),
            Item("upgrade_b", tier=2, cost=1600, slot="Armor", shop_filter="", disabled=True, components=("upgrade_a",)),
        ]

    def it_fails_when_a_tier_has_no_price(self):
        rows = {"x": {"m_iItemTier": "EModTier_9"}}
        with pytest.raises(AssertionError, match="9"):
            _ = items(rows, {0: 0})


class DescribeRender:
    def it_emits_tsv_sorted_by_name_with_header(self):
        assert render(items(ABILITIES, prices(GENERIC))) == (
            "item\ttier\tcost\tslot\tshop_filter\tdisabled\tcomponents\n"
            "upgrade_a\t1\t800\tWeapon\tDPS\tfalse\t\n"
            "upgrade_b\t2\t1600\tArmor\t\ttrue\tupgrade_a\n"
        )
