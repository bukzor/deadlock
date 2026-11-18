"""DPS numbers a player can check in-game, computed from a damage ``Cycle``.

Each ``Measure`` is one number with its unit and a ``check``: one sentence a
player can follow in the sandbox to read or time the same value. Labels and
checks use the words of the source's kind (a clip and its reload, a cast and
its cooldown, a swing) and never another kind's. A measure that is undefined
for its input (no period, no hit, ``hp`` not reached) is left out, never
reported as 0.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import assert_never

from .timeline import Cycle, Hit, landed_by
from .types import Kind

DPS = "damage/s"
DEFAULT_PERIODS = 2  # cycles shown when the horizon is not given
ONE_SHOT_HORIZON = 10.0  # seconds, for a cycle that happens once
KILL_HORIZON = 120.0  # seconds: how far the horizon zooms out to reach ``hp``


@dataclass(frozen=True)
class Measure:
    name: str  # stable identifier
    label: str  # player-facing wording
    value: float
    unit: str
    check: str  # how to verify ``value`` in-game


@dataclass(frozen=True)
class _Words:
    """A kind's labels, and the clauses its checks are built from."""

    per_cycle: str  # label of ``cycle_damage``
    steady: str  # label of ``steady_dps``
    uptime: str  # label of ``uptime_dps``
    uptime_check: str
    once: str  # one cycle at the dummy
    nonstop: str  # cycle after cycle at the dummy
    start: str  # the input the stopwatch starts on


def _words(kind: Kind) -> _Words:
    match kind:
        case "gun":
            return _Words(
                "Damage per clip", "DPS incl. reloads", "DPS while firing (weapon panel)",
                "Read the DPS on the weapon's stat panel.",
                "Empty one clip into the training dummy", "Fire at the training dummy nonstop, reloads included",
                "the first shot",
            )  # fmt: skip
        case "cast":
            return _Words(
                "Damage per cast", "DPS incl. cooldown", "DPS from cast to last damage",
                "Cast once at the training dummy; divide its damage by the stopwatch time from the cast to the last damage number.",
                "Cast once at the training dummy", "Cast at the training dummy each time the cooldown ends",
                "the cast",
            )  # fmt: skip
        case "melee":
            return _Words(
                "Damage per swing", "DPS", "DPS while swinging",
                "Swing at the training dummy nonstop; divide the damage by the stopwatch time.",
                "Swing once at the training dummy", "Swing at the training dummy nonstop",
                "the first swing",
            )  # fmt: skip
        case _:
            assert_never(kind)


def horizon_used(cycle: Cycle, hp: float | None = None, asked: float | None = None) -> float:
    """The ``asked`` horizon, or by default ``DEFAULT_PERIODS`` periods (``ONE_SHOT_HORIZON`` for a one-shot).

    With ``hp``, it zooms out, never in: by whole periods (whole seconds for a
    one-shot) until the hit that reaches ``hp`` lands inside it, up to
    ``KILL_HORIZON``, and to ``KILL_HORIZON`` when ``hp`` is not reached by
    then. A horizon already past ``KILL_HORIZON`` is kept.
    """
    unit, default = (1.0, ONE_SHOT_HORIZON) if cycle.period is None else (cycle.period, DEFAULT_PERIODS * cycle.period)
    base = default if asked is None else asked
    if hp is None:
        return base
    land = _kill_land(sorted(landed_by(cycle, max(base, KILL_HORIZON)), key=lambda h: h.land), hp)
    if land is None:
        return max(base, KILL_HORIZON)
    units = math.floor(land / unit) + 1
    while units * unit <= land:  # float rounding: the window is half-open
        units += 1
    return max(base, min(KILL_HORIZON, units * unit))


def measures(
    cycle: Cycle, horizon: float, hp: float | None = None, *, kind: Kind, card_dps: float | None = None
) -> list[Measure]:
    """``time_to_kill``, ``card_dps``, then per-cycle rates, then totals over ``[0, horizon)`` seconds.

    - ``time_to_kill``: when cumulative landed damage first reaches ``hp``.
      Needs ``hp``, reached by ``horizon``.
    - ``card_dps``: ``card_dps``, the ability card's DPS, when given.
    - ``uptime_dps``: a cycle's damage over its period less its downtime: the
      DPS while the source is dealing damage. For a gun, the stat panel's DPS.
      Needs downtime (else it equals ``steady_dps``), a period longer than
      it, and a cycle of more than one hit (one hit over its land time is not
      a rate).
    - ``steady_dps``: a cycle's damage over its whole period. Needs a period.
    - ``cycle_damage``: a cycle's damage.
    - ``total_damage``: damage landed before ``horizon``.
    - ``first_land``: when the first damage lands. Needs a hit by ``horizon``.

    Totals count a hit when it lands, not when it is triggered.
    """
    assert horizon > 0, horizon
    assert hp is None or hp > 0, hp
    words = _words(kind)
    landed = sorted(landed_by(cycle, horizon), key=lambda h: h.land)
    card = [] if card_dps is None else [_card(card_dps)]
    return [*_kill(landed, hp, words), *card, *_rates(cycle, words), *_totals(landed, horizon, words)]


def _card(value: float) -> Measure:
    check = "Hover the ability in the sandbox at the same spirit power and read the DPS on its card."
    return Measure("card_dps", "DPS on the ability card", value, DPS, check)


def _rates(cycle: Cycle, words: _Words) -> list[Measure]:
    damage = sum(h.damage for h in cycle.hits)
    per_cycle = Measure("cycle_damage", words.per_cycle, damage, "damage", f"{words.once} and read the total damage.")
    if cycle.period is None:
        return [per_cycle]
    assert cycle.downtime <= cycle.period, (cycle.downtime, cycle.period)
    check = f"{words.nonstop}; divide the damage by the stopwatch time."
    steady = Measure("steady_dps", words.steady, damage / cycle.period, DPS, check)
    if 0 < cycle.downtime < cycle.period and len(cycle.hits) != 1:
        uptime = Measure("uptime_dps", words.uptime, damage / (cycle.period - cycle.downtime), DPS, words.uptime_check)
        return [uptime, steady, per_cycle]
    else:
        return [steady, per_cycle]  # no downtime, no active time, or one hit: no uptime rate


def _totals(landed: Sequence[Hit], horizon: float, words: _Words) -> list[Measure]:
    total = sum(h.damage for h in landed)
    check = f"{words.nonstop}; read the damage dealt in the first {horizon:g} s."
    found = [Measure("total_damage", f"Damage in the first {horizon:g} s", total, "damage", check)]
    if landed:
        check = f"{words.once}; stopwatch from {words.start} to the first damage number."
        found.append(Measure("first_land", "Time to first damage", landed[0].land, "s", check))
    return found


def _kill(landed: Sequence[Hit], hp: float | None, words: _Words) -> list[Measure]:
    land = None if hp is None else _kill_land(landed, hp)
    if hp is None or land is None:
        return []  # no hp, or not reached within the horizon
    check = f"{words.nonstop}; stopwatch from {words.start} until its health bar has lost {hp:g} HP."
    return [Measure("time_to_kill", f"Time to deal {hp:g} damage", land, "s", check)]


def _kill_land(landed: Sequence[Hit], hp: float) -> float | None:
    """The land of the hit, in land order, that brings cumulative damage to ``hp``; ``None`` if none does."""
    total = 0.0
    for hit in landed:
        total += hit.damage
        if total >= hp:
            return hit.land
    return None
