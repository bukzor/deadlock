from collections.abc import Iterable, Mapping

import pytest
from deadlock import gamedata, paths
from deadlock.abilities import bindings
from pytest import approx

from . import guns, melee
from .measures import Measure, horizon_used, measures
from .timeline import Cycle, Gun, Hit, gun_cycle
from .types import Kind

# In-game hero stats, level 0, no items, build 6854: docs/dev/mechanics.kb/gun-fire-rate.md
SEVEN = Gun(damage=10.8, pellets=1, burst=3, cycle=0.2625, intra=0.084, shots=30, reload=2.35, travel=0.0)
PAIGE = Gun(damage=32, pellets=1, burst=1, cycle=0.5, intra=0.1, shots=10, reload=2.0, travel=0.0)
ABRAMS = Gun(damage=3.78, pellets=9, burst=1, cycle=0.63, intra=0.0, shots=9, reload=3.88, travel=0.0)

SWING = Cycle(hits=(Hit(0, 0.25, 10, "swing"),), period=1.0)
NUKE = Cycle(hits=(Hit(0, 0.5, 100, "nuke"), Hit(0, 1.5, 5, "tick")), period=None)


CAST = Cycle(hits=(Hit(0, 0.5, 30, "a"), Hit(0.5, 2.0, 30, "b")), period=10.0, downtime=8.0)
COMBO = Cycle(hits=(Hit(0, 0.25, 10, "jab"), Hit(0.25, 0.5, 30, "hook")), period=1.0)  # no downtime
KINDS: tuple[Kind, ...] = ("gun", "melee", "cast")
OTHER_KINDS_WORDS: Mapping[Kind, tuple[str, ...]] = {
    "gun": ("cast", "cooldown", "swing", "melee"),
    "melee": ("gun", "clip", "reload", "shot", "cast", "cooldown", "weapon"),
    "cast": ("gun", "clip", "reload", "shot", "swing", "melee", "weapon"),
}


def by_name(found: Iterable[Measure]) -> Mapping[str, Measure]:
    return {m.name: m for m in found}


def values(
    cycle: Cycle, horizon: float = 10, hp: float | None = None, kind: Kind = "gun", card_dps: float | None = None
) -> Mapping[str, float]:
    return {name: m.value for name, m in by_name(measures(cycle, horizon, hp, kind=kind, card_dps=card_dps)).items()}


