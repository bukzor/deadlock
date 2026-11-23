from collections.abc import Mapping

import pytest
from bukzor_deadlock import paths
from bukzor_deadlock.abilities import bindings
from bukzor_deadlock_lookup.entities import Hero
from bukzor_deadlock_lookup.load import load
from pytest import approx

from . import boons
from .boons import Boons


def _level(standard: bool) -> Mapping[str, object]:
    info: dict[str, object] = {"m_unRequiredGold": 0, "m_mapBonusCurrencies": {"EAbilityPoints": 1}}
    return {**info, "m_bUseStandardUpgrade": True} if standard else info


def _hero(standard: tuple[bool, ...] = (False, True, True, True)) -> Mapping[str, object]:
    return {
        "m_mapStartingStats": {"ELightMeleeDamage": 50, "EHeavyMeleeDamage": 125},
        "m_mapLevelInfo": {str(game): _level(s) for game, s in enumerate(standard, start=1)},
        "m_mapStandardLevelUpUpgrades": {
            "MODIFIER_VALUE_BASE_BULLET_DAMAGE_FROM_LEVEL": 0.25,
            "MODIFIER_VALUE_BASE_MELEE_DAMAGE_FROM_LEVEL": 2.0,
            "MODIFIER_VALUE_TECH_POWER": 1.5,
        },
    }


HEROES = {"hero_a": _hero(), "hero_gap": _hero((False, True, False, True))}


def _of(key: str, heroes: Mapping[str, Mapping[str, object]] = HEROES) -> Hero:
    return Hero(key, None, heroes[key])


class DescribeLastLevel:
    def it_is_one_less_than_the_last_game_level(self):
        assert boons.last_level(_of("hero_a")) == 3


class DescribeAtLevel:
    def it_grants_nothing_at_level_0(self):
        assert boons.at_level(_of("hero_a"), 0) == Boons()

    def it_adds_one_boon_per_standard_level_up(self):
        assert boons.at_level(_of("hero_a"), 2) == Boons(count=2, bullet=0.5, light_melee=4.0, heavy_melee=10.0, spirit=3.0)

    def it_skips_a_level_up_without_the_standard_upgrade(self):
        assert boons.at_level(_of("hero_gap"), 3).count == 2

    def it_scales_heavy_melee_in_proportion_to_light(self):
        assert boons.at_level(_of("hero_a"), 1).heavy_melee == approx(2.0 * 125 / 50)

    @pytest.mark.parametrize("level", [-1, 4])
    def it_asserts_the_level_is_in_range(self, level: int):
        with pytest.raises(AssertionError):
            _ = boons.at_level(_of("hero_a"), level)


def _real():
    path = paths.data_dir() / "gamedata.json/scripts"
    if not path.exists():
        pytest.skip(f"no local game data at {path}; build it with `redo` at the repo root")
    return load()


class DescribeRealData:
    def it_ends_every_live_hero_at_level_35(self):
        game = _real()
        live = sorted({hero for hero, _, _ in bindings(game.heroes)})
        assert live and {boons.last_level(game.hero(hero)) for hero in live} == {35}

    def it_matches_the_wikis_per_boon_numbers_for_abrams(self):
        found = boons.at_level(_real().hero("hero_atlas"), 1)
        assert (found.bullet, found.light_melee, found.heavy_melee, found.spirit) == approx((0.1, 1.738, 4.03, 1.1), abs=0.005)


SCALED: Mapping[str, Mapping[str, object]] = {"hero_s": {"m_mapScalingStats": {"EBulletDamage": {"eScalingStat": "ETechPower", "flScale": 0.08}}}, "hero_a": _hero()}


class DescribeSpiritNote:

    def it_notes_a_stat_that_grows_with_the_levels_spirit(self):
        [note] = boons.spirit_note(_of("hero_s", SCALED), "EBulletDamage", "Bullet damage", 11.0)
        assert "Bullet damage" in note and "0.08" in note and "11" in note and "not included" in note, note

    @pytest.mark.parametrize(("hero", "stat", "spirit"), [("hero_s", "EBulletDamage", 0.0), ("hero_s", "EHeavyMeleeDamage", 11.0), ("hero_a", "EBulletDamage", 11.0)])
    def it_says_nothing_otherwise(self, hero: str, stat: str, spirit: float):
        assert boons.spirit_note(_of(hero, SCALED), stat, "x", spirit) == []
