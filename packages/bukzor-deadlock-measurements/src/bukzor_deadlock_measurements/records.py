"""The vocabulary of sandbox readings, shared by the experiment modules and the
programs that load, check and report them (rules: `layering_test.py`)."""

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
