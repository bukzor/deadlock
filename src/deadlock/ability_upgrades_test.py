from .ability_upgrades import Upgrade, render, upgrades


def _upg(*, prop: str, bonus: object, key: str = "m_strPropertyName") -> dict[str, object]:
    return {key: prop, "m_strBonus": bonus}


def _tiers(*tiers: list[dict[str, object]]) -> dict[str, object]:
    return {"m_vecAbilityUpgrades": [{"m_vecPropertyUpgrades": tier} for tier in tiers]}


ABILITIES = {
    "ability_a": _tiers(
        [_upg(prop="FadingSlowPercent", bonus="25")],
        [
            _upg(prop="Damage", bonus=49.5),
            # the Valve typo spelling must still be captured:
            _upg(prop="AbilityCooldown", bonus="-2", key="m_StrPropertyNAme"),
        ],
        # a behavior-only upgrade (a bonus with no property name) is skipped:
        [{"m_strBonus": "9"}],
    ),
    # an ability outside the requested set is ignored:
    "ability_other": _tiers([_upg(prop="X", bonus="1")]),
    "_include": ["scripts/other.vdata"],
}


class DescribeUpgrades:
    def it_emits_named_property_upgrades_for_requested_abilities_renumbering_tiers_from_one(self):
        assert upgrades(ABILITIES, {"ability_a"}) == [
            Upgrade(ability="ability_a", tier=1, property="FadingSlowPercent", bonus="25"),
            Upgrade(ability="ability_a", tier=2, property="AbilityCooldown", bonus="-2"),
            Upgrade(ability="ability_a", tier=2, property="Damage", bonus="49.5"),
        ]

    def it_emits_nothing_for_an_ability_with_no_upgrades(self):
        assert upgrades({"ability_a": {"m_eAbilityType": "x"}}, {"ability_a"}) == []


class DescribeRender:
    def it_emits_tsv_with_header(self):
        rows = [Upgrade(ability="ability_a", tier=1, property="Damage", bonus="49.5")]
        assert render(rows) == "ability\ttier\tproperty\tbonus\nability_a\t1\tDamage\t49.5\n"