class DescribeMeasures:
    def it_reproduces_the_ui_dps_as_uptime_dps(self):
        assert values(gun_cycle(SEVEN))["uptime_dps"] == approx(63, abs=0.5)
        assert values(gun_cycle(PAIGE))["uptime_dps"] == approx(64, abs=0.5)
        assert values(gun_cycle(ABRAMS))["uptime_dps"] == approx(54, abs=0.5)

    def it_spreads_a_cycles_damage_over_its_period_as_steady_dps(self):
        assert values(gun_cycle(PAIGE))["steady_dps"] == approx(320 / 7)

    def it_answers_time_to_kill_first_then_the_card_comparable_dps(self):
        found = measures(CAST, horizon=10, hp=50, kind="cast", card_dps=20)
        assert [m.name for m in found] == [
            "time_to_kill",
            "card_dps",
            "uptime_dps",
            "steady_dps",
            "cycle_damage",
            "total_damage",
            "first_land",
        ]
        assert all(m.label and m.unit and m.check for m in found), found

    def it_divides_uptime_dps_by_the_period_less_its_downtime(self):
        assert (values(CAST)["uptime_dps"], values(CAST)["steady_dps"]) == approx((30, 6))

    def it_states_the_horizon_and_hp_in_the_checks(self):
        found = by_name(measures(SWING, horizon=7.5, hp=40, kind="melee"))
        assert "7.5 s" in found["total_damage"].check
        assert "40 HP" in found["time_to_kill"].check

    @pytest.mark.parametrize("kind", KINDS)
    def it_words_no_label_or_check_for_another_kind(self, kind: Kind):
        cycle = Cycle(hits=CAST.hits, period=CAST.period, downtime=CAST.downtime)
        found = measures(cycle, horizon=10, hp=50, kind=kind, card_dps=20 if kind == "cast" else None)
        words = " ".join(f"{m.label} {m.check}" for m in found).lower()
        assert [w for w in OTHER_KINDS_WORDS[kind] if w in words] == [], words

    @pytest.mark.parametrize("kind", KINDS)
    def it_keeps_each_check_to_one_sentence(self, kind: Kind):
        found = measures(CAST, horizon=10, hp=50, kind=kind, card_dps=20 if kind == "cast" else None)
        assert [m.check for m in found if m.check.count(".") != 1 or len(m.check) > 120] == []

    @pytest.mark.parametrize(
        ("kind", "labels"),
        [
            ("gun", {"uptime_dps": "DPS while firing (weapon panel)", "steady_dps": "DPS incl. reloads", "cycle_damage": "Damage per clip"}),
            ("cast", {"uptime_dps": "DPS from cast to last damage", "steady_dps": "DPS incl. cooldown", "cycle_damage": "Damage per cast"}),
            ("melee", {"uptime_dps": "DPS while swinging", "steady_dps": "DPS", "cycle_damage": "Damage per swing"}),
        ],
    )  # fmt: skip
    def it_labels_the_rates_in_the_kinds_words(self, kind: Kind, labels: Mapping[str, str]):
        found = by_name(measures(CAST, horizon=10, kind=kind))
        assert {name: found[name].label for name in labels} == labels

    def it_labels_the_totals_alike_for_every_kind(self):
        found = by_name(measures(CAST, horizon=10.0, hp=50.0, kind="cast", card_dps=20))
        assert {name: found[name].label for name in ("time_to_kill", "card_dps", "total_damage", "first_land")} == {
            "time_to_kill": "Time to deal 50 damage",
            "card_dps": "DPS on the ability card",
            "total_damage": "Damage in the first 10 s",
            "first_land": "Time to first damage",
        }

    class WhenTheCycleHasNoPeriod:
        def it_omits_uptime_and_steady_dps(self):
            assert values(NUKE).keys() == {"cycle_damage", "total_damage", "first_land"}

    class WhenTheCycleHasOneHit:
        def it_omits_uptime_dps_but_keeps_steady_dps(self):
            found = values(Cycle(hits=SWING.hits, period=1.0, downtime=0.5))
            assert ("uptime_dps" in found, found["steady_dps"]) == (False, 10)

    class WhenTheCycleHasNoDowntime:
        def it_omits_uptime_dps_which_would_equal_steady_dps(self):
            assert ("uptime_dps" in values(COMBO, kind="melee"), values(COMBO, kind="melee")["steady_dps"]) == (False, 40)

    class WhenThePeriodIsAllDowntime:
        def it_omits_uptime_dps_but_keeps_steady_dps(self):
            found = values(Cycle(hits=(Hit(0, 0, 50, "a"), Hit(0, 0, 50, "b")), period=2.0, downtime=2.0))
            assert ("uptime_dps" in found, found["steady_dps"]) == (False, 50)

    class WhenACardDpsIsGiven:
        def it_reports_it_as_card_dps(self):
            assert values(CAST, kind="cast", card_dps=23)["card_dps"] == 23

        def it_omits_card_dps_otherwise(self):
            assert "card_dps" not in values(CAST, kind="cast")

    class WhenSummingOverTheHorizon:
        def it_counts_only_hits_landed_by_the_horizon(self):
            assert values(SWING, horizon=2.1)["total_damage"] == 20

        def it_reports_the_first_land(self):
            assert values(NUKE)["first_land"] == 0.5

        def it_excludes_a_hit_landing_at_the_horizon(self):
            assert values(SWING, horizon=1.25)["total_damage"] == 10

        def it_has_no_average_dps_which_whole_periods_make_steady_dps(self):
            assert "average_dps" not in values(SWING, horizon=2)

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
            assert values(Cycle(hits=(), period=1.0, downtime=1.0), hp=1) == {
                "steady_dps": 0,
                "cycle_damage": 0,
                "total_damage": 0,
            }


