from collections.abc import Mapping

import pytest
from deadlock import gamedata, paths
from deadlock.abilities import bindings
from pytest import approx

from .melee import HEAVY, LIGHT, melee_cycle
from .types import BadRequest


def _hero(light: float = 50, heavy: float = 116, melee: str = "melee_a") -> Mapping[str, object]:
    return {
        "m_bDisabled": False,
        "m_mapStartingStats": {"ELightMeleeDamage": light, "EHeavyMeleeDamage": heavy},
        "m_mapBoundAbilities": {"ESlot_Weapon_Melee": melee},
    }


def _melee(light: tuple[float, float] = (0.75, 0.75), heavy: tuple[float, float] = (1.0, 1.3)) -> Mapping[str, object]:
    def attack(cooldowns: tuple[float, float]) -> Mapping[str, object]:
        return {"m_flCooldownOnHit": cooldowns[0], "m_flCooldownOnMiss": cooldowns[1]}

    return {"m_mapAttacks": {"EAttackType_Light": attack(light), "EAttackType_Heavy": attack(heavy)}}


HEROES = {"hero_a": _hero(), "hero_b": _hero(light=63, heavy=128, melee="melee_b")}
ABILITIES = {"melee_a": _melee(), "melee_b": _melee(light=(0.65, 0.65), heavy=(1.1, 1.4))}


def _cycle(
    hero: str,
    ability: str,
    windup: float = 0.0,
    heroes: Mapping[str, object] = HEROES,
    abilities: Mapping[str, object] = ABILITIES,
):
    result = melee_cycle(heroes, abilities, hero, ability, windup)
    assert result is not None, (hero, ability)
    return result


class DescribeMeleeCycle:
    def it_returns_none_for_any_other_ability(self):
        assert melee_cycle(HEROES, ABILITIES, "hero_a", "melee_a", 0.0) is None

    def it_swings_once_per_cycle_for_the_heros_damage(self):
        cycle, _ = _cycle("hero_b", LIGHT)
        assert [(h.trigger, h.damage) for h in cycle.hits] == [(0, 63)]
        cycle, _ = _cycle("hero_b", HEAVY)
        assert [(h.trigger, h.damage) for h in cycle.hits] == [(0, 128)]

    def it_repeats_at_the_cooldown_on_hit_of_the_bound_melee(self):
        assert _cycle("hero_a", HEAVY)[0].period == approx(1.0)
        assert _cycle("hero_b", LIGHT)[0].period == approx(0.65)
        assert _cycle("hero_b", HEAVY)[0].period == approx(1.1)

    def it_never_reloads(self):
        assert _cycle("hero_a", LIGHT)[0].reload == 0

    def it_lands_after_the_windup(self):
        hit = _cycle("hero_a", LIGHT, windup=0.3)[0].hits[0]
        assert (hit.trigger, hit.land) == approx((0, 0.3))

    def it_notes_the_windup_is_a_parameter(self):
        notes = _cycle("hero_a", LIGHT, windup=0.3)[1]
        assert any("windup" in n and "0.3" in n for n in notes), notes

    def it_notes_that_hits_are_modeled_when_a_miss_differs(self):
        notes = _cycle("hero_b", HEAVY)[1]
        assert any("1.1" in n and "1.4" in n for n in notes), notes

    def it_says_nothing_of_misses_when_they_cost_the_same(self):
        notes = _cycle("hero_a", LIGHT)[1]
        assert not any("miss" in n for n in notes), notes

    class WhenTheRequestIsBad:
        def it_rejects_an_unknown_hero(self):
            with pytest.raises(BadRequest, match="hero_z"):
                _ = melee_cycle(HEROES, ABILITIES, "hero_z", LIGHT, 0.0)

        def it_rejects_a_negative_windup(self):
            with pytest.raises(BadRequest, match="windup"):
                _ = melee_cycle(HEROES, ABILITIES, "hero_a", LIGHT, -0.1)


def _load(name: str) -> Mapping[str, object]:
    path = paths.data_dir() / "gamedata.json/scripts" / name
    if not path.exists():
        pytest.skip(f"no local game data at {path}; build it with `redo` at the repo root")
    with path.open() as file:
        return gamedata.load(file)


class DescribeRealData:
    def it_yields_both_melee_cycles_for_every_live_hero(self):
        heroes, abilities = _load("heroes.json"), _load("abilities.json")
        live = sorted({hero for hero, _, _ in bindings(heroes)})
        assert live
        for hero in live:
            for ability in (LIGHT, HEAVY):
                cycle, _ = _cycle(hero, ability, heroes=heroes, abilities=abilities)
                assert cycle.hits[0].damage > 0, (hero, ability)
                assert cycle.period is not None and cycle.period > 0, (hero, ability)

