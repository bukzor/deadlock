import pytest

from .entities import Ability, Hero, NotANumber, Scale, number

TECH = {
    "_class": "scale_function_tech_damage",
    "m_flStatScale": 0.5,
    "m_eSpecificStatScaleType": "ETechPower",
}
BLAST = Ability(
    key="blast",
    name="Blast",
    tree={
        "m_mapAbilityProperties": {
            "Damage": {
                "m_strValue": "100",
                "m_subclassScaleFunction": TECH,
                "m_bIsAbilityDamageProperty": True,
            },
            "Bare": {
                "m_strValue": "1",
                "m_subclassScaleFunction": {
                    "_class": "scale_function_tech_damage",
                    "m_flStatScale": 2,
                },
            },
            "Melee": {
                "m_strValue": 3,
                "m_subclassScaleFunction": {
                    "m_flStatScale": 1.5,
                    "m_eSpecificStatScaleType": "ELightMeleeDamage",
                },
            },
            "Levels": {"m_strValue": "40 30 20"},
            "ImpactDamage": {"m_strValue": "5", "m_bIsAbilityDamageProperty": True},
        }
    },
)


class DescribeNumber:
    @pytest.mark.parametrize(
        "value, expected",
        [(3, 3.0), (2.5, 2.5), ("100", 100.0), ("-.5", -0.5), ("1.", 1.0)],
    )
    def it_reads_numbers_and_numeric_strings(self, value: object, expected: float):
        assert number(value) == expected

    @pytest.mark.parametrize("value", [True, None, "0.1m", "40 30 20", ""])
    def it_rejects_anything_else(self, value: object):
        with pytest.raises(NotANumber):
            _ = number(value)


class DescribeAbility:
    def it_reads_a_property(self):
        assert BLAST.value("Damage") == 100.0

    def it_defaults_an_absent_property(self):
        assert BLAST.value("AbilityCooldown", 0.0) == 0.0

    def it_raises_for_an_absent_property_without_a_default(self):
        with pytest.raises(KeyError):
            _ = BLAST.value("AbilityCooldown")

    def it_names_the_ability_when_a_property_is_not_a_number(self):
        with pytest.raises(NotANumber) as error:
            _ = BLAST.value("Levels")
        assert str(error.value) == "blast: Levels is '40 30 20', not a number"

    def it_lists_its_damage_properties(self):
        assert BLAST.damage_properties() == ["Damage", "ImpactDamage"]

    class WhenScaling:
        def it_reads_a_named_stat(self):
            assert BLAST.scale("Damage") == Scale(stat="ETechPower", factor=0.5)

        def it_reads_an_unnamed_tech_damage_function_as_spirit(self):
            assert BLAST.scale("Bare") == Scale(stat="ETechPower", factor=2.0)

        def it_reads_another_stat(self):
            assert BLAST.scale("Melee") == Scale(stat="ELightMeleeDamage", factor=1.5)

        def it_is_none_without_a_scale(self):
            assert BLAST.scale("Levels") is None

        def it_says_whether_it_is_spirit(self):
            assert [
                Scale("ETechPower", 1).spirit,
                Scale("ELightMeleeDamage", 1).spirit,
                Scale(None, 1).spirit,
            ] == [True, False, False]


HERO = Hero(
    key="hero_a",
    name="Alpha",
    tree={
        "m_mapStartingStats": {"ELightMeleeDamage": 50, "EMaxHealth": 600.0},
        "m_mapBoundAbilities": {
            "ESlot_Weapon_Primary": "gun_a",
            "ESlot_Signature_1": "blast",
        },
    },
)


class DescribeHero:
    def it_reads_its_kit_by_slot(self):
        assert HERO.kit == {"Weapon_Primary": "gun_a", "Signature_1": "blast"}

    def it_reads_a_starting_stat(self):
        assert HERO.stat("ELightMeleeDamage") == 50.0

    def it_has_no_kit_without_bindings(self):
        assert Hero("hero_x", None, {}).kit == {}
