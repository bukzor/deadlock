"""Live sandbox measurements of Yamato's Crimson Slash self-heal.

Setup: max hero level, max ability upgrades, every imbue set onto Crimson
Slash.

Procedure, per scenario:

- wait for cooldowns and for the target dummy to regen to full health
- press the sandbox "half health" button; record hero health as `half_health`
- cast Crimson Slash on the dummy as fast as possible
- with Mystic Reverb: record health right after the cast as `initial`
- record health once all healing has landed (after the Reverb echo, if any)
  as `after`
- run each scenario 3 times; record the lowest reading of the three

Items: spirit-slot spending is held constant across scenarios by swapping
each new item for one of equal cost. Item names are the in-game English.

Run `python crimson_slash_test_data.py` to print the observed heals.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Target:
    health: int
    spirit_resist: float
    # Health per second. Repeated measurements disagreed; these are the values
    # that each recurred.
    regen: tuple[float, ...]


DUMMY = Target(health=10686, spirit_resist=0.10, regen=(15.3, 21.8, 23.5, 33.5))


@dataclass(frozen=True)
class Scenario:
    name: str
    items: tuple[str, ...]
    health: int  # hero max health
    spirit: int  # hero spirit power, as shown on the stat sheet
    half_health: int
    after: int
    initial: int | None = None  # only with Mystic Reverb
    target: Target = DUMMY
    # Target health, read at the same moments as the hero's `initial`/`after`.
    target_initial: int | None = None
    target_after: int | None = None
    # Each purple damage number that pops up over the target, in order of
    # appearance (slash, item procs, Reverb echo).
    damage_popups: tuple[int, ...] = ()

    @property
    def heal(self) -> int:
        """Total self-heal from one cast."""
        return self.after - self.half_health

    @property
    def health_lost(self) -> int | None:
        """Target health lost by the `after` reading, starting from full.

        Smaller than the damage dealt by whatever the target regenerated
        before the reading.
        """
        if self.target_after is None:
            return None
        else:
            return self.target.health - self.target_after

    @property
    def echo_heal(self) -> int | None:
        """Self-heal from the delayed Mystic Reverb echo alone."""
        if self.initial is None:
            return None
        else:
            return self.after - self.initial


BASELINE_ITEMS = (
    "Healbane",
    "Mystic Shot",
    "Refresher",
    "Focus Lens",
    "Rapid Recharge",
)

SCENARIOS = (
    Scenario(
        name="baseline",
        items=BASELINE_ITEMS,
        health=2672,
        spirit=171,
        half_health=1337,
        after=1800,
        target_after=10537,
    ),
    Scenario(
        name="tankbuster",
        items=("Healbane", "Mystic Shot", "Refresher", "Focus Lens", "Tankbuster"),
        health=2722,
        spirit=171,
        half_health=1361,
        after=1828,
        target_after=9706,
    ),
    Scenario(
        name="reverb",
        # Reverb replaced Refresher or Focus Lens -- unconfirmed which.
        items=(
            "Healbane",
            "Mystic Shot",
            "Mystic Reverb",
            "Focus Lens",
            "Rapid Recharge",
        ),
        health=2672,
        spirit=171,
        half_health=1337,
        initial=1860,
        after=1894,
    ),
    Scenario(
        name="reverb+tankbuster",
        # Reverb replaced Refresher or Focus Lens -- unconfirmed which.
        items=("Healbane", "Mystic Shot", "Mystic Reverb", "Focus Lens", "Tankbuster"),
        health=2722,
        spirit=171,
        half_health=1361,
        initial=2136,
        after=2284,
    ),
)


def format_row(s: Scenario) -> str:
    echo = "" if s.echo_heal is None else str(s.echo_heal)
    lost = "" if s.health_lost is None else str(s.health_lost)
    popups = " ".join(str(p) for p in s.damage_popups)
    return (
        f"{s.name:<20}{s.health:>7}{s.spirit:>7}{s.target.health:>8}"
        + f"{s.heal:>6}{echo:>6}{lost:>6}  {popups}"
    )


def main():
    print(
        f"{'scenario':<20}{'hp':>7}{'spirit':>7}{'tgt_hp':>8}"
        + f"{'heal':>6}{'echo':>6}{'lost':>6}  popups"
    )
    for s in SCENARIOS:
        print(format_row(s))


if __name__ == "__main__":
    main()
