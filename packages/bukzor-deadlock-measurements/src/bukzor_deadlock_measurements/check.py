"""Check an experiment's item lists against the game data.

Readings are observations: nothing here replaces or defaults a recorded
number from the data, it only compares.
"""

from bukzor_deadlock_lookup.lookup import Lookup
from bukzor_deadlock_lookup.resolve import Unresolved

from .records import ExperimentalSetup, Scenario

SPIRIT_SLOT = "Tech"  # the shop's spirit column
BASELINE = "baseline"


class ReadingsError(ValueError):
    pass


def spirit_cost(
    lookup: Lookup, where: str, setup: ExperimentalSetup, scenario: Scenario
) -> int:
    """Souls the scenario's spirit items, the setup's included, cost in all;
    every name must resolve."""
    total = 0
    for name in setup.items + scenario.items:
        try:
            item = lookup.item(name)
        except Unresolved as e:
            raise ReadingsError(f"{where} ({scenario.name!r}): {e}") from e
        if item.slot == SPIRIT_SLOT:
            total += item.cost
    return total


def check(name: str, setups: tuple[ExperimentalSetup, ...], lookup: Lookup) -> None:
    """Raise `ReadingsError` unless every item resolves and each scenario's
    spirit items cost the same as its setup's `baseline` scenario's."""
    for n, setup in enumerate(setups):
        where = f"{name}.SETUPS[{n}]"
        costs = {s.name: spirit_cost(lookup, where, setup, s) for s in setup.scenarios}
        if BASELINE not in costs:
            raise ReadingsError(f"{where}: no {BASELINE!r} scenario")
        for scenario, cost in costs.items():
            if cost != costs[BASELINE]:
                raise ReadingsError(
                    f"{where} ({scenario!r}): spirit items cost {cost}, "
                    + f"but the baseline's cost {costs[BASELINE]}"
                )
