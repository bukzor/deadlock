"""A hero's light or heavy melee as a repeating ``Cycle``: one swing per cooldown.

Melee is offered as two pseudo-abilities, ``melee_light`` and ``melee_heavy``.
The damage is the hero's own ``m_mapStartingStats.E{Light,Heavy}MeleeDamage``.
The period is ``m_mapAttacks.EAttackType_{Light,Heavy}.m_flCooldownOnHit`` of
the melee ability the hero binds to ``ESlot_Weapon_Melee``: the attack timings
live on that ability, not on the hero.

No ``_base`` resolution is needed: the compiled data materializes every starting
stat on every hero (see ``bukzor_deadlock.heroes``), and melee abilities carry the full
``m_mapAttacks`` with no ``_base`` of their own.

Every swing is assumed to hit. A miss can cost a longer cooldown (heavy: 1.3 s
against 1.0 s on a hit); a note says so whenever the two differ. The wind-up is
not in the data, so it is the caller's ``windup``, and a note says that too.
The hero's level adds to the damage (``boons``).
"""

from collections.abc import Mapping

from bukzor_deadlock_lookup.lookup import Lookup

from . import BadInput
from .boons import NONE, Boons, spirit_note
from .timeline import Cycle, Hit

LIGHT = "melee_light"
HEAVY = "melee_heavy"
NAMES = {LIGHT: "Light Melee", HEAVY: "Heavy Melee"}  # the game's own words for the two melee stats

_MELEE_SLOT = "Weapon_Melee"
# pseudo-ability: (label, hero damage stat, attack type on the melee ability)
_ATTACKS: Mapping[str, tuple[str, str, str]] = {
    LIGHT: ("light melee", "ELightMeleeDamage", "EAttackType_Light"),
    HEAVY: ("heavy melee", "EHeavyMeleeDamage", "EAttackType_Heavy"),
}


def cycle(
    game: Lookup,
    hero: str,
    ability: str,
    windup: float,
    boons: Boons = NONE,
) -> tuple[Cycle, tuple[str, ...]] | None:
    """``hero``'s ``ability`` as ``(Cycle, notes)``; ``None`` unless ``ability`` is ``LIGHT`` or ``HEAVY``.

    ``boons`` is what the hero's level adds.
    The cycle is one hit, triggered at 0 and landing at ``windup`` seconds.
    Raises ``BadInput`` for a negative ``windup``, and ``Lookup.hero``'s
    ``Unresolved`` for an unknown hero.
    """
    if ability not in _ATTACKS:
        return None
    if windup < 0:
        raise BadInput(f"windup must be >= 0, got {windup}")
    label, stat, attack_type = _ATTACKS[ability]
    attacker = game.hero(hero)
    damage = attacker.stat(stat) + (boons.light_melee if ability == LIGHT else boons.heavy_melee)
    attack = game.ability(attacker.kit[_MELEE_SLOT]).attack(attack_type)
    on_hit, on_miss = attack.on_hit, attack.on_miss
    notes = spirit_note(attacker, stat, f"{label.capitalize()} damage", boons.spirit)
    if on_miss != on_hit:
        notes.append(f"Every swing is assumed to hit: the cooldown is {on_hit:g} s on a hit, {on_miss:g} s on a miss.")
    notes.append(f"The swing's wind-up is not in the data: {windup:g} s is assumed (set it with the wind-up field).")
    cycle = Cycle(hits=(Hit(0.0, windup, damage, label),), period=on_hit)
    return cycle, tuple(notes)
