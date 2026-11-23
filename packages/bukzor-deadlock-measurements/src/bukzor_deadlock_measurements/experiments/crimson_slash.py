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

Run `python -m bukzor_deadlock_measurements` to print the observed heals.
"""

from ..records import Dummy, ExperimentalSetup, Health, Scenario

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
