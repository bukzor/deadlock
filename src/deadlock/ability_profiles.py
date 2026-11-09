"""Recompile ``ability_profiles.tsv`` — the weapon profiles of live heroes' bound abilities — from data.

Source: ``data/gamedata.json/scripts/{heroes,abilities}.json``.
Heroes bind abilities to slots via ``m_mapBoundAbilities``. Guns are abilities
too (``EAbilityType_Weapon``), bound to ``ESlot_Weapon_Primary`` /
``ESlot_Weapon_Secondary``. Any bound ability may carry ``m_mapWeaponInfos``, a
map of named profiles (``primary``, ``fakegun``, ``scrap``, ...) holding bullet
stats in ``scripts/abilities.vdata``. This table resolves that join for the live
roster; it is the per-profile child of ``abilities.tsv``, sharing its
``hero``/``slot``/``ability`` columns.

Scope is ``deadlock.abilities.bindings`` — the live roster, without the
``hero_base`` template — so every row's ``(hero, slot, ability)`` is a row of
``abilities.tsv``.

One row per ``(hero, slot, ability, profile)`` whose profile sets at least one
stat below (most bound abilities' profiles set none — movement, melee,
innates), sorted, in raw weapon units. A stat the profile doesn't set is blank.

- ``damage``  — ``m_flBulletDamage`` per pellet.
- ``bullets`` — ``m_iBullets``, pellets per shot (>1 for shotgun-like weapons).
- ``burst``   — ``m_iBurstShotCount``, shots per trigger pull.
- ``cycle``   — ``m_flCycleTime``, seconds.
- ``intra``   — ``m_flIntraBurstCycleTime``, seconds (raw: inert when burst is 1).
- ``clip``    — ``m_iClipSize``.
- ``reload``  — ``m_reloadDuration``, seconds (per shell on single-bullet reloaders).
- ``range``   — ``m_flRange``.

Derived, for guns (``Weapon_*`` slots) only — the table's value-add. The
formulas and their in-game evidence are in ``docs/dev/mechanics.kb/``
(``gun-fire-rate.md``, ``gun-sustained-dps.md``):

- ``bps``  — shots per second, the UI's "bullets per second".
- ``dps``  — damage per second until reload, the UI's "DPS".
- ``sdps`` — sustained: a full clip's damage over the time to fire it plus the
  reload (reads ``m_iAmmoConsumedPerShot`` and single-bullet reload fields too).

Ability profiles get none: their bullet damage is usually a 0 placeholder, the
real damage living in the ability's own properties.

Every live hero's ``Weapon_Primary`` gun must define all base fields in its
``primary`` profile; that invariant is asserted so a missing field or dangling
weapon fails loudly.

    python -m deadlock.ability_profiles abilities.json < heroes.json
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from . import gamedata
from .abilities import bindings
from .types import dig, is_str_mapping

_GUN_SLOT = "Weapon_Primary"
_GUN_SLOTS = "Weapon_"
_GUN_PROFILE = "primary"
_FIELDS = {
    "damage": "m_flBulletDamage",
    "bullets": "m_iBullets",
    "burst": "m_iBurstShotCount",
    "cycle": "m_flCycleTime",
    "intra": "m_flIntraBurstCycleTime",
    "clip": "m_iClipSize",
    "reload": "m_reloadDuration",
    "range": "m_flRange",
}
_AMMO_PER_SHOT = "m_iAmmoConsumedPerShot"
_RELOAD_SINGLE = "m_bReloadSingleBullets"
_RELOAD_SINGLE_DELAY = "m_flReloadSingleBulletsInitialDelay"


@dataclass(frozen=True)
class Profile:
    """One emitted ``ability_profiles.tsv`` row: one weapon profile of a live hero's bound ability."""

    hero: str
    slot: str
    ability: str
    profile: str
    damage: float | None = None
    bullets: int | None = None
    burst: int | None = None
    cycle: float | None = None
    intra: float | None = None
    bps: float | None = None
    dps: float | None = None
    clip: int | None = None
    reload: float | None = None
    sdps: float | None = None
    range: float | None = None


def profiles(heroes: Mapping[str, object], abilities: Mapping[str, object]) -> list[Profile]:
    """Live heroes' bound weapon profiles joined to their stats, with derived DPS; sorted.

    ``heroes`` and ``abilities`` are the nested trees of ``heroes.vdata`` and
    ``abilities.vdata`` (see ``deadlock.gamedata``).
    """
    result = [row for hero, slot, ability in bindings(heroes) for row in _rows(hero, slot, ability, abilities)]
    return sorted(result, key=lambda p: (p.hero, p.slot, p.ability, p.profile))


