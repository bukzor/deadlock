"""The summary table of observed heals."""

from .load import Experiments
from .records import ExperimentalSetup, Scenario


def blank_none(x: int | None) -> str:
    return "" if x is None else str(x)


def format_row(setup: ExperimentalSetup, s: Scenario) -> str:
    damage = " ".join(str(n) for n in s.damage)
    return (
        f"{s.name:<20}{s.health.max:>7}{setup.spirit:>7}"
        + f"{setup.dummy.max_health:>8}{setup.dummy.spirit_resist:>7.0%}"
        + f"{s.heal:>6}{blank_none(s.echo_heal):>6}  {damage}"
    )


def format_table(experiments: Experiments) -> str:
    lines = [
        f"{'scenario':<20}{'hp':>7}{'spirit':>7}{'tgt_hp':>8}{'resist':>7}"
        + f"{'heal':>6}{'echo':>6}  damage"
    ]
    for setups in experiments.values():
        lines += [format_row(setup, s) for setup in setups for s in setup.scenarios]
    return "\n".join(lines) + "\n"
