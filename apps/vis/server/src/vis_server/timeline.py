"""Damage over time: when each hit is triggered, and when it lands.

A ``Hit`` is one damage instance. ``trigger`` is when the input that caused it
happened (trigger pull, swing, cast); ``land`` is when the damage applies. The
gap between them is the wind-up: bullet travel, a swing's lead-in, a cast delay.

Every source is modeled as a ``Cycle``: the hits that follow one cycle start,
repeated every ``period`` seconds (a gun's clip plus its reload, a melee swing's
cooldown, a cast's cooldown). ``repeat`` unrolls a cycle onto a time axis.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, replace
from itertools import pairwise


@dataclass(frozen=True)
class Hit:
    trigger: float  # seconds
    land: float  # seconds
    damage: float
    label: str
    cycle: int = 0  # which repeat of its cycle, from 0


@dataclass(frozen=True)
class Cycle:
    hits: Sequence[Hit]  # sorted by trigger, relative to the cycle start
    period: float | None  # None: happens once
    downtime: float = 0.0  # seconds of each period spent dealing no damage

    def __post_init__(self) -> None:
        unsorted = [(a, b) for a, b in pairwise(self.hits) if a.trigger > b.trigger]
        assert not unsorted, unsorted


@dataclass(frozen=True)
class Gun:
    """A gun's primary-fire stats, effective values (see ``docs/dev/mechanics.kb/gun-*.md``)."""

    damage: float  # per pellet
    pellets: int
    burst: int  # shots per trigger pull
    cycle: float  # seconds after a burst
    intra: float  # seconds after each shot of a burst
    shots: int  # per clip
    reload: float  # seconds to refill an empty clip
    travel: float  # seconds from shot to impact


def gun_cycle(gun: Gun) -> Cycle:
    """One clip emptied as fast as the gun fires, then reloaded."""
    intra = gun.intra if gun.burst > 1 else 0.0  # the game ignores intra on single-shot guns
    period = gun.cycle + gun.burst * intra
    per_shot = gun.damage * gun.pellets
    hits: list[Hit] = []
    for shot in range(gun.shots):
        t = (shot // gun.burst) * period + (shot % gun.burst) * intra
        hits.append(Hit(t, t + gun.travel, per_shot, f"shot {shot + 1}"))
    firing = gun.shots * period / gun.burst
    return Cycle(hits=tuple(hits), period=firing + gun.reload, downtime=gun.reload)


def repeat(cycle: Cycle, horizon: float) -> Iterator[Hit]:
    """Every hit whose trigger falls within ``[0, horizon]``, in trigger order."""
    assert cycle.period is None or cycle.period > 0, cycle.period
    n = 0
    while True:
        start = 0.0 if cycle.period is None else n * cycle.period
        if start > horizon:
            return
        for hit in cycle.hits:
            if start + hit.trigger > horizon:
                break
            yield replace(hit, trigger=start + hit.trigger, land=start + hit.land, cycle=n)
        if cycle.period is None:
            return
        n += 1
