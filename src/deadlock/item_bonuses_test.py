from .item_bonuses import Bonus, bonuses, render


def _prop(*, stat: str, value: object) -> dict[str, object]:
    return {"m_eProvidedPropertyType": stat, "m_strValue": value}


ABILITIES = {
    "upgrade_a": {
        "m_iItemTier": "EModTier_1",
        "m_mapAbilityProperties": {
            "BonusHealth": _prop(stat="MODIFIER_VALUE_HEALTH_MAX", value="210"),
            "FireRate": _prop(stat="MODIFIER_VALUE_FIRE_RATE", value=8.0),
            # an inherited zero-valued provided stat is noise, not a bonus:
            "WeaponPower": _prop(stat="MODIFIER_VALUE_WEAPON_POWER", value="0"),
            # an internal param (no provided type) is not a bonus:
            "ChannelMoveSpeed": {"m_strValue": "-1"},
            # a provided property with no value is skipped (value applied only via upgrades):
            "NoVal": {"m_eProvidedPropertyType": "MODIFIER_VALUE_X"},
        },
    },
    # a non-item ability is ignored entirely:
    "ability_z": {"m_mapAbilityProperties": {"Dmg": _prop(stat="MODIFIER_VALUE_Y", value="99")}},
    "_include": ["scripts/other.vdata"],
}


class DescribeBonuses:
    def it_emits_nonzero_provided_stat_bonuses_per_item_stripping_the_prefix(self):
        assert bonuses(ABILITIES) == [
            Bonus(item="upgrade_a", property="BonusHealth", stat="HEALTH_MAX", value="210"),
            Bonus(item="upgrade_a", property="FireRate", stat="FIRE_RATE", value="8"),
        ]


class DescribeRender:
    def it_emits_tsv_sorted_by_item_then_property_with_header(self):
        rows = [
            Bonus(item="upgrade_a", property="BonusHealth", stat="HEALTH_MAX", value="210"),
            Bonus(item="upgrade_a", property="FireRate", stat="FIRE_RATE", value="8"),
        ]
        assert render(rows) == (
            "item\tproperty\tstat\tvalue\n"
            "upgrade_a\tBonusHealth\tHEALTH_MAX\t210\n"
            "upgrade_a\tFireRate\tFIRE_RATE\t8\n"
        )
