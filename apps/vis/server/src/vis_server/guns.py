"""A hero's gun as a ``Cycle``: one clip fired as fast as the gun fires, then its reload.

A hero's gun is the ability ``deadlock.abilities.bindings`` binds to its
``Weapon_Primary`` slot, read from that ability's ``primary`` weapon profile.
That ability key is the one the gun answers to. ``Weapon_Secondary`` weapons
are not guns here.

The base stats are ``deadlock.ability_profiles.profiles``' row for that
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

from collections.abc import Mapping

from deadlock.ability_profiles import Profile, profiles
from deadlock.types import dig, is_sequence, is_str_mapping

from .timeline import Cycle, Gun, gun_cycle

SLOT = "Weapon_Primary"
PROFILE = "primary"
METERS_PER_UNIT = 0.0254


def cycle(
    heroes: Mapping[str, object], abilities: Mapping[str, object], hero: str, ability: str, distance: float = 0.0
) -> tuple[Cycle, list[str]] | None:
    """``hero``'s gun as a cycle, with notes on what the model leaves out; ``None`` unless ``ability`` is that gun.

    ``heroes`` and ``abilities`` are the ``heroes.vdata`` and ``abilities.vdata``
    trees (see ``deadlock.gamedata``); ``distance`` is to the target, in meters.
    """
    rows = [p for p in profiles(heroes, abilities) if (p.hero, p.slot, p.ability, p.profile) == (hero, SLOT, ability, PROFILE)]
    if not rows:
        return None
    [row] = rows
    stats = dig(abilities, ability, "m_mapWeaponInfos", PROFILE)
    assert is_str_mapping(stats), (hero, ability)
    reload, reload_notes = _reload(row, stats)
    speed, speed_notes = _speed(stats)
    travel = 0.0 if speed is None else distance / speed
    gun = Gun(
        damage=_given(row.damage), pellets=_given(row.bullets), burst=_given(row.burst), cycle=_given(row.cycle),
        intra=_given(row.intra), shots=_shots(_given(row.clip), stats), reload=reload, travel=travel,
    )  # fmt: skip
    return gun_cycle(gun), _falloff(stats, distance) + reload_notes + speed_notes  # biggest effect first


def _shots(clip: int, stats: Mapping[str, object]) -> int:
    ammo = int(_num(stats.get("m_iAmmoConsumedPerShot", 1)))
    assert clip % ammo == 0, (clip, ammo)
    return clip // ammo


def _reload(row: Profile, stats: Mapping[str, object]) -> tuple[float, list[str]]:
    """Seconds to refill an empty clip."""
    per = _given(row.reload)
    if stats.get("m_bReloadSingleBullets", False) is not True:
        return per, []
    delay = _num(stats.get("m_flReloadSingleBulletsInitialDelay", 0))
    reload = delay + _given(row.clip) * per
    note = f"This gun reloads one bullet at a time; a full reload from empty is taken as {reload:g} s ({delay:g} s delay + {row.clip} × {per:g} s). Not checked in-game."
    return reload, [note]


def _speed(stats: Mapping[str, object]) -> tuple[float | None, list[str]]:
    """Bullet speed in m/s, ``None`` if unknown."""
    flat = stats.get("m_flBulletSpeed")
    flat_speed = None if flat is None else _num(flat) * METERS_PER_UNIT
    spline = dig(stats, "m_BulletSpeedCurve", "m_spline")
    if spline is None:
        if flat_speed is None:
            return None, ["Bullet speed is not in the data: hits land the instant you fire, with no travel time."]
        return flat_speed, []
    assert is_sequence(spline), spline
    ys = {_num(dig(point, "y")) for point in spline}
    if len(ys) != 1:
        raise NotImplementedError(f"m_BulletSpeedCurve varies, which is not modeled: {sorted(ys)}")
    [y] = ys
    speed = y * METERS_PER_UNIT
    if flat_speed is None or flat_speed == speed:
        return speed, []
    note = f"The data gives two bullet speeds, {speed:g} m/s and {flat_speed:g} m/s; the {speed:g} m/s one is used. Not checked in-game."
    return speed, [note]


def _falloff(stats: Mapping[str, object], distance: float) -> list[str]:
    start = stats.get("m_flDamageFalloffStartRange")
    if start is None or distance <= _num(start) * METERS_PER_UNIT:
        return []
    return [f"Damage falls off beyond {_num(start) * METERS_PER_UNIT:.3g} m; the falloff is not included."]


def _given[T](value: T | None) -> T:
    assert value is not None
    return value


def _num(value: object) -> float:
    assert isinstance(value, (int, float, str)) and not isinstance(value, bool), value
    return float(value)
