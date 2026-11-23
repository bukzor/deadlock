"""Live sandbox measurements of Yamato's Crimson Slash self-heal.

Setup: max hero level, max ability upgrades, every imbue set onto Crimson
Slash.

Procedure, per scenario:

- wait for cooldowns and for the target dummy to regen to full health
- press the sandbox "half health" button; record hero health as `start`
- cast Crimson Slash on the dummy as fast as possible
- with Mystic Reverb: record health right after the cast as `initial`
- record health once all healing has landed (after the Reverb echo, if any)
  as `after`
- run each scenario 3 times; record the lowest reading of the three

Items: spirit investment is held constant across scenarios by swapping each
new item for a spirit item of equal cost. Item names are the in-game English.

Scenarios are grouped under the dummy they were run against, so experiments
with other dummy stats get their own `Dummy` entry.

Run `python crimson_slash_test_data.py` to print the observed heals.
"""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Health:
    max: int
    start: int  # just before the cast
    initial: int | None = None  # right after the cast; only with Mystic Reverb
    after: int | None = None  # once everything has landed


@dataclass(frozen=True, kw_only=True)
class Hero:
    spirit: int  # spirit power, as shown on the stat sheet
    health: Health


@dataclass(frozen=True, kw_only=True)
class Scenario:
    name: str
    items: tuple[str, ...]
    hero: Hero
    # Each purple damage number that pops up over the target, in order of
    # appearance (slash, item procs, Reverb echo).
    damage_popups: tuple[int, ...] = ()

    @property
    def heal(self) -> int | None:
        """Total self-heal from one cast."""
        h = self.hero.health
        return None if h.after is None else h.after - h.start

    @property
    def echo_heal(self) -> int | None:
        """Self-heal from the delayed Mystic Reverb echo alone."""
        h = self.hero.health
        if h.initial is None or h.after is None:
            return None
        else:
            return h.after - h.initial


@dataclass(frozen=True, kw_only=True)
class Dummy:
    max_health: int
    spirit_resist: float
    # Health per second. Repeated measurements disagreed; these are the values
    # that each recurred.
    regen: tuple[float, ...]
    scenarios: tuple[Scenario, ...]


BASE_ITEMS = ("Healbane", "Mystic Shot", "Boundless Spirit")

DUMMIES = (
    Dummy(
        max_health=10686,
        spirit_resist=0.10,
        regen=(15.3, 21.8, 23.5, 33.5),
        scenarios=(
            Scenario(
                name="baseline",
                items=(*BASE_ITEMS, "Refresher", "Rapid Recharge"),
                hero=Hero(spirit=171, health=Health(max=2672, start=1337, after=1800)),
                damage_popups=(199,),
            ),
            Scenario(
                name="tankbuster",
                items=(*BASE_ITEMS, "Refresher", "Tankbuster"),
                hero=Hero(spirit=171, health=Health(max=2722, start=1361, after=1828)),
                damage_popups=(1025,),
            ),
            Scenario(
                name="reverb",
                items=(*BASE_ITEMS, "Mystic Reverb", "Rapid Recharge"),
                hero=Hero(
                    spirit=171,
                    health=Health(max=2672, start=1337, initial=1860, after=1894),
                ),
                damage_popups=(198, 99),
            ),
            Scenario(
                name="reverb+tankbuster",
                items=(*BASE_ITEMS, "Mystic Reverb", "Tankbuster"),
                hero=Hero(
                    spirit=171,
                    health=Health(max=2722, start=1361, initial=2136, after=2284),
                ),
                damage_popups=(1025, 471),
            ),
        ),
    ),
)


def blank_none(x: int | None) -> str:
    return "" if x is None else str(x)


def format_row(d: Dummy, s: Scenario) -> str:
    popups = " ".join(str(p) for p in s.damage_popups)
    return (
        f"{s.name:<20}{s.hero.health.max:>7}{s.hero.spirit:>7}{d.max_health:>8}"
        + f"{d.spirit_resist:>7.0%}{blank_none(s.heal):>6}"
        + f"{blank_none(s.echo_heal):>6}  {popups}"
    )


def main():
    print(
        f"{'scenario':<20}{'hp':>7}{'spirit':>7}{'tgt_hp':>8}{'resist':>7}"
        + f"{'heal':>6}{'echo':>6}  popups"
    )
    for d in DUMMIES:
        for s in d.scenarios:
            print(format_row(d, s))


if __name__ == "__main__":
    main()
