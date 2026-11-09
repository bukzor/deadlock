import pytest

from .ability_profiles import Profile, profiles, render


def _hero(*, disabled: bool, primary: str | None, **slots: str) -> dict[str, object]:
    bound = dict(slots) if primary is None else {"ESlot_Weapon_Primary": primary, **slots}
    return {"m_bDisabled": disabled, "m_mapBoundAbilities": bound}


def _info(
    *, damage: object, bullets: int, clip: int, cycle: object, reload: object, rng: object, burst: int = 1, intra: object = 0.0
) -> dict[str, object]:
    return {
        "m_flBulletDamage": damage,
        "m_iBullets": bullets,
        "m_iBurstShotCount": burst,
        "m_flCycleTime": cycle,
        "m_flIntraBurstCycleTime": intra,
        "m_iClipSize": clip,
        "m_reloadDuration": reload,
        "m_flRange": rng,
    }


def _gun(info: dict[str, object]) -> list[Profile]:
    """The rows for a lone hero wielding ``info`` as its primary."""
    return profiles({"hero_a": _hero(disabled=False, primary="weap")}, {"weap": _infos(primary=info)})


def _infos(**named: dict[str, object]) -> dict[str, object]:
    return {"m_mapWeaponInfos": named}


HEROES = {
    "hero_a": _hero(disabled=False, primary="weap_a"),
    "hero_base": _hero(disabled=False, primary="weap_a"),
    "hero_dev": _hero(disabled=True, primary="weap_dev"),
    "hero_unarmed": _hero(disabled=False, primary=None),
}
GUN_INFO = _info(damage=4.0, bullets=9, clip=9, cycle=0.5, reload=2.0, rng=7000.0)
ABILITIES = {"weap_a": _infos(primary=GUN_INFO)}
GUN_A = Profile(
    "hero_a", "Weapon_Primary", "weap_a", "primary",
    damage=4.0, bullets=9, burst=1, cycle=0.5, intra=0.0, clip=9, reload=2.0, range=7000.0, bps=2.0, dps=72.0, sdps=49.8,
)  # fmt: skip


class DescribeProfiles:
    def it_joins_live_heroes_bound_abilities_excludes_base_and_computes_dps(self):
        assert profiles(HEROES, ABILITIES) == [GUN_A]

    def it_fails_when_a_live_primary_weapon_is_undefined(self):
        heroes = {"hero_b": _hero(disabled=False, primary="ghost")}
        with pytest.raises(AssertionError, match="ghost"):
            _ = profiles(heroes, {})

    def it_fails_when_a_primary_weapon_stat_is_missing(self):
        abilities = {"weap_a": _infos(primary={"m_flBulletDamage": 1.0})}
        with pytest.raises(AssertionError, match="m_iBullets"):
            _ = profiles({"hero_a": _hero(disabled=False, primary="weap_a")}, abilities)

    def it_emits_every_profile_of_an_ability(self):
        abilities = {"weap_a": _infos(primary=GUN_INFO, alt={"m_flBulletDamage": 9.0})}
        assert profiles({"hero_a": HEROES["hero_a"]}, abilities) == [
            Profile("hero_a", "Weapon_Primary", "weap_a", "alt", damage=9.0),
            GUN_A,
        ]

    def it_keys_each_row_by_the_slot_the_ability_is_bound_to(self):
        heroes = {"hero_a": _hero(disabled=False, primary="weap_a", ESlot_Weapon_Secondary="weap_alt")}
        abilities = {**ABILITIES, "weap_alt": _infos(primary={"m_iClipSize": 8})}
        assert profiles(heroes, abilities) == [GUN_A, Profile("hero_a", "Weapon_Secondary", "weap_alt", "primary", clip=8)]

    def it_emits_a_row_per_bound_ability_profile_that_sets_a_stat(self):
        heroes = {"hero_a": _hero(disabled=False, primary="weap_a", ESlot_Signature_4="ability_ult")}
        ult = _infos(primary={"m_flBulletSpeed": 10000.0}, fakegun={"m_iBullets": 4, "m_flBulletSpeed": 2000.0})
        assert profiles(heroes, {**ABILITIES, "ability_ult": ult}) == [
            Profile("hero_a", "Signature_4", "ability_ult", "fakegun", bullets=4),
            GUN_A,
        ]

    def it_derives_rates_only_for_guns(self):
        heroes = {"hero_a": _hero(disabled=False, primary="weap_a", ESlot_Signature_1="ability_x")}
        x = _infos(primary=_info(damage=10.0, bullets=2, cycle=0.5, clip=3, reload=1.0, rng=100.0))
        assert profiles(heroes, {**ABILITIES, "ability_x": x}) == [
            Profile(
                "hero_a", "Signature_1", "ability_x", "primary",
                damage=10.0, bullets=2, burst=1, cycle=0.5, intra=0.0, clip=3, reload=1.0, range=100.0,
            ),  # fmt: skip
            GUN_A,
        ]

    def it_skips_bound_abilities_without_weapon_infos(self):
        heroes = {"hero_a": _hero(disabled=False, primary="weap_a", ESlot_Ability_Jump="ability_jump")}
        assert profiles(heroes, {**ABILITIES, "ability_jump": {}}) == [GUN_A]


