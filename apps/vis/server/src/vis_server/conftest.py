"""Synthetic game data shared by the query tests."""

import signal
from collections.abc import Generator, Mapping
from contextlib import contextmanager

from .queries import GameData, registry


TECH = {"_class": "scale_function_tech_damage", "m_flStatScale": 0.5, "m_eSpecificStatScaleType": "ETechPower"}


def ability_props(**values: object) -> dict[str, object]:
    return {k: v if isinstance(v, Mapping) else {"m_strValue": v} for k, v in values.items()}


def level(game: int) -> dict[str, object]:
    info: dict[str, object] = {"m_unRequiredGold": 100 * game, "m_mapBonusCurrencies": {"EAbilityPoints": 1}}
    return info if game == 1 else {**info, "m_bUseStandardUpgrade": True}


PER_BOON = {
    "MODIFIER_VALUE_BASE_BULLET_DAMAGE_FROM_LEVEL": 0.25,
    "MODIFIER_VALUE_BASE_MELEE_DAMAGE_FROM_LEVEL": 2.0,
    "MODIFIER_VALUE_TECH_POWER": 1.5,
}


def hero(slots: Mapping[str, str], disabled: bool = False) -> dict[str, object]:
    """A hero whose last level is 3."""
    return {
        "m_bDisabled": disabled,
        "m_mapStartingStats": {"ELightMeleeDamage": 50, "EHeavyMeleeDamage": 116},
        "m_mapBoundAbilities": {f"ESlot_{slot}": ability for slot, ability in slots.items()},
        "m_mapLevelInfo": {str(game): level(game) for game in range(1, 5)},
        "m_mapStandardLevelUpUpgrades": PER_BOON,
    }


GUN = {
    "m_flBulletDamage": 4.0, "m_iBullets": 1, "m_iBurstShotCount": 1, "m_flCycleTime": 0.5,
    "m_flIntraBurstCycleTime": 0.0, "m_iClipSize": 4, "m_reloadDuration": 2.0, "m_flRange": 7000.0,
    "m_flBulletSpeed": 10000 / 0.0254,  # 10000 m/s
}  # fmt: skip
ATTACK = {"m_flCooldownOnHit": 0.75, "m_flCooldownOnMiss": 0.75}
KIT = {"Weapon_Primary": "gun_a", "Weapon_Melee": "melee_a", "Signature_2": "buff", "Signature_1": "blast"}
DATA = GameData(
    heroes={
        "hero_c": hero({"Weapon_Melee": "melee_a"}),
        "hero_a": hero(KIT),
        "hero_off": hero(KIT, disabled=True),
        "hero_dev": hero(KIT),  # live, but not listed
    },
    abilities={
        "gun_a": {"m_mapWeaponInfos": {"primary": GUN}},
        "melee_a": {"m_mapAttacks": {"EAttackType_Light": ATTACK, "EAttackType_Heavy": ATTACK}},
        "blast": {"m_mapAbilityProperties": ability_props(Damage={"m_strValue": "100", "m_subclassScaleFunction": TECH},
                                                   AbilityCooldown="10", AbilityCastDelay="0.5")},
        "buff": {"m_mapAbilityProperties": ability_props(AbilityCooldown="20")},
    },  # fmt: skip
    listed={"hero_a": "Bravo", "hero_c": "Alpha", "hero_off": "Off"},
    tokens={"blast:n": "Blast"},
)
SYNTHETIC = registry(lambda: DATA)


@contextmanager
def within(seconds: int) -> Generator[None]:
    """Fail, rather than hang the run, if the block takes more than ``seconds`` (Unix main thread)."""

    def expired(_signum: int, _frame: object) -> None:
        raise TimeoutError(f"still running after {seconds} s: an unbounded loop?")

    previous = signal.signal(signal.SIGALRM, expired)
    _ = signal.alarm(seconds)
    try:
        yield
    finally:
        _ = signal.alarm(0)
        _ = signal.signal(signal.SIGALRM, previous)
