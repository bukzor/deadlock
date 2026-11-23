"""A hero's signature or ultimate ability, as a damage ``Cycle`` (the design's "Cast" source).

The model, an unverified heuristic: a cast at t=0 lands its ``Damage`` after
``AbilityCastDelay``; its ``DPS`` then ticks every tick interval across its
duration, each tick triggered at the previous tick's land (the first at the
cast), so the ticks tile the duration; the whole repeats every
``AbilityCooldown`` (once, if that is 0). The cycle's downtime is the cooldown
left after the last land, 0 when the damage outlasts the cooldown.
Damage and DPS that scale with ``ETechPower`` add ``m_flStatScale × spirit``.
Each property is ``m_mapAbilityProperties.X.m_strValue``.

Survey of the live roster's bound signatures and ultimates (build of
2026-11-11), which the fallbacks and notes below are fitted to:

- 184 bound; 99 have ``Damage`` and/or ``DPS`` (75 only Damage, 16 only DPS,
  8 both) and yield a cycle; the other 85 return ``None``. All 99 carry
  upgrades (one note each); 19 have charges; 3 have a cooldown of 0.
- Of the 24 with DPS, 14 tick: 8 across ``AbilityDuration`` at ``TickRate``,
  6 across ``AbilityChannelTime`` (3 of those at an interval named otherwise:
  ``DamageInterval``, ``Interval``, ``TickInterval``). 9 have neither duration,
  keeping it in an ability-specific property (``BurnDuration``, ...), and 1
  has no tick interval; those 10 are noted, not modeled. 14 cycles have no
  hits at spirit 0.
- Of the 107 Damage/DPS properties, 47 scale with ``ETechPower`` and 36 are
  ``scale_function_tech_damage`` naming no stat, read as spirit too. 13 scale
  with another stat (``ELightMeleeDamage``, ``EBaseWeaponDamageIncrease``,
  ``ELevelUpBoons``, ``EStatsCount``, one unnamed), noted, not modeled; 11
  don't scale.
- 24 other properties flagged ``m_bIsAbilityDamageProperty`` (``ImpactDamage``,
  ``MaxDPS``, ...) sit on the 99; each gets a note.
- Every field read is numeric, as a number or a numeric string.
"""

import re

from bukzor_deadlock.abilities import SIGNATURE, bindings
from bukzor_deadlock.ability_upgrades import upgrades
from bukzor_deadlock_lookup.entities import Ability, NotANumber
from bukzor_deadlock_lookup.lookup import Lookup

from . import BadInput
from .timeline import Cycle, Hit

HEURISTIC = (
    "Not yet checked in-game: damage lands after the cast delay, damage over time ticks through the ability's "
    "duration, and the cast repeats every cooldown."
)
# A note's rank: the lower, the more it moves the numbers. Notes are returned in rank order.
LEFT_OUT, UPGRADES, CHARGES, OVERLAP, NO_COOLDOWN, UNVERIFIED = range(6)
type Notes = list[tuple[int, str]]
_DAMAGE = ("Damage", "DPS")
_DURATIONS = ("AbilityDuration", "AbilityChannelTime")  # first positive wins
_TICKS = ("TickRate", "DPSTickInterval", "DamageInterval", "TickInterval", "Interval")  # first positive wins
_NAMES = {"Damage": "Damage", "DPS": "Damage over time"}  # property: player-facing name


def cycle(game: Lookup, hero: str, ability: str, spirit: float) -> tuple[Cycle, tuple[str, ...]] | None:
    """``ability`` cast on cooldown by ``hero`` with ``spirit`` spirit power, and caveats on the model.

    ``None`` unless ``ability`` is bound to
    one of ``hero``'s signature slots (the ultimate included) and has a
    ``Damage`` or ``DPS`` property. The first note is ``HEURISTIC``; each
    further note names one factor present on the ability that the model leaves
    out or reads unusually, naming a property by its in-game label
    (``Lookup.label``), else in words. A
    zero-damage hit is dropped, so a cycle may have no hits.

    A read field that is missing or isn't a plain number (``"0.1m"``, a
    per-level list like ``"40 30 20"``) raises ``BadInput``: the model can't
    say what it means.
    """
    if (hero, ability) not in {(h, a) for h, slot, a in bindings(game.heroes) if slot.startswith(SIGNATURE)}:
        return None
    cast = game.ability(ability)
    if not any(name in cast.properties for name in _DAMAGE):
        return None
    notes: Notes = [(UNVERIFIED, HEURISTIC)]
    delay = _number(cast, "AbilityCastDelay")
    hits: list[Hit] = []
    if "Damage" in cast.properties:
        damage = _scaled(cast, "Damage", spirit, notes)
        hits.extend([Hit(0.0, delay, damage, "Damage")] if damage else [])
    if "DPS" in cast.properties:
        hits.extend(_ticks(cast, delay, _scaled(cast, "DPS", spirit, notes), notes))
    cooldown = _number(cast, "AbilityCooldown")
    if cooldown <= 0:
        notes.append((NO_COOLDOWN, "This ability has no cooldown: a single cast is shown."))
    notes.extend(_unmodeled(game, cast))
    cycle = Cycle(hits=tuple(hits), period=cooldown if cooldown > 0 else None, downtime=_downtime(hits, cooldown, notes))
    return cycle, tuple(text for _, text in sorted(notes, key=lambda note: note[0]))


