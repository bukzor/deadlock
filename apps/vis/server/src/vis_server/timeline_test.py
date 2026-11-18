from dataclasses import replace
from itertools import islice

from pytest import approx, raises

from .timeline import Cycle, Gun, Hit, gun_cycle, repeat

# In-game hero stats, level 0, no items, build 6854: docs/dev/mechanics.kb/gun-fire-rate.md
SEVEN = Gun(damage=10.8, pellets=1, burst=3, cycle=0.2625, intra=0.084, shots=30, reload=2.35, travel=0.0)
PAIGE = Gun(damage=32, pellets=1, burst=1, cycle=0.5, intra=0.1, shots=10, reload=2.0, travel=0.0)
ABRAMS = Gun(damage=3.78, pellets=9, burst=1, cycle=0.63, intra=0.0, shots=9, reload=3.88, travel=0.0)


def uptime_dps(cycle: Cycle) -> float:
    assert cycle.period is not None
    return sum(h.damage for h in cycle.hits) / (cycle.period - cycle.downtime)


class DescribeGunCycle:
    def it_spaces_a_burst_by_intra_then_cycle(self):
        triggers = [h.trigger for h in gun_cycle(SEVEN).hits[:4]]
        assert triggers == approx([0, 0.084, 0.168, 0.5145])

    def it_ignores_intra_on_a_single_shot_gun(self):
        triggers = [h.trigger for h in gun_cycle(PAIGE).hits[:2]]
        assert triggers == approx([0, 0.5])

    def it_reproduces_the_ui_dps(self):
        assert uptime_dps(gun_cycle(SEVEN)) == approx(63, abs=0.5)
        assert uptime_dps(gun_cycle(PAIGE)) == approx(64, abs=0.5)
        assert uptime_dps(gun_cycle(ABRAMS)) == approx(54, abs=0.5)

    def it_sums_pellets_into_one_hit_per_shot(self):
        assert gun_cycle(ABRAMS).hits[0].damage == approx(34.02)

    def it_reloads_after_the_clip(self):
        cycle = gun_cycle(PAIGE)
        assert (len(cycle.hits), cycle.period, cycle.downtime) == (10, approx(7.0), 2.0)

    def it_lands_after_the_travel_time(self):
        hit = gun_cycle(replace(PAIGE, travel=0.25)).hits[1]
        assert hit == Hit(trigger=0.5, land=0.75, damage=32, label="shot 2")


class DescribeCycle:
    def it_rejects_hits_out_of_trigger_order(self):
        with raises(AssertionError, match=r"trigger=1\.0.*trigger=0\.5"):
            _ = Cycle(hits=(Hit(0.0, 0.0, 1, "a"), Hit(1.0, 1.0, 1, "b"), Hit(0.5, 0.5, 1, "c")), period=2.0)

    def it_accepts_hits_sharing_a_trigger(self):
        _ = Cycle(hits=(Hit(0, 0.5, 1, "a"), Hit(0, 0.25, 1, "b")), period=None)


class DescribeRepeat:
    def it_repeats_the_cycle_until_the_horizon(self):
        cycle = Cycle(hits=(Hit(0, 0.25, 10, "swing"),), period=1.0)
        hits = list(repeat(cycle, horizon=2.5))
        assert [(h.trigger, h.land, h.label) for h in hits] == [
            (0, 0.25, "swing"),
            (1, 1.25, "swing"),
            (2, 2.25, "swing"),
        ]

    def it_numbers_repeats_in_the_cycle_field(self):
        cycle = Cycle(hits=(Hit(0, 0, 10, "swing"),), period=1.0)
        assert [h.cycle for h in repeat(cycle, horizon=1)] == [0, 1]

    def it_fires_once_without_a_period(self):
        cycle = Cycle(hits=(Hit(0, 0.5, 10, "nuke"), Hit(0, 1.5, 5, "tick")), period=None)
        hits = list(islice(repeat(cycle, horizon=60), 3))  # bounded, so a wrongful repeat fails rather than hangs
        assert [(h.trigger, h.land, h.label) for h in hits] == [(0, 0.5, "nuke"), (0, 1.5, "tick")]

    def it_stops_at_triggers_past_the_horizon(self):
        cycle = Cycle(hits=(Hit(0, 0, 1, "a"), Hit(0.9, 0.9, 1, "b")), period=1.0)
        assert [h.trigger for h in repeat(cycle, horizon=1.5)] == [0, 0.9, 1]

    def it_keeps_a_hit_triggered_within_the_horizon_that_lands_past_it(self):
        cycle = Cycle(hits=(Hit(0, 0.5, 1, "shot"),), period=1.0)
        assert [(h.trigger, h.land) for h in repeat(cycle, horizon=1.2)] == [(0, 0.5), (1, 1.5)]
