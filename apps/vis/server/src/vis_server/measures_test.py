from collections.abc import Iterable, Mapping

from pytest import approx

from .measures import Measure, measures
from .timeline import Cycle, Gun, Hit, gun_cycle

# In-game hero stats, level 0, no items, build 6854: docs/dev/mechanics.kb/gun-fire-rate.md
SEVEN = Gun(damage=10.8, pellets=1, burst=3, cycle=0.2625, intra=0.084, shots=30, reload=2.35, travel=0.0)
PAIGE = Gun(damage=32, pellets=1, burst=1, cycle=0.5, intra=0.1, shots=10, reload=2.0, travel=0.0)
ABRAMS = Gun(damage=3.78, pellets=9, burst=1, cycle=0.63, intra=0.0, shots=9, reload=3.88, travel=0.0)

SWING = Cycle(hits=(Hit(0, 0.25, 10, "swing"),), period=1.0)
NUKE = Cycle(hits=(Hit(0, 0.5, 100, "nuke"), Hit(0, 1.5, 5, "tick")), period=None)


def by_name(found: Iterable[Measure]) -> Mapping[str, Measure]:
    return {m.name: m for m in found}


def values(cycle: Cycle, horizon: float = 10, hp: float | None = None) -> Mapping[str, float]:
    return {name: m.value for name, m in by_name(measures(cycle, horizon, hp)).items()}


class DescribeMeasures:
    def it_reproduces_the_ui_dps_as_uptime_dps(self):
        assert values(gun_cycle(SEVEN))["uptime_dps"] == approx(63, abs=0.5)
        assert values(gun_cycle(PAIGE))["uptime_dps"] == approx(64, abs=0.5)
        assert values(gun_cycle(ABRAMS))["uptime_dps"] == approx(54, abs=0.5)

    def it_spreads_a_cycles_damage_over_its_period_as_steady_dps(self):
        assert values(gun_cycle(PAIGE))["steady_dps"] == approx(320 / 7)

    def it_gives_every_measure_a_unit_and_a_check(self):
        found = measures(gun_cycle(PAIGE), horizon=10, hp=100)
        assert [m.name for m in found] == [
            "uptime_dps",
            "steady_dps",
            "cycle_damage",
            "total_damage",
            "average_dps",
            "first_land",
            "time_to_kill",
        ]
        assert all(m.label and m.unit and m.check for m in found), found

    def it_checks_uptime_dps_the_same_way_for_every_source(self):
        gun = by_name(measures(gun_cycle(PAIGE), horizon=10))["uptime_dps"].check
        cast = Cycle(hits=(Hit(0, 0.5, 30, "a"), Hit(0.5, 2.0, 30, "b")), period=10.0, downtime=8.0)
        assert (by_name(measures(cast, horizon=10))["uptime_dps"].check, "gun" in gun) == (gun, False)

    def it_divides_uptime_dps_by_the_period_less_its_downtime(self):
        cast = Cycle(hits=(Hit(0, 0.5, 30, "a"), Hit(0.5, 2.0, 30, "b")), period=10.0, downtime=8.0)
        assert (values(cast)["uptime_dps"], values(cast)["steady_dps"]) == approx((30, 6))

    def it_states_the_horizon_and_hp_in_the_checks(self):
        found = by_name(measures(SWING, horizon=7.5, hp=40))
        assert "7.5 s" in found["total_damage"].check
        assert "40 HP" in found["time_to_kill"].check

    class WhenTheCycleHasNoPeriod:
        def it_omits_uptime_and_steady_dps(self):
            assert values(NUKE).keys() == {"cycle_damage", "total_damage", "average_dps", "first_land"}

    class WhenTheCycleHasOneHit:
        def it_omits_uptime_dps_but_keeps_steady_dps(self):
            assert ("uptime_dps" in values(SWING), values(SWING)["steady_dps"]) == (False, 10)

        def it_labels_each_measure_in_player_words(self):
            found = by_name(measures(gun_cycle(PAIGE), horizon=10.0, hp=50.0))
            assert {name: m.label for name, m in found.items()} == {
                "uptime_dps": "DPS while active (≈ stat panel for guns)",
                "steady_dps": "DPS incl. reload/cooldown",
                "cycle_damage": "Damage per cycle",
                "total_damage": "Damage in the first 10 s",
                "average_dps": "DPS over the first 10 s",
                "first_land": "Time to first damage",
                "time_to_kill": "Time to deal 50 damage",
            }

    class WhenThePeriodIsAllDowntime:
        def it_omits_uptime_dps_but_keeps_steady_dps(self):
            found = values(Cycle(hits=(Hit(0, 0, 50, "a"),), period=2.0, downtime=2.0))
            assert ("uptime_dps" in found, found["steady_dps"]) == (False, 25)

    class WhenSummingOverTheHorizon:
        def it_counts_only_hits_landed_by_the_horizon(self):
            assert values(SWING, horizon=2.1)["total_damage"] == 20

        def it_averages_the_landed_damage_over_the_horizon(self):
            assert values(SWING, horizon=2.5)["average_dps"] == approx(30 / 2.5)

        def it_reports_the_first_land(self):
            assert values(NUKE)["first_land"] == 0.5

    class WhenHpIsNotGiven:
        def it_omits_time_to_kill(self):
            assert "time_to_kill" not in values(SWING)

    class WhenHpIsGiven:
        def it_is_the_land_of_the_hit_that_reaches_hp(self):
            assert values(SWING, hp=30)["time_to_kill"] == 2.25

        def it_counts_hits_in_land_order(self):
            late_first = Cycle(hits=(Hit(0, 3, 50, "slow"), Hit(0.5, 1, 50, "fast")), period=None)
            assert values(late_first, hp=50)["time_to_kill"] == 1

        def it_omits_time_to_kill_when_the_horizon_ends_first(self):
            assert "time_to_kill" not in values(SWING, horizon=2.5, hp=31)

    class WhenThereAreNoHits:
        def it_reports_zero_damage_and_omits_what_needs_a_hit(self):
            assert values(Cycle(hits=(), period=1.0), hp=1) == {
                "uptime_dps": 0,
                "steady_dps": 0,
                "cycle_damage": 0,
                "total_damage": 0,
                "average_dps": 0,
            }