def card_dps(ability: Ability, spirit: float) -> float | None:
    """``ability``'s ``DPS`` property with ``spirit`` spirit power: the DPS its card shows; ``None`` without one.

    Scaling by a stat other than spirit is left out, as in ``cycle``, which notes it.
    """
    return _scaled(ability, "DPS", spirit, []) if "DPS" in ability.properties else None


def _downtime(hits: list[Hit], cooldown: float, notes: Notes) -> float:
    """The cooldown left after the last land; 0, with a note, when the damage outlasts it."""
    if cooldown <= 0:
        return 0.0
    last = max((h.land for h in hits), default=0.0)
    if last > cooldown:
        notes.append((OVERLAP, f"The damage outlasts the cooldown ({last:g} s > {cooldown:g} s): casts overlap, so no downtime is shown."))
        return 0.0
    else:
        return cooldown - last


def _scaled(ability: Ability, name: str, spirit: float, notes: Notes) -> float:
    """``name``'s value plus its spirit scaling; a note if it scales with another stat instead."""
    base = _number(ability, name)
    scale = ability.scale(name)
    if scale is None:
        return base
    if scale.spirit:
        return base + scale.factor * spirit
    what = _humanize(scale.stat) if scale.stat else "an unnamed stat"
    notes.append((LEFT_OUT, f"{_NAMES.get(name, name)} also scales with {what} (×{scale.factor:g}); that is not included."))
    return base


def _ticks(ability: Ability, delay: float, dps: float, notes: Notes) -> list[Hit]:
    """``dps`` as ticks landing every interval from ``delay``, each triggered at the previous land.

    Ticks are whole intervals that fit the duration; a remainder is dropped.
    """
    duration_field = next((f for f in _DURATIONS if _number(ability, f, 0) > 0), None)
    tick_field = next((f for f in _TICKS if _number(ability, f, 0) > 0), None)
    if duration_field is None:
        notes.append((LEFT_OUT, f"Damage over time ({dps:g}/s) is not included: its duration is not in the data."))
        return []
    if tick_field is None:
        notes.append((LEFT_OUT, f"Damage over time ({dps:g}/s) is not included: its tick interval is not in the data."))
        return []
    duration = _number(ability, duration_field)
    interval = _number(ability, tick_field)
    count = int(duration / interval + 1e-9)
    if not dps:
        return []
    return [
        Hit(delay + i * interval if i else 0.0, delay + (i + 1) * interval, dps * interval, f"DPS tick {i + 1}")
        for i in range(count)
    ]


def _unmodeled(game: Lookup, ability: Ability) -> Notes:
    """One note per factor present on ``ability`` that the model ignores."""
    notes: Notes = []

    def label(prop: str) -> str:
        return game.label(ability, prop) or _humanize(prop)

    charges = _number(ability, "AbilityCharges", 0)
    if charges > 0:
        between = _number(ability, "AbilityCooldownBetweenCharge", 0)
        notes.append((CHARGES, f"Charges are not included: one cast per cooldown is shown (the ability has {charges:g}, one back every {between:g} s)."))
    ups = upgrades(game.abilities, {ability.key})
    if ups:
        tiers = ", ".join(f"T{u.tier} {label(u.property)} {u.bonus}" for u in ups)
        notes.append((UPGRADES, f"Upgrades not included: {tiers}."))
    for name in ability.damage_properties():
        if name not in _DAMAGE:
            notes.append((LEFT_OUT, f"Extra damage not included: {label(name)} {ability.text(name)}."))
    return notes


def _number(ability: Ability, name: str, default: float | None = None) -> float:
    """``Ability.value``, a missing or unreadable value as ``BadInput``."""
    try:
        return ability.value(name, default)
    except KeyError:
        raise BadInput(f"{ability.key}: {name} is missing, and this model needs it") from None
    except NotANumber as bad:
        raise BadInput(f"{bad} this model can read") from None


def _humanize(name: str) -> str:
    """An engine name in words: ``AbilityCooldown`` is ``cooldown``, ``ETechPower`` is ``tech power``."""
    bare = re.sub(r"^(E(?=[A-Z][a-z])|Ability(?=[A-Z]))", "", name)
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", bare).lower()