class DescribeHorizonUsed:
    def it_is_two_periods(self):
        assert horizon_used(SWING) == 2

    def it_is_10_s_for_a_one_shot(self):
        assert horizon_used(NUKE) == 10

    class WhenHpIsGiven:
        def it_stretches_to_whole_periods_past_the_time_to_kill(self):
            assert horizon_used(SWING, hp=50) == 5  # the 5th swing lands at 4.25

        def it_includes_a_kill_landing_on_a_period_boundary(self):
            on_beat = Cycle(hits=(Hit(0, 0, 10, "beat"),), period=0.7)  # the 4th beat lands at 3 * 0.7 == 2.0999999999999996
            horizon = horizon_used(on_beat, hp=40)
            assert values(on_beat, horizon, hp=40).get("time_to_kill") == approx(2.1), horizon

        def it_never_shrinks_below_two_periods(self):
            assert horizon_used(SWING, hp=5) == 2

        def it_stretches_a_one_shot_by_whole_seconds(self):
            slow = Cycle(hits=(Hit(0, 12.4, 100, "late"),), period=None)
            assert (horizon_used(slow, hp=100), horizon_used(NUKE, hp=100)) == (13, 10)

        def it_stops_at_120_s(self):
            weekly = Cycle(hits=SWING.hits, period=7.0)  # the 18th swing lands at 119.25, in the 18th period of 7 s
            assert (horizon_used(weekly, hp=180), horizon_used(SWING, hp=10_000)) == (120, 120)

        def it_keeps_two_periods_beyond_120_s(self):
            assert horizon_used(Cycle(hits=SWING.hits, period=90.0), hp=10_000) == 180

    class WhenAHorizonIsAsked:
        def it_is_the_asked_horizon_without_hp(self):
            assert horizon_used(SWING, asked=3.3) == 3.3

        def it_zooms_out_by_whole_periods_to_the_time_to_kill(self):
            assert (horizon_used(SWING, hp=50, asked=1.5), horizon_used(SWING, hp=5, asked=0.5)) == (5, 1)

        def it_never_zooms_in(self):
            assert horizon_used(SWING, hp=50, asked=7.5) == 7.5

        def it_zooms_out_to_120_s_when_hp_is_out_of_reach(self):
            assert (horizon_used(SWING, hp=10_000, asked=3), horizon_used(SWING, hp=10_000, asked=200)) == (120, 200)

def _load(name: str) -> Mapping[str, object]:
    path = paths.data_dir() / "gamedata.json/scripts" / name
    if not path.exists():
        pytest.skip(f"no local data: {path} (build it with `redo` at the repo root)")
    with path.open() as file:
        return gamedata.load(file)


class DescribeTwoPeriods:
    """The default horizon is 2 periods (see ``queries.timeline``), which must hold exactly 2 cycles."""

    def it_holds_two_cycles_for_every_live_heros_gun_and_melee(self):
        heroes, abilities = _load("heroes.json"), _load("abilities.json")
        cycles = [
            (hero, ability, guns.cycle(heroes, abilities, hero, ability))
            for hero, slot, ability in bindings(heroes)
            if slot == "Weapon_Primary"
        ]
        cycles += [
            (hero, ability, melee.cycle(heroes, abilities, hero, ability, 0.25))
            for hero in {hero for hero, _, _ in bindings(heroes)}
            for ability in (melee.LIGHT, melee.HEAVY)
        ]
        assert len(cycles) > 2
        for hero, ability, result in cycles:
            assert result is not None, (hero, ability)
            cycle, _ = result
            assert cycle.period is not None, (hero, ability)
            found = values(cycle, horizon=2 * cycle.period)
            assert found["total_damage"] == approx(2 * found["cycle_damage"]), (hero, ability)
