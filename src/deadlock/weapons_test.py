import pytest

from .weapons import Weapon, render, weapons


def _hero(*, disabled: bool, primary: str | None) -> dict[str, object]:
    bound = {} if primary is None else {"ESlot_Weapon_Primary": primary}
    return {"m_bDisabled": disabled, "m_mapBoundAbilities": bound}


def _weapon(*, damage: object, bullets: int, clip: int, cycle: object, reload: object, rng: object) -> dict[str, object]:
    info = {
        "m_flBulletDamage": damage,
        "m_iBullets": bullets,
        "m_iClipSize": clip,
        "m_flCycleTime": cycle,
        "m_reloadDuration": reload,
        "m_flRange": rng,
    }
    return {"m_mapWeaponInfos": {"primary": info}}


HEROES = {
    "hero_a": _hero(disabled=False, primary="weap_a"),
    "hero_base": _hero(disabled=False, primary="weap_a"),
    "hero_dev": _hero(disabled=True, primary="weap_dev"),
    "hero_unarmed": _hero(disabled=False, primary=None),
}
ABILITIES = {
    "weap_a": _weapon(damage=4.0, bullets=9, clip=9, cycle=0.5, reload=2.0, rng=7000.0),
}


class DescribeWeapons:
    def it_joins_live_primaries_excludes_base_and_computes_dps(self):
        assert weapons(HEROES, ABILITIES) == [
            Weapon("hero_a", "weap_a", damage=4.0, bullets=9, clip=9, cycle=0.5, reload=2.0, range=7000.0, dps=72.0)
        ]

    def it_fails_when_a_live_primary_weapon_is_undefined(self):
        heroes = {"hero_b": _hero(disabled=False, primary="ghost")}
        with pytest.raises(AssertionError, match="ghost"):
            _ = weapons(heroes, {})

    def it_fails_when_a_stat_is_missing(self):
        abilities = {"weap_a": {"m_mapWeaponInfos": {"primary": {"m_flBulletDamage": 1.0}}}}
        with pytest.raises(AssertionError, match="m_iBullets"):
            _ = weapons({"hero_a": _hero(disabled=False, primary="weap_a")}, abilities)

    def it_fails_when_any_weapon_gains_a_second_weapon_info(self):
        abilities: dict[str, object] = {**ABILITIES, "weap_alt": {"m_mapWeaponInfos": {"primary": {}, "secondary": {}}}}
        with pytest.raises(AssertionError, match="secondary"):
            _ = weapons(HEROES, abilities)


class DescribeRender:
    def it_emits_tsv_dropping_trailing_zeros_with_one_decimal_dps(self):
        rows = [Weapon("hero_a", "weap_a", damage=5.5, bullets=1, clip=27, cycle=0.105, reload=2.25, range=7000.0, dps=52.4)]
        assert render(rows) == (
            "hero\tweapon\tdamage\tbullets\tclip\tcycle\treload\trange\tdps\n"
            "hero_a\tweap_a\t5.5\t1\t27\t0.105\t2.25\t7000\t52.4\n"
        )