class DescribeGunRates:
    """Expected values are the in-game UI's (see docs/dev/mechanics.kb/gun-fire-rate.md)."""

    def it_waits_intra_after_every_shot_of_a_burst(self):
        [seven] = _gun(_info(damage=10.8, bullets=1, burst=3, cycle=0.2625, intra=0.084, clip=29, reload=2.35, rng=0.0))
        assert (seven.bps, seven.dps) == (5.83, 63.0)

    def it_ignores_intra_on_a_single_shot_gun(self):
        [paige] = _gun(_info(damage=32.0, bullets=1, burst=1, cycle=0.5, intra=0.1, clip=10, reload=2.0, rng=0.0))
        assert (paige.bps, paige.dps) == (2.0, 64.0)

    def it_multiplies_damage_not_rate_by_pellets(self):
        [rat_king] = _gun(_info(damage=5.8, bullets=2, burst=1, cycle=0.2, intra=0.1, clip=30, reload=2.0, rng=0.0))
        assert (rat_king.bps, rat_king.dps) == (5.0, 58.0)

    def it_sustains_damage_over_a_clip_and_its_reload(self):
        [seven] = _gun(_info(damage=10.8, bullets=1, burst=3, cycle=0.2625, intra=0.084, clip=29, reload=2.35, rng=0.0))
        assert seven.sdps == 42.8

    def it_counts_shots_per_clip_by_ammo_consumed_per_shot(self):
        info = _info(damage=42.0, bullets=1, cycle=1.26, clip=10, reload=2.1, rng=0.0)
        [viscous_alt] = _gun({**info, "m_iAmmoConsumedPerShot": 5})
        assert viscous_alt.sdps == 18.2

    def it_reloads_single_bullet_guns_one_shell_at_a_time_after_a_delay(self):
        info = _info(damage=3.78, bullets=9, cycle=0.63, clip=9, reload=0.3525, rng=0.0)
        [abrams] = _gun({**info, "m_bReloadSingleBullets": True, "m_flReloadSingleBulletsInitialDelay": 0.705})
        assert (abrams.dps, abrams.sdps) == (54.0, 32.1)


class DescribeRender:
    def it_emits_tsv_dropping_trailing_zeros_with_one_decimal_dps_and_blank_unset_stats(self):
        rows = [
            Profile(
                "hero_a", "Weapon_Primary", "weap_a", "primary",
                damage=5.5, bullets=1, burst=1, cycle=0.105, intra=0.0, clip=27, reload=2.25, range=7000.0,
                bps=9.52, dps=52.4, sdps=37.0,
            ),  # fmt: skip
            Profile("hero_a", "Signature_4", "ability_x", "fakegun", bullets=4),
        ]
        assert render(rows) == (
            "hero\tslot\tability\tprofile\tdamage\tbullets\tburst\tcycle\tintra\tbps\tdps\tclip\treload\tsdps\trange\n"
            "hero_a\tWeapon_Primary\tweap_a\tprimary\t5.5\t1\t1\t0.105\t0\t9.52\t52.4\t27\t2.25\t37.0\t7000\n"
            "hero_a\tSignature_4\tability_x\tfakegun\t\t4\t\t\t\t\t\t\t\t\t\n"
        )
