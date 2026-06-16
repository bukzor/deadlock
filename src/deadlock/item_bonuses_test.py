from .item_bonuses import Bonus, bonuses, render


def _prop(item: str, prop: str, *, stat: str, value: object) -> list[dict[str, object]]:
    base = f"{item}.m_mapAbilityProperties.{prop}"
    return [
        {"file": "scripts/abilities.vdata", "path": f"{base}.m_eProvidedPropertyType", "value": stat},
        {"file": "scripts/abilities.vdata", "path": f"{base}.m_strValue", "value": value},
    ]


RECORDS = [
    {"file": "scripts/abilities.vdata", "path": "upgrade_a.m_iItemTier", "value": "EModTier_1"},
    *_prop("upgrade_a", "BonusHealth", stat="MODIFIER_VALUE_HEALTH_MAX", value="210"),
    *_prop("upgrade_a", "FireRate", stat="MODIFIER_VALUE_FIRE_RATE", value=8.0),
    # an inherited zero-valued provided stat is noise, not a bonus:
    *_prop("upgrade_a", "WeaponPower", stat="MODIFIER_VALUE_WEAPON_POWER", value="0"),
    # an internal param (no provided type) is not a bonus:
    {"file": "scripts/abilities.vdata", "path": "upgrade_a.m_mapAbilityProperties.ChannelMoveSpeed.m_strValue", "value": "-1"},
    # a provided property with no value is skipped (value applied only via upgrades):
    {"file": "scripts/abilities.vdata", "path": "upgrade_a.m_mapAbilityProperties.NoVal.m_eProvidedPropertyType", "value": "MODIFIER_VALUE_X"},
    # a non-item ability is ignored entirely:
    {"file": "scripts/abilities.vdata", "path": "ability_z.m_mapAbilityProperties.Dmg.m_eProvidedPropertyType", "value": "MODIFIER_VALUE_Y"},
    {"file": "scripts/abilities.vdata", "path": "ability_z.m_mapAbilityProperties.Dmg.m_strValue", "value": "99"},
]


class DescribeBonuses:
    def it_emits_nonzero_provided_stat_bonuses_per_item_stripping_the_prefix(self):
        assert bonuses(RECORDS) == [
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
