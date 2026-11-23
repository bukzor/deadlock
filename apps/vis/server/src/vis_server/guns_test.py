from collections.abc import Mapping

import pytest
from bukzor_deadlock import gamedata, paths
from bukzor_deadlock.abilities import bindings
from bukzor_deadlock.ability_profiles import profiles
from pytest import approx

from . import guns
from .boons import Boons
from .timeline import Cycle, Gun, gun_cycle

INCH = 0.0254  # meters per engine unit


def _info(**extra: object) -> dict[str, object]:
    """A primary weapon profile; an ``extra`` of ``None`` removes that field."""
    info = {
        "m_flBulletDamage": 4.0,
        "m_iBullets": 9,
        "m_iBurstShotCount": 1,
        "m_flCycleTime": 0.5,
        "m_flIntraBurstCycleTime": 0.0,
        "m_iClipSize": 9,
        "m_reloadDuration": 2.0,
        "m_flRange": 7000.0,
        "m_flBulletSpeed": 25000.0,
        **extra,
    }
    return {key: value for key, value in info.items() if value is not None}


def _curve(*speeds: float) -> dict[str, object]:
    return {"m_spline": [{"x": 100.0 * i, "y": y} for i, y in enumerate(speeds)]}


def _trees(**extra: object) -> tuple[Mapping[str, object], Mapping[str, object]]:
    """Live ``hero_a`` with primary ``weap`` (beside a non-``primary`` profile) and secondary ``alt``, and
    ``hero_b``; ``extra`` merges into ``weap``'s ``primary`` profile."""
    heroes = {
        "hero_a": {
            "m_bDisabled": False,
            "m_mapBoundAbilities": {"ESlot_Weapon_Primary": "weap", "ESlot_Weapon_Secondary": "alt"},
        },
        "hero_b": {"m_bDisabled": False, "m_mapBoundAbilities": {"ESlot_Weapon_Primary": "weap_b"}},
    }
    abilities = {
        "weap": {"m_mapWeaponInfos": {"primary": _info(**extra), "fakegun": {"m_flBulletDamage": 0.0}}},
        "alt": {"m_mapWeaponInfos": {"primary": _info()}},
        "weap_b": {"m_mapWeaponInfos": {"primary": _info()}},
    }
    return heroes, abilities


def _gun(distance: float = 0.0, **extra: object) -> tuple[Cycle, list[str]]:
    result = guns.cycle(*_trees(**extra), "hero_a", "weap", distance)
    assert result is not None
    return result


BASE = Gun(damage=4.0, pellets=9, burst=1, cycle=0.5, intra=0.0, shots=9, reload=2.0, travel=0.0)


