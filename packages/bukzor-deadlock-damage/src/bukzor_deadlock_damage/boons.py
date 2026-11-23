"""What a hero's level adds to its stats, with no items: one boon per standard level-up.

A level is numbered as ``bukzor_deadlock.levels`` numbers it: game level − 1, so 0 is
the match start. Each game level after the first that sets
``m_bUseStandardUpgrade`` grants one boon, which adds the hero's
``m_mapStandardLevelUpUpgrades``. Heavy melee grows in proportion to light. The
formulas and their evidence: ``docs/dev/mechanics.kb/boons-per-level.md``.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from bukzor_deadlock.levels import curves
from bukzor_deadlock.types import dig, is_str_mapping

_PER_BOON = "m_mapStandardLevelUpUpgrades"


@dataclass(frozen=True)
class Boons:
    """What a level's boons add to a hero's base stats."""

    count: int = 0
    bullet: float = 0.0  # bullet damage, per pellet
    light_melee: float = 0.0
    heavy_melee: float = 0.0
    spirit: float = 0.0  # spirit power


NONE = Boons()  # level 0


def last_level(heroes: Mapping[str, object], hero: str) -> int:
    """``hero``'s highest level."""
    return max(_game_levels(heroes, hero)) - 1


def at_level(heroes: Mapping[str, object], hero: str, level: int) -> Boons:
    """What ``hero``'s boons add at ``level``, which must be from 0 to ``last_level``."""
    assert 0 <= level <= last_level(heroes, hero), (hero, level)
    standard = [dig(heroes, hero, "m_mapLevelInfo", str(game), "m_bUseStandardUpgrade") is True for game in range(2, level + 2)]
    count = sum(standard)
    light = count * _stat(heroes, hero, _PER_BOON, "MODIFIER_VALUE_BASE_MELEE_DAMAGE_FROM_LEVEL")
    ratio = _stat(heroes, hero, "m_mapStartingStats", "EHeavyMeleeDamage") / _stat(heroes, hero, "m_mapStartingStats", "ELightMeleeDamage")
    return Boons(
        count=count,
        bullet=count * _stat(heroes, hero, _PER_BOON, "MODIFIER_VALUE_BASE_BULLET_DAMAGE_FROM_LEVEL"),
        light_melee=light,
        heavy_melee=light * ratio,
        spirit=count * _stat(heroes, hero, _PER_BOON, "MODIFIER_VALUE_TECH_POWER"),
    )


def _game_levels(heroes: Mapping[str, object], hero: str) -> Mapping[int, object]:
    entity = heroes.get(hero)
    assert is_str_mapping(entity), hero
    return curves({hero: entity})[hero]


def _stat(heroes: Mapping[str, object], hero: str, group: str, name: str) -> float:
    value = dig(heroes, hero, group, name)
    assert isinstance(value, (int, float)) and not isinstance(value, bool), (hero, group, name, value)
    return float(value)


def spirit_note(heroes: Mapping[str, object], hero: str, stat: str, what: str, spirit: float) -> list[str]:
    """A note, when ``hero``'s ``stat`` (``what``, in player words) scales with spirit power and ``spirit`` is above 0."""
    scaling = dig(heroes, hero, "m_mapScalingStats", stat)
    if spirit <= 0 or dig(scaling, "eScalingStat") != "ETechPower":
        return []
    scale = dig(scaling, "flScale")
    return [f"{what} also grows with spirit power (×{scale}; this level gives {spirit:g}): that is not included."]
