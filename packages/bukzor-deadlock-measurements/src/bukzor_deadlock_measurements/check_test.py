import dataclasses

import pytest
from bukzor_deadlock_lookup.load import load

from .check import check
from .load import ReadingsError, load_all
from .records import Dummy, Experiment, Scenario


def swap(experiment: Experiment, scenario: str, old: str, new: str) -> Experiment:
    """The experiment with `old` replaced by `new` in the named scenario."""
    (dummy,) = experiment.dummies
    scenarios = tuple(
        (
            dataclasses.replace(s, items=tuple(new if i == old else i for i in s.items))
            if s.name == scenario
            else s
        )
        for s in dummy.scenarios
    )
    return dataclasses.replace(
        experiment, dummies=(dataclasses.replace(dummy, scenarios=scenarios),)
    )


def only_dummy(e: Experiment) -> Dummy:
    (dummy,) = e.dummies
    return dummy


def scenario_named(e: Experiment, name: str) -> Scenario:
    return next(s for s in only_dummy(e).scenarios if s.name == name)


class DescribeCheck:
    def it_accepts_the_real_experiments(self):
        lookup = load()
        for experiment in load_all():
            check(experiment, lookup)

    def it_names_the_scenario_and_near_items_for_a_misspelling(self):
        (crimson,) = load_all()
        bad = swap(crimson, "tankbuster", "Tankbuster", "Tankbustre")
        with pytest.raises(ReadingsError, match=r"'tankbuster'.*Tankbuster"):
            check(bad, load())

    def it_rejects_an_unequal_spirit_swap(self):
        (crimson,) = load_all()
        # Rapid Recharge (3200) for Tankbuster's slot-mate Refresher (6400).
        bad = swap(crimson, "tankbuster", "Refresher", "Rapid Recharge")
        with pytest.raises(
            ReadingsError, match=r"'tankbuster'.*cost 12800.*cost 16000"
        ):
            check(bad, load())

    def it_ignores_a_non_spirit_swap(self):
        (crimson,) = load_all()
        ok = swap(crimson, "baseline", "Healbane", "Mystic Shot")
        check(ok, load())

    def it_needs_a_baseline(self):
        (crimson,) = load_all()
        bad = swap(crimson, "baseline", "x", "x")
        (dummy,) = bad.dummies
        renamed = tuple(
            dataclasses.replace(s, name="other") for s in dummy.scenarios[:1]
        )
        bad = dataclasses.replace(
            bad, dummies=(dataclasses.replace(dummy, scenarios=renamed),)
        )
        with pytest.raises(ReadingsError, match="no 'baseline'"):
            check(bad, load())
