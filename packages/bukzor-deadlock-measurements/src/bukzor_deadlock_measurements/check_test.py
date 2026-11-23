import dataclasses

import pytest
from bukzor_deadlock_lookup.load import load

from .check import ReadingsError, check
from .load import load_all
from .records import ExperimentalSetup


def first_setup() -> ExperimentalSetup:
    return load_all()["crimson_slash"][0]


def swap(setup: ExperimentalSetup, scenario: str, old: str, new: str):
    """The setup with `old` replaced by `new` in the named scenario's items."""
    scenarios = tuple(
        (
            dataclasses.replace(s, items=tuple(new if i == old else i for i in s.items))
            if s.name == scenario
            else s
        )
        for s in setup.scenarios
    )
    return dataclasses.replace(setup, scenarios=scenarios)


class DescribeCheck:
    def it_accepts_the_real_experiments(self):
        lookup = load()
        for name, setups in load_all().items():
            check(name, setups, lookup)

    def it_names_the_scenario_and_near_items_for_a_misspelling(self):
        bad = swap(first_setup(), "tankbuster", "Tankbuster", "Tankbustre")
        with pytest.raises(
            ReadingsError, match=r"^x.SETUPS\[0\] \('tankbuster'\).*Tankbuster"
        ):
            check("x", (bad,), load())

    def it_names_a_misspelled_setup_item(self):
        setup = first_setup()
        bad = dataclasses.replace(setup, items=("Healbane", "Mystic Shott"))
        with pytest.raises(ReadingsError, match=r"'baseline'.*Mystic Shot"):
            check("x", (bad,), load())

    def it_rejects_an_unequal_spirit_swap(self):
        # Rapid Recharge (3200) for Tankbuster's slot-mate Refresher (6400).
        bad = swap(first_setup(), "tankbuster", "Refresher", "Rapid Recharge")
        with pytest.raises(
            ReadingsError, match=r"'tankbuster'.*cost 12800.*cost 16000"
        ):
            check("x", (bad,), load())

    def it_ignores_a_non_spirit_swap(self):
        setup = first_setup()
        ok = dataclasses.replace(
            setup,
            items=tuple("Mystic Shot" if i == "Healbane" else i for i in setup.items),
        )
        check("x", (ok,), load())

    def it_needs_a_baseline(self):
        setup = first_setup()
        renamed = tuple(
            dataclasses.replace(s, name="other") for s in setup.scenarios[:1]
        )
        bad = dataclasses.replace(setup, scenarios=renamed)
        with pytest.raises(ReadingsError, match="no 'baseline'"):
            check("x", (bad,), load())
