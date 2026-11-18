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
from collections.abc import Mapping

from deadlock.abilities import SIGNATURE, bindings
from deadlock.ability_upgrades import upgrades
from deadlock.types import dig, is_str_mapping

from .timeline import Cycle, Hit
from .types import BadRequest

HEURISTIC = (
    "unverified heuristic: Damage lands at AbilityCastDelay, DPS ticks across the ability's duration, "
    "and the cast repeats every AbilityCooldown; not yet checked in-game"
)
_DAMAGE = ("Damage", "DPS")
_DURATIONS = ("AbilityDuration", "AbilityChannelTime")  # first positive wins
_TICKS = ("TickRate", "DPSTickInterval", "DamageInterval", "TickInterval", "Interval")  # first positive wins
_SPIRIT = "ETechPower"
_SPIRIT_CLASS = "scale_function_tech_damage"  # scales with spirit when it names no stat
_NUMBER = re.compile(r"-?(\d+\.?\d*|\.\d+)")

type Props = Mapping[str, object]


def cycle(
    heroes: Mapping[str, object], abilities: Mapping[str, object], hero: str, ability: str, spirit: float
) -> tuple[Cycle, tuple[str, ...]] | None:
    """``ability`` cast on cooldown by ``hero`` with ``spirit`` spirit power, and caveats on the model.

    ``heroes`` and ``abilities`` are the ``heroes.vdata`` and ``abilities.vdata``
    trees (see ``deadlock.gamedata``). ``None`` unless ``ability`` is bound to
    one of ``hero``'s signature slots (the ultimate included) and has a
    ``Damage`` or ``DPS`` property. The first note is ``HEURISTIC``; each
    further note names one factor present on the ability that the model leaves
    out or reads unusually. A zero-damage hit is dropped, so a cycle may have
    no hits.

    A read field that isn't a plain number (``"0.1m"``, a per-level list like
    ``"40 30 20"``) raises ``BadRequest``: the model can't say what it means.
    """
    if (hero, ability) not in {(h, a) for h, slot, a in bindings(heroes) if slot.startswith(SIGNATURE)}:
        return None
    props = dig(abilities, ability, "m_mapAbilityProperties")
    assert is_str_mapping(props), ability
    if not any(name in props for name in _DAMAGE):
        return None
    notes = [HEURISTIC]
    delay = _number(props, ability, "AbilityCastDelay")
    hits: list[Hit] = []
    if "Damage" in props:
        damage = _scaled(props, ability, "Damage", spirit, notes)
        hits.extend([Hit(0.0, delay, damage, "Damage")] if damage else [])
    if "DPS" in props:
        hits.extend(_ticks(props, ability, delay, _scaled(props, ability, "DPS", spirit, notes), notes))
    cooldown = _number(props, ability, "AbilityCooldown")
    if cooldown <= 0:
        notes.append("AbilityCooldown is 0: shown as a single cast")
    notes.extend(_unmodeled(abilities, ability, props))
    return Cycle(hits=tuple(hits), period=cooldown if cooldown > 0 else None, downtime=_downtime(hits, cooldown, notes)), tuple(notes)


def _downtime(hits: list[Hit], cooldown: float, notes: list[str]) -> float:
    """The cooldown left after the last land; 0, with a note, when the damage outlasts it."""
    if cooldown <= 0:
        return 0.0
    last = max((h.land for h in hits), default=0.0)
    if last > cooldown:
        notes.append(f"damage outlasts the cooldown ({last:g}s > {cooldown:g}s): casts on cooldown overlap, no downtime")
        return 0.0
    else:
        return cooldown - last


def _scaled(props: Props, ability: str, name: str, spirit: float, notes: list[str]) -> float:
    """``name``'s value plus its spirit scaling; a note if it scales with another stat instead."""
    base = _number(props, ability, name)
    scale = dig(props, name, "m_subclassScaleFunction")
    factor = dig(scale, "m_flStatScale")
    if factor is None:
        return base
    assert isinstance(factor, (int, float)) and not isinstance(factor, bool), (ability, name, factor)
    stat = dig(scale, "m_eSpecificStatScaleType")
    if stat == _SPIRIT or (stat is None and dig(scale, "_class") == _SPIRIT_CLASS):
        return base + factor * spirit
    notes.append(f"{name} scales with {stat or dig(scale, '_class') or 'an unnamed stat'} (x{factor:g}), not modeled")
    return base


def _ticks(props: Props, ability: str, delay: float, dps: float, notes: list[str]) -> list[Hit]:
    """``dps`` as ticks landing every interval from ``delay``, each triggered at the previous land.

    Ticks are whole intervals that fit the duration; a remainder is dropped.
    """
    duration_field = next((f for f in _DURATIONS if _number(props, ability, f, 0) > 0), None)
    tick_field = next((f for f in _TICKS if _number(props, ability, f, 0) > 0), None)
    if duration_field is None:
        others = sorted(k for k in props if k.endswith("Duration") and k not in _DURATIONS and _positive(props[k]))
        notes.append(
            f"DPS {dps:g}/s not modeled: {' and '.join(_DURATIONS)} are 0"
            + (f"; its duration may be one of {', '.join(others)}" if others else "")
        )
        return []
    if tick_field is None:
        notes.append(f"DPS {dps:g}/s not modeled: no tick interval (none of {', '.join(_TICKS)})")
        return []
    duration = _number(props, ability, duration_field)
    interval = _number(props, ability, tick_field)
    if (duration_field, tick_field) != (_DURATIONS[0], _TICKS[0]):
        notes.append(f"DPS ticks every {tick_field} ({interval:g}s) for {duration_field} ({duration:g}s)")
    count = int(duration / interval + 1e-9)
    if not dps:
        return []
    return [
        Hit(delay + i * interval if i else 0.0, delay + (i + 1) * interval, dps * interval, f"DPS tick {i + 1}")
        for i in range(count)
    ]


def _unmodeled(abilities: Mapping[str, object], ability: str, props: Props) -> list[str]:
    """One note per factor present on ``ability`` that the model ignores."""
    notes: list[str] = []
    charges = _number(props, ability, "AbilityCharges", 0)
    if charges > 0:
        between = _number(props, ability, "AbilityCooldownBetweenCharge", 0)
        notes.append(f"charges not modeled, one cast per cooldown shown: AbilityCharges {charges:g}, recharge {between:g}s")
    ups = upgrades(abilities, {ability})
    if ups:
        tiers = ", ".join(f"T{u.tier} {u.property} {u.bonus}" for u in ups)
        notes.append(f"upgrades not modeled, base values shown: {tiers}")
    for name, prop in props.items():
        if name not in _DAMAGE and dig(prop, "m_bIsAbilityDamageProperty") is True:
            notes.append(f"{name} {dig(prop, 'm_strValue')} not read: damage this model leaves out")
    return notes


def _number(props: Props, ability: str, name: str, default: float | None = None) -> float:
    """``name``'s ``m_strValue`` as a number; ``default`` if absent, when given."""
    if name not in props and default is not None:
        return default
    value = dig(props, name, "m_strValue")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str) and _NUMBER.fullmatch(value):
        return float(value)
    raise BadRequest(f"{ability}: {name} is {value!r}, not a number this model can read")


def _positive(prop: object) -> bool:
    value = dig(prop, "m_strValue")
    return _NUMBER.fullmatch(str(value)) is not None and float(str(value)) > 0