class DescribeCycle:
    def it_builds_one_clip_and_its_reload_from_the_primary_profile(self):
        assert _gun() == (gun_cycle(BASE), [])

    @pytest.mark.parametrize(("hero", "ability"), [("hero_a", "alt"), ("hero_a", "weap_b"), ("hero_z", "weap")])
    def it_is_none_for_any_key_but_the_heros_primary_weapon(self, hero: str, ability: str):
        assert guns.cycle(*_trees(), hero, ability) is None

    def it_adds_the_levels_bullet_damage_to_each_pellet(self):
        result = guns.cycle(*_trees(), "hero_a", "weap", boons=Boons(count=4, bullet=0.5, spirit=4.4))
        assert result is not None
        assert result[0].hits[0].damage == approx((4.0 + 0.5) * 9)

    def it_notes_bullet_damage_that_grows_with_the_levels_spirit(self):
        _, abilities = _trees()
        scaling = {"EBulletDamage": {"eScalingStat": "ETechPower", "flScale": 0.08}}
        hero = {"m_bDisabled": False, "m_mapBoundAbilities": {"ESlot_Weapon_Primary": "weap"}, "m_mapScalingStats": scaling}
        result = guns.cycle({"hero_a": hero}, abilities, "hero_a", "weap", boons=Boons(count=4, spirit=4.4))
        assert result is not None
        assert [n for n in result[1] if n.startswith("Bullet damage also grows with spirit")], result[1]

    def it_fires_a_clip_divided_by_the_ammo_per_shot(self):
        cycle, _ = _gun(m_iAmmoConsumedPerShot=3)
        assert len(cycle.hits) == 3

    def it_reloads_single_bullets_from_empty_and_says_that_is_unverified(self):
        cycle, notes = _gun(m_bReloadSingleBullets=True, m_flReloadSingleBulletsInitialDelay=0.5, m_reloadDuration=0.25)
        assert cycle.downtime == approx(0.5 + 9 * 0.25)
        assert [n for n in notes if "Not checked in-game" in n and "reloads" in n], notes

    class WhenTheBulletTravels:
        def it_lands_after_distance_over_the_flat_speed(self):
            cycle, notes = _gun(distance=25000 * INCH / 10)
            assert (cycle.hits[0].land, notes) == (approx(0.1), [])

        def it_takes_the_speed_from_the_curve_when_present(self):
            cycle, _ = _gun(distance=22500 * INCH / 10, m_BulletSpeedCurve=_curve(22500.0, 22500.0))
            assert cycle.hits[0].land == approx(0.1)

        def it_notes_when_the_curve_disagrees_with_the_flat_speed(self):
            _, notes = _gun(m_BulletSpeedCurve=_curve(22500.0, 22500.0))
            assert [n for n in notes if "571.5" in n and "635" in n], notes

        def it_fails_on_a_curve_that_varies(self):
            with pytest.raises(NotImplementedError, match="m_BulletSpeedCurve"):
                _ = _gun(m_BulletSpeedCurve=_curve(22500.0, 10000.0))

        def it_lands_on_the_trigger_and_says_so_when_the_speed_is_unknown(self):
            cycle, notes = _gun(distance=30.0, m_flBulletSpeed=None)
            assert cycle.hits[0].land == cycle.hits[0].trigger
            assert [n for n in notes if "speed" in n and "not in the data" in n], notes

        def it_orders_notes_by_how_much_they_move_the_numbers(self):
            extra = {"m_flDamageFalloffStartRange": 20 / INCH, "m_bReloadSingleBullets": True, "m_BulletSpeedCurve": _curve(22500.0, 22500.0)}
            _, notes = _gun(distance=21, **extra)
            assert [n.split()[0] for n in notes] == ["Damage", "This", "The"], notes  # falloff, reload, speed

        def it_notes_damage_falloff_only_beyond_its_start(self):
            start = 20 / INCH
            assert _gun(distance=20, m_flDamageFalloffStartRange=start)[1] == []
            _, notes = _gun(distance=21, m_flDamageFalloffStartRange=start)
            assert [n for n in notes if "falloff" in n and "20 m" in n], notes


def _load(name: str) -> Mapping[str, object]:
    path = paths.data_dir() / "gamedata.json/scripts" / name
    if not path.exists():
        pytest.skip(f"no local data: {path} (build it with `redo` at the repo root)")
    with path.open() as file:
        return gamedata.load(file)


class DescribeRealData:
    def it_reproduces_every_live_heros_profile_dps_and_sdps(self):
        heroes, abilities = _load("heroes.json"), _load("abilities.json")
        oracle = {(p.hero, p.ability): p for p in profiles(heroes, abilities) if (p.slot, p.profile) == ("Weapon_Primary", "primary")}
        bound = [(hero, ability) for hero, slot, ability in bindings(heroes) if slot == "Weapon_Primary"]
        assert bound, "no live hero binds a primary weapon"
        for hero, ability in bound:
            result = guns.cycle(heroes, abilities, hero, ability)
            assert result is not None, (hero, ability)
            cycle, _ = result
            assert cycle.period is not None, (hero, ability)
            damage = sum(h.damage for h in cycle.hits)
            profile = oracle[hero, ability]
            # the profile rounds to 0.1
            assert damage / (cycle.period - cycle.downtime) == approx(profile.dps, abs=0.051), (hero, ability)
            assert damage / cycle.period == approx(profile.sdps, abs=0.051), (hero, ability)
