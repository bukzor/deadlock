"""DPS numbers a player can check in-game, computed from a damage ``Cycle``.

Each ``Measure`` is one number with its unit and a ``check``: an instruction a
player can follow to read or time the same value in-game. A measure that is
undefined for its input (no period, no hit, ``hp`` not reached) is left out,
never reported as 0.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from .timeline import Cycle, Hit, landed_by

DPS = "damage/s"


@dataclass(frozen=True)
class Measure:
    name: str  # stable identifier
    label: str  # player-facing wording
    value: float
    unit: str
    check: str  # how to verify ``value`` in-game


def measures(cycle: Cycle, horizon: float, hp: float | None = None) -> list[Measure]:
    """Per-cycle rates, then totals over ``[0, horizon)`` seconds, the card's number first.

    - ``uptime_dps``: a cycle's damage over its period less its downtime: the
      DPS while the source is dealing damage. For a gun, the stat panel's DPS.
      Needs a period longer than its downtime, and a cycle of more than one
      hit (one hit over its land time is not a rate).
    - ``steady_dps``: a cycle's damage over its whole period. Needs a period.
    - ``cycle_damage``: a cycle's damage.
    - ``total_damage``, ``average_dps``: damage landed before ``horizon``.
    - ``first_land``: when the first damage lands. Needs a hit by ``horizon``.
    - ``time_to_kill``: when cumulative landed damage first reaches ``hp``.
      Needs ``hp``, reached by ``horizon``.

    Totals count a hit when it lands, not when it is triggered.
    """
    assert horizon > 0, horizon
    assert hp is None or hp > 0, hp
    landed = sorted(landed_by(cycle, horizon), key=lambda h: h.land)
    return [*_rates(cycle), *_totals(landed, horizon), *_kill(landed, hp)]


def _rates(cycle: Cycle) -> list[Measure]:
    damage = sum(h.damage for h in cycle.hits)
    per_cycle = Measure(
        "cycle_damage",
        "Damage per cycle",
        damage,
        "damage",
        "In the sandbox, deal one cycle (a clip, a swing, a cast) to the training dummy and read the total damage.",
    )
    if cycle.period is None:
        return [per_cycle]
    assert cycle.downtime <= cycle.period, (cycle.downtime, cycle.period)
    steady = Measure(
        "steady_dps",
        "DPS incl. reload/cooldown",
        damage / cycle.period,
        DPS,
        "Not shown in-game. In the sandbox, attack the training dummy nonstop, every reload and cooldown included, "
        + "for several cycles; divide the damage dealt by the stopwatch time from the first trigger.",
    )
    if cycle.period > cycle.downtime and len(cycle.hits) != 1:
        uptime = Measure(
            "uptime_dps",
            "DPS while active (≈ stat panel for guns)",
            damage / (cycle.period - cycle.downtime),
            DPS,
            "In the sandbox, deal one cycle (a clip, a swing, a cast) to the training dummy; "
            + "divide its damage by the stopwatch time from the first trigger until its downtime starts.",
        )
        return [uptime, steady, per_cycle]
    else:
        return [steady, per_cycle]  # no active time, or one hit: no uptime rate


def _totals(landed: Sequence[Hit], horizon: float) -> list[Measure]:
    total = sum(h.damage for h in landed)
    over = f"in the first {horizon:g} s by stopwatch from the first trigger"
    found = [
        Measure("total_damage", f"Damage in the first {horizon:g} s", total, "damage", f"Damage dealt to the sandbox training dummy {over}."),
        Measure("average_dps", f"DPS over the first {horizon:g} s", total / horizon, DPS, f"Damage dealt to the training dummy {over}, ÷ {horizon:g}."),
    ]
    if landed:
        check = "Stopwatch from the first trigger to the first damage number on the training dummy."
        found.append(Measure("first_land", "Time to first damage", landed[0].land, "s", check))
    return found


def _kill(landed: Sequence[Hit], hp: float | None) -> list[Measure]:
    if hp is None:
        return []
    total = 0.0
    for hit in landed:
        total += hit.damage
        if total >= hp:
            check = f"Stopwatch from the first trigger until the training dummy's health bar has lost {hp:g} HP."
            return [Measure("time_to_kill", f"Time to deal {hp:g} damage", hit.land, "s", check)]
    return []  # hp not reached within the horizon
