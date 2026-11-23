"""The summary table of observed heals."""

from .records import Dummy, Experiment, Scenario


def blank_none(x: int | None) -> str:
    return "" if x is None else str(x)


def format_row(d: Dummy, s: Scenario) -> str:
    popups = " ".join(str(p) for p in s.damage_popups)
    return (
        f"{s.name:<20}{s.hero.health.max:>7}{s.hero.spirit:>7}{d.max_health:>8}"
        + f"{d.spirit_resist:>7.0%}{blank_none(s.heal):>6}"
        + f"{blank_none(s.echo_heal):>6}  {popups}"
    )


def format_table(experiments: tuple[Experiment, ...]) -> str:
    lines = [
        f"{'scenario':<20}{'hp':>7}{'spirit':>7}{'tgt_hp':>8}{'resist':>7}"
        + f"{'heal':>6}{'echo':>6}  popups"
    ]
    for e in experiments:
        lines += [format_row(d, s) for d in e.dummies for s in d.scenarios]
    return "\n".join(lines) + "\n"
