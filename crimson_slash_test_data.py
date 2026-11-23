"""Live sandbox measurements of Yamato's Crimson Slash self-heal.

Setup: max hero level, max ability upgrades, every imbue set onto Crimson
Slash.

Procedure, per scenario:

- wait for cooldowns and for the target dummy to regen to full health
- press the sandbox "half health" button; record hero health as `start`
- cast Crimson Slash on the dummy as fast as possible
- record health once the slash's healing has landed as `hit`
- with Mystic Reverb: record health once the echo's healing has landed as
  `reverb`
- run each scenario 3 times; record the lowest reading of the three

Every reading lags its moment a little: a changing number can't be read
until it settles, so a reading may include some regen or late healing.

The game rounds damage numbers randomly (199 or 198 for the same hit), so
`damage` holds the lowest number seen.

Items: spirit investment is held constant within an `ExperimentalSetup` by
swapping each new item for a spirit item of equal cost. Rapid Recharge's
spirit bonus is for charged abilities only, which Crimson Slash is not, so
the stat-sheet spirit stays put. Item names are the in-game English.

An `ExperimentalSetup` holds what its scenarios share: the dummy, the items
common to all of them, and the hero's spirit. A scenario lists only the items
it adds.

Run `python crimson_slash_test_data.py` to print the observed heals.
"""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Health:
    max: int
    start: int  # just before the cast
    hit: int  # once the slash's healing has landed
    reverb: int | None = None  # once the Mystic Reverb echo has landed


@dataclass(frozen=True, kw_only=True)
class Scenario:
    name: str
    items: tuple[str, ...]  # on top of the setup's
    health: Health  # the hero's
    # Each purple damage number that pops up over the target, in order of
    # appearance (slash, item procs, Reverb echo).
    damage: tuple[int, ...]

    @property
    def heal(self) -> int:
        """Total self-heal from one cast."""
        h = self.health
        return (h.hit if h.reverb is None else h.reverb) - h.start

    @property
    def echo_heal(self) -> int | None:
        """Self-heal from the delayed Mystic Reverb echo alone."""
        h = self.health
        if h.reverb is None:
            return None
        else:
            return h.reverb - h.hit


@dataclass(frozen=True, kw_only=True)
class Dummy:
    max_health: int
    spirit_resist: float
    regen: tuple[float, ...]  # health per second, one value per condition


@dataclass(frozen=True, kw_only=True)
class ExperimentalSetup:
    dummy: Dummy
    items: tuple[str, ...]
    spirit: int  # hero spirit power, as shown on the stat sheet
    scenarios: tuple[Scenario, ...]


SETUPS = (
    ExperimentalSetup(
        dummy=Dummy(
            max_health=10686,
            spirit_resist=0.10,
            regen=(
                15.3,  # healbane, in combat
                21.8,  # healbane, out of combat
                23.5,  # in combat
                33.5,  # out of combat, steady state
            ),
        ),
        items=("Healbane", "Mystic Shot", "Boundless Spirit"),
        spirit=171,
        scenarios=(
            Scenario(
                name="baseline",
                items=("Refresher", "Rapid Recharge"),
                health=Health(max=2672, start=1336, hit=1800),
                damage=(198,),
            ),
            Scenario(
                name="tankbuster",
                items=("Refresher", "Tankbuster"),
                health=Health(max=2722, start=1361, hit=1828),
                damage=(1025,),
            ),
            Scenario(
                name="reverb",
                items=("Mystic Reverb", "Rapid Recharge"),
                health=Health(max=2672, start=1336, hit=1860, reverb=1894),
                damage=(198, 99),
            ),
            Scenario(
                name="reverb+tankbuster",
                items=("Mystic Reverb", "Tankbuster"),
                health=Health(max=2722, start=1361, hit=2136, reverb=2284),
                damage=(1025, 471),
            ),
        ),
    ),
    ExperimentalSetup(
        dummy=Dummy(
            max_health=9091,
            spirit_resist=0.10,
            regen=(
                15.3,  # healbane, in combat
                21.8,  # healbane, out of combat
                23.5,  # in combat
                33.5,  # out of combat, steady state
            ),
        ),
        items=("Healbane", "Mystic Shot", "Boundless Spirit"),
        spirit=171,
        scenarios=(
            Scenario(
                name="baseline",
                items=("Refresher", "Rapid Recharge"),
                health=Health(max=2672, start=1336, hit=1800),
                damage=(198,),
            ),
            Scenario(
                name="tankbuster",
                items=("Refresher", "Tankbuster"),
                health=Health(max=2722, start=1361, hit=1828),
                damage=(905,),
            ),
            Scenario(
                name="reverb",
                items=("Mystic Reverb", "Rapid Recharge"),
                health=Health(max=2672, start=1336, hit=1860, reverb=1894),
                damage=(198, 99),
            ),
            Scenario(
                name="reverb+tankbuster",
                items=("Mystic Reverb", "Tankbuster"),
                health=Health(max=2722, start=1361, hit=2100, reverb=2228),
                damage=(905, 417),
            ),
        ),
    ),
    ExperimentalSetup(
        dummy=Dummy(
            max_health=10686,
            spirit_resist=0.10,
            regen=(
                23.5,  # in combat
                33.5,  # out of combat, steady state
            ),
        ),
        items=("Improved Spirit",),
        spirit=116,
        scenarios=(
            Scenario(
                name="baseline",
                items=("Refresher", "Rapid Recharge"),
                health=Health(max=2320, start=1160, hit=1522),
                damage=(150,),
            ),
            Scenario(
                name="tankbuster",
                items=("Refresher", "Tankbuster"),
                health=Health(max=2370, start=1185, hit=1550),
                damage=(981,),
            ),
            Scenario(
                name="reverb",
                items=("Mystic Reverb", "Rapid Recharge"),
                health=Health(max=2320, start=1160, hit=1568, reverb=1593),
                damage=(150, 75),
            ),
            Scenario(
                name="reverb+tankbuster",
                items=("Mystic Reverb", "Tankbuster"),
                health=Health(max=2370, start=1185, hit=1844, reverb=1982),
                damage=(981, 449),
            ),
        ),
    ),
)


def blank_none(x: int | None) -> str:
    return "" if x is None else str(x)


def format_row(setup: ExperimentalSetup, s: Scenario) -> str:
    damage = " ".join(str(n) for n in s.damage)
    return (
        f"{s.name:<20}{s.health.max:>7}{setup.spirit:>7}"
        + f"{setup.dummy.max_health:>8}{setup.dummy.spirit_resist:>7.0%}"
        + f"{s.heal:>6}{blank_none(s.echo_heal):>6}  {damage}"
    )


def main():
    print(
        f"{'scenario':<20}{'hp':>7}{'spirit':>7}{'tgt_hp':>8}{'resist':>7}"
        + f"{'heal':>6}{'echo':>6}  damage"
    )
    for setup in SETUPS:
        for s in setup.scenarios:
            print(format_row(setup, s))


if __name__ == "__main__":
    main()
