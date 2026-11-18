"""DPS numbers a player can check in-game, computed from a damage ``Cycle``.

Each ``Measure`` is one number with its unit and a ``check``: one sentence a
player can follow in the sandbox to read or time the same value. Labels and
checks use the words of the source's kind (a clip and its reload, a cast and
its cooldown, a swing) and never another kind's. A measure that is undefined
for its input (no period, no hit, ``hp`` not reached) is left out, never
reported as 0.
"""

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import assert_never

from .timeline import Cycle, Hit, landed_by
from .types import Kind

DPS = "damage/s"
DEFAULT_PERIODS = 2  # cycles shown when the horizon is not given
ONE_SHOT_HORIZON = 10.0  # seconds, for a cycle that happens once


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


def horizon_used(cycle: Cycle, seconds: float | None = None, cycles: float | None = None) -> float:
    """The window, in seconds: ``seconds``, or ``cycles`` periods, or by default ``DEFAULT_PERIODS`` periods.

    A one-shot has no period, so ``cycles`` leaves it at ``ONE_SHOT_HORIZON``.
    """
    assert seconds is None or cycles is None, (seconds, cycles)
    if seconds is not None:
        return seconds
    elif cycle.period is None:
        return ONE_SHOT_HORIZON
    else:
        return (DEFAULT_PERIODS if cycles is None else cycles) * cycle.period


def measures(
    cycle: Cycle, horizon: float, hp: float | None = None, *, kind: Kind, card_dps: float | None = None
) -> list[Measure]:
    """``time_to_kill``, ``card_dps``, then per-cycle rates, then totals over ``[0, horizon)`` seconds.

    - ``time_to_kill``: ``kill_time``, inside the horizon or past it. Needs
      ``hp``, and a cycle that reaches it.
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
    return [*_kill(cycle, hp, words), *card, *_rates(cycle, words), *_totals(landed, horizon, words)]


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


def _kill(cycle: Cycle, hp: float | None, words: _Words) -> list[Measure]:
    land = None if hp is None else kill_time(cycle, hp)
    if hp is None or land is None:
        return []  # no hp, or never reached
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


def kill_time(cycle: Cycle, hp: float) -> float | None:
    """When cumulative landed damage first reaches ``hp``, however many cycles out; ``None`` if it never does.

    The time is the land ``timeline.repeat`` gives that hit, found without
    unrolling the cycles before it.
    """
    if cycle.period is None:
        return _kill_land(sorted(cycle.hits, key=lambda h: h.land), hp)
    period = cycle.period
    if sum(h.damage for h in cycle.hits) <= 0:
        return None

    def dealt(t: float) -> float:
        return sum(h.damage * _landed_by(h.land, period, t) for h in cycle.hits)

    # Cumulative damage only rises at a land, so the kill is the earliest land
    # of some hit, in the first cycle where that land has reached ``hp``.
    return min(_first(lambda n, land=h.land: dealt(n * period + land) >= hp) * period + h.land for h in cycle.hits)


def _landed_by(land: float, period: float, t: float) -> int:
    """How many repeats of a hit landing at ``land`` into its cycle have landed by ``t``, inclusive."""
    n = max(0, math.floor((t - land) / period) + 1)
    while n > 0 and (n - 1) * period + land > t:  # float rounding: compare as ``repeat`` computes
        n -= 1
    while n * period + land <= t:
        n += 1
    return n


def _first(reached: Callable[[int], bool]) -> int:
    """The least ``n >= 0`` that is ``reached``, which is monotone and true for some ``n``."""
    hi = 1
    while not reached(hi):
        hi *= 2
    lo = 0
    while lo < hi:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if reached(mid) else (mid + 1, hi)
    return lo
