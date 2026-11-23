"""A hero's gun as a ``Cycle``: one clip fired as fast as the gun fires, then its reload.

A hero's gun is the ability ``bukzor_deadlock.abilities.bindings`` binds to its
``Weapon_Primary`` slot, read from that ability's ``primary`` weapon profile.
That ability key is the one the gun answers to. ``Weapon_Secondary`` weapons
are not guns here.

The base stats are ``bukzor_deadlock.ability_profiles.profiles``' row for that
binding. Shots per clip and the reload from empty re-read the same fields that
``ability_profiles`` reads for its ``sdps``. The formulas are in
``docs/dev/mechanics.kb/gun-*.md``.

Bullet travel is ``distance / speed``. The speed is the constant
``m_BulletSpeedCurve`` when the profile has one (a curve that varies is not
modeled, and raises). Otherwise it is ``m_flBulletSpeed``, which every live
gun sets. Without either, travel is 0 and a note says so. Engine units are
inches: speeds and ranges in those units convert to round m/s and m (20669.3
is 525 m/s, 669.291 is 17 m).
"""

from bukzor_deadlock.ability_profiles import Profile, profiles
from bukzor_deadlock_lookup.entities import Weapon
from bukzor_deadlock_lookup.lookup import Lookup

from .boons import NONE, Boons, spirit_note
from .timeline import Cycle, Gun, gun_cycle

SLOT = "Weapon_Primary"
PROFILE = "primary"
METERS_PER_UNIT = 0.0254


def cycle(
    game: Lookup,
    hero: str,
    ability: str,
    distance: float = 0.0,
    boons: Boons = NONE,
) -> tuple[Cycle, list[str]] | None:
    """``hero``'s gun as a cycle, with notes on what the model leaves out; ``None`` unless ``ability`` is that gun.

    ``distance`` is to the target, in meters.
    ``boons`` is what the hero's level adds.
    """
    rows = [p for p in profiles(game.heroes, game.abilities) if (p.hero, p.slot, p.ability, p.profile) == (hero, SLOT, ability, PROFILE)]
    if not rows:
        return None
    [row] = rows
    stats = game.ability(ability).weapon(PROFILE)
    reload, reload_notes = _reload(row, stats)
    speed, speed_notes = _speed(stats)
    travel = 0.0 if speed is None else distance / speed
    gun = Gun(
        damage=_given(row.damage) + boons.bullet, pellets=_given(row.bullets), burst=_given(row.burst), cycle=_given(row.cycle),
        intra=_given(row.intra), shots=_shots(_given(row.clip), stats), reload=reload, travel=travel,
    )  # fmt: skip
    spirit = spirit_note(game.hero(hero), "EBulletDamage", "Bullet damage", boons.spirit)
    return gun_cycle(gun), _falloff(stats, distance) + spirit + reload_notes + speed_notes  # biggest effect first


def _shots(clip: int, stats: Weapon) -> int:
    ammo = int(stats.ammo_per_shot)
    assert clip % ammo == 0, (clip, ammo)
    return clip // ammo


def _reload(row: Profile, stats: Weapon) -> tuple[float, list[str]]:
    """Seconds to refill an empty clip."""
    per = _given(row.reload)
    if not stats.reload_single:
        return per, []
    delay = stats.reload_single_delay
    reload = delay + _given(row.clip) * per
    note = f"This gun reloads one bullet at a time; a full reload from empty is taken as {reload:g} s ({delay:g} s delay + {row.clip} × {per:g} s). Not checked in-game."
    return reload, [note]


def _speed(stats: Weapon) -> tuple[float | None, list[str]]:
    """Bullet speed in m/s, ``None`` if unknown."""
    flat_speed = None if stats.bullet_speed is None else stats.bullet_speed * METERS_PER_UNIT
    if stats.speed_curve is None:
        if flat_speed is None:
            return None, ["Bullet speed is not in the data: hits land the instant you fire, with no travel time."]
        return flat_speed, []
    ys = set(stats.speed_curve)
    if len(ys) != 1:
        raise NotImplementedError(f"m_BulletSpeedCurve varies, which is not modeled: {sorted(ys)}")
    [y] = ys
    speed = y * METERS_PER_UNIT
    if flat_speed is None or flat_speed == speed:
        return speed, []
    note = f"The data gives two bullet speeds, {speed:g} m/s and {flat_speed:g} m/s; the {speed:g} m/s one is used. Not checked in-game."
    return speed, [note]


def _falloff(stats: Weapon, distance: float) -> list[str]:
    start = stats.falloff_start
    if start is None or distance <= start * METERS_PER_UNIT:
        return []
    return [f"Damage falls off beyond {start * METERS_PER_UNIT:.3g} m; the falloff is not included."]


def _given[T](value: T | None) -> T:
    assert value is not None
    return value
