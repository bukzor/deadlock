"""What a hero's level adds to its stats, with no items: one boon per standard level-up.

A level is numbered as ``bukzor_deadlock.levels`` numbers it: game level − 1, so 0 is
the match start. Each game level after the first that sets
``m_bUseStandardUpgrade`` grants one boon, which adds the hero's
``m_mapStandardLevelUpUpgrades``. Heavy melee grows in proportion to light. The
formulas and their evidence: ``docs/dev/mechanics.kb/boons-per-level.md``.
"""

from dataclasses import dataclass

from bukzor_deadlock.levels import curves
from bukzor_deadlock_lookup.entities import Hero


@dataclass(frozen=True)
class Boons:
    """What a level's boons add to a hero's base stats."""

    count: int = 0
    bullet: float = 0.0  # bullet damage, per pellet
    light_melee: float = 0.0
    heavy_melee: float = 0.0
    spirit: float = 0.0  # spirit power


NONE = Boons()  # level 0


def last_level(hero: Hero) -> int:
    """``hero``'s highest level."""
    return max(curves({hero.key: hero.tree})[hero.key]) - 1


def at_level(hero: Hero, level: int) -> Boons:
    """What ``hero``'s boons add at ``level``, which must be from 0 to ``last_level``."""
    assert 0 <= level <= last_level(hero), (hero.key, level)
    count = sum(hero.grants_boon(game) for game in range(2, level + 2))
    light = count * hero.per_boon("MODIFIER_VALUE_BASE_MELEE_DAMAGE_FROM_LEVEL")
    ratio = hero.stat("EHeavyMeleeDamage") / hero.stat("ELightMeleeDamage")
    return Boons(
        count=count,
        bullet=count * hero.per_boon("MODIFIER_VALUE_BASE_BULLET_DAMAGE_FROM_LEVEL"),
        light_melee=light,
        heavy_melee=light * ratio,
        spirit=count * hero.per_boon("MODIFIER_VALUE_TECH_POWER"),
    )


def spirit_note(hero: Hero, stat: str, what: str, spirit: float) -> list[str]:
    """A note, when ``hero``'s ``stat`` (``what``, in player words) scales with spirit power and ``spirit`` is above 0."""
    scale = hero.scaling(stat)
    if spirit <= 0 or scale is None or not scale.spirit:
        return []
    return [f"{what} also grows with spirit power (×{scale.factor}; this level gives {spirit:g}): that is not included."]
