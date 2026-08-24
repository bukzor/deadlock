import pytest

from .weapons import Weapon, render, weapons


def _hero(name: str, *, disabled: bool, primary: str) -> list[dict[str, object]]:
    return [
        {"path": f"{name}.m_bDisabled", "value": disabled},
        {"path": f"{name}.m_mapBoundAbilities.ESlot_Weapon_Primary", "value": primary},
    ]


def _weapon(name: str, *, damage: object, bullets: int, clip: int, cycle: object, reload: object, rng: object) -> list[dict[str, object]]:
    info = f"{name}.m_WeaponInfo"
    return [
        {"path": f"{info}.m_flBulletDamage", "value": damage},
        {"path": f"{info}.m_iBullets", "value": bullets},
        {"path": f"{info}.m_iClipSize", "value": clip},
        {"path": f"{info}.m_flCycleTime", "value": cycle},
        {"path": f"{info}.m_reloadDuration", "value": reload},
        {"path": f"{info}.m_flRange", "value": rng},
    ]


HERO_RECORDS = [
    *_hero("hero_a", disabled=False, primary="weap_a"),
    *_hero("hero_base", disabled=False, primary="weap_a"),
    *_hero("hero_dev", disabled=True, primary="weap_dev"),
]
ABILITY_RECORDS = [
    *_weapon("weap_a", damage=4.0, bullets=9, clip=9, cycle=0.5, reload=2.0, rng=7000.0),
]


class DescribeWeapons:
    def it_joins_live_primaries_excludes_base_and_computes_dps(self):
        assert weapons(HERO_RECORDS, ABILITY_RECORDS) == [
            Weapon("hero_a", "weap_a", damage=4.0, bullets=9, clip=9, cycle=0.5, reload=2.0, range=7000.0, dps=72.0)
        ]

    def it_fails_when_a_live_primary_weapon_is_undefined(self):
        heroes = _hero("hero_b", disabled=False, primary="ghost")
        with pytest.raises(AssertionError, match="ghost"):
            weapons(heroes, [])


class DescribeRender:
    def it_emits_tsv_dropping_trailing_zeros_with_one_decimal_dps(self):
        rows = [Weapon("hero_a", "weap_a", damage=5.5, bullets=1, clip=27, cycle=0.105, reload=2.25, range=7000.0, dps=52.4)]
        assert render(rows) == (
            "hero\tweapon\tdamage\tbullets\tclip\tcycle\treload\trange\tdps\n"
            "hero_a\tweap_a\t5.5\t1\t27\t0.105\t2.25\t7000\t52.4\n"
        )
