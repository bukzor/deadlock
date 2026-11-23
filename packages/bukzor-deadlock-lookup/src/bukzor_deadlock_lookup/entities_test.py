import pytest

from .entities import Ability, Attack, Hero, NotANumber, Scale, Weapon, number

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
GUN = {
    "m_flBulletSpeed": 20000,
    "m_flDamageFalloffStartRange": "500",
    "m_bReloadSingleBullets": True,
    "m_flReloadSingleBulletsInitialDelay": 0.5,
    "m_iAmmoConsumedPerShot": 2,
    "m_BulletSpeedCurve": {"m_spline": [{"x": 0, "y": 100}, {"x": 1, "y": 200}]},
}
WEAPON = Ability(
    key="gun",
    name=None,
    tree={
        "m_mapWeaponInfos": {"primary": GUN, "bare": {}},
        "m_mapAttacks": {
            "EAttackType_Heavy": {"m_flCooldownOnHit": 1.0, "m_flCooldownOnMiss": 1.3}
        },
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

    def it_gives_a_property_as_the_data_writes_it(self):
        assert [BLAST.text("Levels"), BLAST.text("Melee")] == ["40 30 20", "3"]

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


class DescribeWeapon:
    def it_reads_a_weapon_profile(self):
        assert WEAPON.weapon("primary") == Weapon(
            ammo_per_shot=2.0,
            reload_single=True,
            reload_single_delay=0.5,
            bullet_speed=20000.0,
            speed_curve=(100.0, 200.0),
            falloff_start=500.0,
        )

    def it_defaults_what_a_profile_leaves_out(self):
        assert WEAPON.weapon("bare") == Weapon(
            ammo_per_shot=1.0,
            reload_single=False,
            reload_single_delay=0.0,
            bullet_speed=None,
            speed_curve=None,
            falloff_start=None,
        )


class DescribeAttack:
    def it_reads_the_cooldowns_on_a_hit_and_a_miss(self):
        assert WEAPON.attack("EAttackType_Heavy") == Attack(on_hit=1.0, on_miss=1.3)


HERO = Hero(
    key="hero_a",
    name="Alpha",
    tree={
        "m_mapStartingStats": {"ELightMeleeDamage": 50, "EMaxHealth": 600.0},
        "m_mapScalingStats": {
            "EBulletDamage": {"eScalingStat": "ETechPower", "flScale": 0.14}
        },
        "m_mapStandardLevelUpUpgrades": {"MODIFIER_VALUE_TECH_POWER": 1.5},
        "m_mapLevelInfo": {"1": {}, "2": {"m_bUseStandardUpgrade": True}},
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

    def it_reads_how_a_stat_scales(self):
        assert HERO.scaling("EBulletDamage") == Scale(stat="ETechPower", factor=0.14)

    def it_is_none_for_a_stat_that_does_not_scale(self):
        assert HERO.scaling("EMaxHealth") is None

    def it_reads_what_one_boon_adds(self):
        assert HERO.per_boon("MODIFIER_VALUE_TECH_POWER") == 1.5

    def it_says_which_game_levels_grant_a_boon(self):
        assert [HERO.grants_boon(1), HERO.grants_boon(2)] == [False, True]
