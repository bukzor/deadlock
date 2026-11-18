"""DPS numbers a player can check in-game, computed from a damage ``Cycle``.

Each ``Measure`` is one number with its unit and a ``check``: an instruction a
player can follow to read or time the same value in-game. A measure that is
undefined for its input (no period, no hit, ``hp`` not reached) is left out,
never reported as 0.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from .timeline import Cycle, Hit, repeat

DPS = "damage/s"


@dataclass(frozen=True)
class Measure:
    name: str
    value: float
    unit: str
    check: str  # how to verify ``value`` in-game


def measures(cycle: Cycle, horizon: float, hp: float | None = None) -> list[Measure]:
    """Per-cycle rates, then totals over ``[0, horizon]`` seconds.

    - ``uptime_dps``: a cycle's damage over the time not spent reloading; for a
      gun, the stat panel's DPS. Needs a period longer than its reload.
    - ``steady_dps``: a cycle's damage over its whole period. Needs a period.
    - ``total_damage``, ``average_dps``: damage landed by ``horizon``.
    - ``first_land``: when the first damage lands. Needs a hit by ``horizon``.
    - ``time_to_kill``: when cumulative landed damage first reaches ``hp``.
      Needs ``hp``, reached by ``horizon``.

    Totals count a hit when it lands, not when it is triggered.
    """
    assert horizon > 0, horizon
    assert hp is None or hp > 0, hp
    landed = sorted((h for h in repeat(cycle, horizon) if h.land <= horizon), key=lambda h: h.land)
    return [*_rates(cycle), *_totals(landed, horizon), *_kill(landed, hp)]


def _rates(cycle: Cycle) -> list[Measure]:
    if cycle.period is None:
        return []
    assert cycle.reload <= cycle.period, (cycle.reload, cycle.period)
    damage = sum(h.damage for h in cycle.hits)
    steady = Measure(
        "steady_dps",
        damage / cycle.period,
        DPS,
        "Not shown in-game. In the sandbox, attack the training dummy nonstop, reloads included, "
        + "for several cycles; divide the damage dealt by the stopwatch time from the first trigger.",
    )
    if cycle.period > cycle.reload:
        uptime = Measure(
            "uptime_dps",
            damage / (cycle.period - cycle.reload),
            DPS,
            "For a gun, the DPS on the hero's stat panel (weapon). Otherwise, empty one clip or "
            + "cycle into the sandbox training dummy; divide its damage by the stopwatch time spent firing.",
        )
        return [uptime, steady]
    else:
        return [steady]  # all reload: no firing time to divide by


def _totals(landed: Sequence[Hit], horizon: float) -> list[Measure]:
    total = sum(h.damage for h in landed)
    over = f"in the first {horizon:g} s by stopwatch from the first trigger"
    found = [
        Measure("total_damage", total, "damage", f"Damage dealt to the sandbox training dummy {over}."),
        Measure("average_dps", total / horizon, DPS, f"Damage dealt to the training dummy {over}, ÷ {horizon:g}."),
    ]
    if landed:
        check = "Stopwatch from the first trigger to the first damage number on the training dummy."
        found.append(Measure("first_land", landed[0].land, "s", check))
    return found


def _kill(landed: Sequence[Hit], hp: float | None) -> list[Measure]:
    if hp is None:
        return []
    total = 0.0
    for hit in landed:
        total += hit.damage
        if total >= hp:
            check = f"Stopwatch from the first trigger until the training dummy's health bar has lost {hp:g} HP."
            return [Measure("time_to_kill", hit.land, "s", check)]
    return []  # hp not reached within the horizon
