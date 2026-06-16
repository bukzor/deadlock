import pytest

from .items import Item, items, prices, render

RECORDS = [
    {"file": "scripts/generic_data.vdata", "path": "m_nItemPricePerTier[0]", "value": 0},
    {"file": "scripts/generic_data.vdata", "path": "m_nItemPricePerTier[1]", "value": 800},
    {"file": "scripts/generic_data.vdata", "path": "m_nItemPricePerTier[2]", "value": 1600},
    {"file": "scripts/abilities.vdata", "path": "upgrade_a.m_iItemTier", "value": "EModTier_1"},
    {"file": "scripts/abilities.vdata", "path": "upgrade_a.m_eItemSlotType", "value": "EItemSlotType_Weapon"},
    {"file": "scripts/abilities.vdata", "path": "upgrade_a.m_eShopFilters", "value": "EShopFilterDPS"},
    {"file": "scripts/abilities.vdata", "path": "upgrade_b.m_iItemTier", "value": "EModTier_2"},
    {"file": "scripts/abilities.vdata", "path": "upgrade_b.m_eItemSlotType", "value": "EItemSlotType_Armor"},
    {"file": "scripts/abilities.vdata", "path": "upgrade_b.m_bDisabled", "value": "true"},
    {"file": "scripts/abilities.vdata", "path": "upgrade_b.m_vecComponentItems[0]", "value": "upgrade_a"},
    {"file": "scripts/abilities.vdata", "path": "not_an_item.m_eAbilityType", "value": "EAbilityType_Item"},
]


class DescribePrices:
    def it_reads_the_tier_price_table(self):
        assert prices(RECORDS) == {0: 0, 1: 800, 2: 1600}


class DescribeItems:
    def it_joins_tier_to_cost_strips_prefixes_and_normalizes_disabled(self):
        assert items(RECORDS, prices(RECORDS)) == [
            Item("upgrade_a", tier=1, cost=800, slot="Weapon", shop_filter="DPS", disabled=False, components=()),
            Item("upgrade_b", tier=2, cost=1600, slot="Armor", shop_filter="", disabled=True, components=("upgrade_a",)),
        ]

    def it_fails_when_a_tier_has_no_price(self):
        rows = [{"file": "scripts/abilities.vdata", "path": "x.m_iItemTier", "value": "EModTier_9"}]
        with pytest.raises(AssertionError, match="9"):
            items(rows, {0: 0})


class DescribeRender:
    def it_emits_tsv_sorted_by_name_with_header(self):
        assert render(items(RECORDS, prices(RECORDS))) == (
            "item\ttier\tcost\tslot\tshop_filter\tdisabled\tcomponents\n"
            "upgrade_a\t1\t800\tWeapon\tDPS\tfalse\t\n"
            "upgrade_b\t2\t1600\tArmor\t\ttrue\tupgrade_a\n"
        )
