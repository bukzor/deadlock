"""Check an experiment's item lists against the game data.

Readings are observations: nothing here replaces or defaults a recorded
number from the data, it only compares.
"""

from bukzor_deadlock_lookup.lookup import Lookup
from bukzor_deadlock_lookup.resolve import Unresolved

from .records import Experiment, Scenario

SPIRIT_SLOT = "Tech"  # the shop's spirit column
BASELINE = "baseline"


class ReadingsError(ValueError):
    pass


def spirit_cost(lookup: Lookup, where: str, scenario: Scenario) -> int:
    """Souls the scenario's spirit items cost in all; every name must resolve."""
    total = 0
    for name in scenario.items:
        try:
            item = lookup.item(name)
        except Unresolved as e:
            raise ReadingsError(f"{where} ({scenario.name!r}): {e}") from e
        if item.slot == SPIRIT_SLOT:
            total += item.cost
    return total


def check(experiment: Experiment, lookup: Lookup) -> None:
    """Raise `ReadingsError` unless every item resolves and each scenario's
    spirit items cost the same as its dummy's `baseline` scenario's."""
    for n, dummy in enumerate(experiment.dummies):
        where = f"{experiment.name}.dummies[{n}]"
        costs = {s.name: spirit_cost(lookup, where, s) for s in dummy.scenarios}
        if BASELINE not in costs:
            raise ReadingsError(f"{where}: no {BASELINE!r} scenario")
        for name, cost in costs.items():
            if cost != costs[BASELINE]:
                raise ReadingsError(
                    f"{where} ({name!r}): spirit items cost {cost}, "
                    + f"but the baseline's cost {costs[BASELINE]}"
                )
