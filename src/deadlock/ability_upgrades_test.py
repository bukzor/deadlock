from .ability_upgrades import Upgrade, render, upgrades


def _upg(ability: str, tier: int, i: int, *, prop: str, bonus: object, key: str = "m_strPropertyName") -> list[dict[str, object]]:
    base = f"{ability}.m_vecAbilityUpgrades[{tier}].m_vecPropertyUpgrades[{i}]"
    return [
        {"file": "scripts/abilities.vdata", "path": f"{base}.{key}", "value": prop},
        {"file": "scripts/abilities.vdata", "path": f"{base}.m_strBonus", "value": bonus},
    ]


RECORDS = [
    *_upg("ability_a", 0, 0, prop="FadingSlowPercent", bonus="25"),
    *_upg("ability_a", 1, 0, prop="Damage", bonus=49.5),
    # the Valve typo spelling must still be captured:
    *_upg("ability_a", 1, 1, prop="AbilityCooldown", bonus="-2", key="m_StrPropertyNAme"),
    # a behavior-only upgrade (a bonus with no property name) is skipped:
    {"file": "scripts/abilities.vdata", "path": "ability_a.m_vecAbilityUpgrades[2].m_vecPropertyUpgrades[0].m_strBonus", "value": "9"},
    # an ability outside the requested set is ignored:
    *_upg("ability_other", 0, 0, prop="X", bonus="1"),
]


class DescribeUpgrades:
    def it_emits_named_property_upgrades_for_requested_abilities_renumbering_tiers_from_one(self):
        assert upgrades(RECORDS, {"ability_a"}) == [
            Upgrade(ability="ability_a", tier=1, property="FadingSlowPercent", bonus="25"),
            Upgrade(ability="ability_a", tier=2, property="AbilityCooldown", bonus="-2"),
            Upgrade(ability="ability_a", tier=2, property="Damage", bonus="49.5"),
        ]


class DescribeRender:
    def it_emits_tsv_with_header(self):
        rows = [Upgrade(ability="ability_a", tier=1, property="Damage", bonus="49.5")]
        assert render(rows) == "ability\ttier\tproperty\tbonus\nability_a\t1\tDamage\t49.5\n"