def _rows(hero: str, slot: str, ability: str, abilities: Mapping[str, object]) -> list[Profile]:
    """One bound ability's rows: one per weapon profile that sets a stat."""
    infos = dig(abilities, ability, "m_mapWeaponInfos")
    if slot == _GUN_SLOT:
        assert is_str_mapping(infos) and _GUN_PROFILE in infos, (hero, ability)
        _require_all_fields(hero, ability, infos[_GUN_PROFILE])
    elif not is_str_mapping(infos):
        return []
    rows = (_row(hero, slot, ability, profile, stats) for profile, stats in infos.items())
    return [row for row in rows if row is not None]


def _require_all_fields(hero: str, ability: str, stats: object) -> None:
    assert is_str_mapping(stats), (hero, ability)
    for key in _FIELDS.values():
        assert key in stats, (hero, ability, key)


def _row(hero: str, slot: str, ability: str, profile: str, stats: object) -> Profile | None:
    assert is_str_mapping(stats), (hero, ability, profile)
    v = {name: _num(stats[key]) for name, key in _FIELDS.items() if key in stats}
    if not v:
        return None
    bps, dps, sdps = _gun_rates(v, stats) if slot.startswith(_GUN_SLOTS) else (None, None, None)
    return Profile(
        hero, slot, ability, profile,
        damage=v.get("damage"), bullets=_int(v.get("bullets")), burst=_int(v.get("burst")),
        cycle=v.get("cycle"), intra=v.get("intra"), bps=bps, dps=dps,
        clip=_int(v.get("clip")), reload=v.get("reload"), sdps=sdps, range=v.get("range"),
    )  # fmt: skip


def _gun_rates(v: Mapping[str, float], stats: Mapping[str, object]) -> tuple[float | None, float | None, float | None]:
    """``(bps, dps, sdps)``; see ``docs/dev/mechanics.kb/gun-*.md``. Blank when inputs are missing."""
    if not {"damage", "bullets", "burst", "cycle", "intra"} <= v.keys():
        return None, None, None
    burst = v["burst"]
    intra = v["intra"] if burst > 1 else 0.0  # the game ignores intra on single-shot guns
    bps = burst / (v["cycle"] + burst * intra)
    per_shot = v["damage"] * v["bullets"]
    if not {"clip", "reload"} <= v.keys():
        return round(bps, 2), round(per_shot * bps, 1), None
    shots = v["clip"] / _num(stats.get(_AMMO_PER_SHOT, 1))
    reload = v["reload"]
    if stats.get(_RELOAD_SINGLE, False) is True:
        reload = _num(stats.get(_RELOAD_SINGLE_DELAY, 0)) + v["clip"] * reload
    sdps = per_shot * shots / (shots / bps + reload)
    return round(bps, 2), round(per_shot * bps, 1), round(sdps, 1)


def render(rows: Iterable[Profile]) -> str:
    """Render profiles as a tab-separated table with a header line; unset stats are blank."""
    body = "".join(
        "\t".join(
            (
                p.hero,
                p.slot,
                p.ability,
                p.profile,
                _fmt(p.damage),
                _blank_or(p.bullets),
                _blank_or(p.burst),
                _fmt(p.cycle),
                _fmt(p.intra),
                _blank_or(p.bps),
                _blank_or(p.dps),
                _blank_or(p.clip),
                _fmt(p.reload),
                _blank_or(p.sdps),
                _fmt(p.range),
            )
        )
        + "\n"
        for p in rows
    )
    header = "hero\tslot\tability\tprofile\tdamage\tbullets\tburst\tcycle\tintra\tbps\tdps\tclip\treload\tsdps\trange\n"
    return header + body


def _num(value: object) -> float:
    assert isinstance(value, (int, float, str)) and not isinstance(value, bool), value
    return float(value)


def _int(value: float | None) -> int | None:
    return None if value is None else int(value)


def _fmt(value: float | None) -> str:
    """Render a float without a trailing ``.0`` for whole numbers; ``None`` as blank."""
    if value is None:
        return ""
    return str(int(value)) if value == int(value) else str(value)


def _blank_or(value: object) -> str:
    return "" if value is None else str(value)


def main(argv: list[str]) -> None:
    [abilities_source] = argv[1:]
    heroes = gamedata.load(sys.stdin)
    with Path(abilities_source).open() as defs_file:
        abilities = gamedata.load(defs_file)
    _ = sys.stdout.write(render(profiles(heroes, abilities)))


if __name__ == "__main__":
    main(sys.argv)
