"""The vocabulary of sandbox readings, shared by the experiment modules and the
programs that load, check and report them (rules: `layering_test.py`)."""

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
    # Each purple damage number over the target, in order of appearance.
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
        return h.after - h.initial


@dataclass(frozen=True, kw_only=True)
class Dummy:
    max_health: int
    spirit_resist: float
    regen: tuple[float, ...]  # health per second
    scenarios: tuple[Scenario, ...]


@dataclass(frozen=True, kw_only=True)
class Experiment:
    name: str
    dummies: tuple[Dummy, ...]
