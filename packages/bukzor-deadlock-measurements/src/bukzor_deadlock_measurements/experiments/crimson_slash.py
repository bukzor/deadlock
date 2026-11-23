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

`damage_popups`: each purple damage number that pops up over the target, in
order of appearance (slash, item procs, Reverb echo).
"""

from ..records import Dummy, Experiment, Health, Hero, Scenario

BASE_ITEMS = ("Healbane", "Mystic Shot", "Boundless Spirit")

EXPERIMENT = Experiment(
    name="crimson-slash",
    dummies=(
        Dummy(
            max_health=10686,
            spirit_resist=0.10,
            # Health per second. Repeated measurements disagreed; these are the
            # values that each recurred.
            regen=(15.3, 21.8, 23.5, 33.5),
            scenarios=(
                Scenario(
                    name="baseline",
                    items=(*BASE_ITEMS, "Refresher", "Rapid Recharge"),
                    hero=Hero(
                        spirit=171, health=Health(max=2672, start=1337, after=1800)
                    ),
                    damage_popups=(199,),
                ),
                Scenario(
                    name="tankbuster",
                    items=(*BASE_ITEMS, "Refresher", "Tankbuster"),
                    hero=Hero(
                        spirit=171, health=Health(max=2722, start=1361, after=1828)
                    ),
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
    ),
)
