"""The query registry: every query the HTTP API and the CLI answer, by name.

``QUERIES`` maps a name to a ``Query`` (see ``types.py``); the lines each one
emits are the design's "Protocol" (``docs/dev/decisions.kb/vis-app.md``).
``registry`` builds the same table over any game-data loader, so tests can
substitute synthetic trees. ``QUERIES`` reads ``data/`` once per process, when
its first query runs, so importing this module is cheap and needs no data.
Ability and property names come from the game's localization (``names``).
"""

import csv
import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cache

from deadlock import gamedata, paths
from deadlock.abilities import SIGNATURE, bindings

from . import boons, casts, guns, melee, names
from .boons import NONE, Boons
from .measures import Measure, horizon_used, measures
from .timeline import Cycle, Hit, landed_by
from .types import BadRequest, JsonObj, Kind, Params, Query

MAX_HITS = 10_000  # per timeline: what a browser chart draws without stalling
NOT_PLAYABLE = {"hero_targetdummy", "hero_genericperson"}  # the training dummy; Generic Person

HERO = "hero key, from the heroes query (required)"
TIMELINE = {
    "hero": HERO,
    "ability": "ability key, from the abilities query (required)",
    "seconds": "the window in seconds, > 0; give this or cycles (default 2 cycles, or 10 s for a one-shot)",
    "cycles": "the window in periods of the cycle, > 0; give this or seconds",
    "level": "hero level, a whole number from 0 (default) to the data's last: one boon per level",
    "distance": "meters to the target, >= 0 (default 0): a gun's bullet travel",
    "spirit": "spirit power on top of the level's, >= 0 (default 0): scales a cast's damage",
    "windup": "seconds from a melee swing to its hit, >= 0 (default 0)",
    "hp": "target health, > 0 (optional): adds time_to_kill, first, wherever the kill falls; never changes the window",
}

type Source = tuple[Kind, Cycle, Sequence[str]]  # (kind, cycle, notes)


@dataclass(frozen=True)
class GameData:
    """The ``heroes.vdata`` and ``abilities.vdata`` trees (see ``deadlock.gamedata``), the heroes to list, and the localization."""

    heroes: Mapping[str, object]
    abilities: Mapping[str, object]
    listed: Mapping[str, str]  # hero key: display name, for each hero the heroes query may list
    tokens: Mapping[str, str] = field(default_factory=dict[str, str])  # the localization (``names.load_tokens``)


def registry(data: Callable[[], GameData]) -> Mapping[str, Query]:
    """``heroes``, ``abilities`` and ``timeline`` over ``data``, which each run calls.

    Every query rejects a parameter it doesn't declare.
    """
    return {
        "heroes": _query({}, lambda _: heroes(data())),
        "abilities": _query({"hero": HERO}, lambda params: abilities(data(), _required(params, "hero"))),
        "timeline": _query(TIMELINE, lambda params: timeline(data(), params)),
    }


def _query(params: Mapping[str, str], run: Callable[[Params], Sequence[JsonObj]]) -> Query:
    def checked(given: Params) -> Sequence[JsonObj]:
        unknown = sorted(set(given) - set(params))
        if unknown:
            raise BadRequest(f"unknown parameter: {', '.join(unknown)} (accepted: {', '.join(params) or 'none'})")
        return run(given)

    return Query(params, checked)


def heroes(data: GameData) -> list[JsonObj]:
    """``{"hero", "name"}`` for each live hero in ``data.listed``, by display name."""
    live = {h for h, _, _ in bindings(data.heroes)} & set(data.listed)
    return [{"hero": hero, "name": data.listed[hero]} for hero in sorted(live, key=lambda h: (data.listed[h], h))]


def abilities(data: GameData, hero: str) -> list[JsonObj]:
    """``{"ability", "name", "kind"}`` for ``hero``'s gun, light and heavy melee, then signatures by slot.

    ``name`` is the in-game name (``names.ability_name``).
    ``kind`` is the source that models the ability at default parameters
    (``"gun"``, ``"melee"``, ``"cast"``), or ``None`` when none does.
    """
    lines: list[JsonObj] = []
    for ability in _kit(data, hero):
        found = _source(data, hero, ability)
        lines.append({"ability": ability, "name": names.ability_name(data.tokens, ability), "kind": None if found is None else found[0]})
    return lines


def timeline(data: GameData, params: Params) -> list[JsonObj]:
    """The ``cycle`` line, every hit that lands by the horizon, every measure, then every note, for ``TIMELINE``'s parameters.

    The horizon is ``measures.horizon_used``; a window of more than
    ``MAX_HITS`` hits is a ``BadRequest``. A cast's measures include its
    card's DPS, when it has one. The notes are the level's (see
    ``_level_notes``), the source's (by how much each moves the numbers), then
    one when a one-shot is asked for in cycles, and one when ``hp`` is never
    reached. An ability ``abilities`` lists that no source models gets only
    notes, one saying so.
    """
    hero, ability = _required(params, "hero"), _required(params, "ability")
    seconds, cycles = (_optional_number(params, name, positive=True) for name in ("seconds", "cycles"))
    if seconds is not None and cycles is not None:
        raise BadRequest("give the window in seconds or in cycles, not both")
    distance, spirit, windup = (_number(params, name, 0.0) for name in ("distance", "spirit", "windup"))
    hp = _optional_number(params, "hp", positive=True)
    if ability not in _kit(data, hero):
        raise BadRequest(f"unknown ability for {hero}: {ability} (see the abilities query)")
    level = _level(params, boons.last_level(data.heroes, hero))
    gained = boons.at_level(data.heroes, hero, level)
    found = _source(data, hero, ability, distance=distance, spirit=spirit + gained.spirit, windup=windup, boons=gained)
    level_notes = _level_notes(level, gained)
    if found is None:
        unmodeled = f"{ability} has no damage model: only guns, melee and damaging signature abilities are modeled"
        return [*(_note(text) for text in level_notes), _note(unmodeled)]
    kind, cycle, notes = found
    horizon = horizon_used(cycle, seconds, cycles)
    _check_hits(cycle, horizon)
    if cycles is not None and cycle.period is None:
        notes = [*notes, f"This happens once, so it has no cycles: the window is {horizon:g} s."]
    card = casts.card_dps(data.abilities, ability, spirit + gained.spirit) if kind == "cast" else None
    measured = measures(cycle, horizon, hp, kind=kind, card_dps=card)
    if hp is not None and "time_to_kill" not in {m.name for m in measured}:
        notes = [*notes, f"The target's {hp:g} HP is never reached: no time to kill is shown."]
    return [
        {"kind": "cycle", "period": cycle.period, "downtime": cycle.downtime, "horizon": horizon},
        *(_hit(hit) for hit in landed_by(cycle, horizon)),
        *(_measure(m) for m in measured),
        *(_note(text) for text in [*level_notes, *notes]),
    ]


@cache
def load_data() -> GameData:
    """``data/``'s hero and ability trees, ``gamedata.tsv/heroes.tsv``'s ``listed`` heroes, and the install's localization, read once per process."""
    root = paths.data_dir()
    with (root / "gamedata.json/scripts/heroes.json").open() as file:
        hero_tree = gamedata.load(file)
    with (root / "gamedata.json/scripts/abilities.json").open() as file:
        ability_tree = gamedata.load(file)
    with (root / "gamedata.tsv/heroes.tsv").open(newline="") as file:
        hero_names = listed(csv.DictReader(file, delimiter="\t", quoting=csv.QUOTE_NONE))
    return GameData(hero_tree, ability_tree, hero_names, names.load_tokens())


def listed(rows: Iterable[Mapping[str, str]]) -> dict[str, str]:
    """``{hero: name}`` from ``heroes.tsv`` rows that are not ``disabled``, have a name, and are neither Generic Person nor the training dummy."""
    return {r["hero"]: r["name"] for r in rows if r["disabled"] == "false" and r["name"] and r["hero"] not in NOT_PLAYABLE}


QUERIES: Mapping[str, Query] = registry(load_data)


def _kit(data: GameData, hero: str) -> list[str]:
    """The abilities ``abilities`` lists for ``hero``, in order; ``BadRequest`` unless ``hero`` is live."""
    slots = {slot: ability for h, slot, ability in bindings(data.heroes) if h == hero}
    if not slots:
        raise BadRequest(f"unknown hero: {hero} (see the heroes query)")
    gun = [slots[guns.SLOT]] if guns.SLOT in slots else []
    return [*gun, melee.LIGHT, melee.HEAVY, *(slots[s] for s in sorted(slots) if s.startswith(SIGNATURE))]


def _source(
    data: GameData,
    hero: str,
    ability: str,
    distance: float = 0.0,
    spirit: float = 0.0,
    windup: float = 0.0,
    boons: Boons = NONE,
) -> Source | None:
    """The first source that models ``ability``, as ``(kind, cycle, notes)``; ``spirit`` is the total."""
    trees = (data.heroes, data.abilities, hero, ability)
    sources: Mapping[Kind, Callable[[], tuple[Cycle, Sequence[str]] | None]] = {
        "gun": lambda: guns.cycle(*trees, distance, boons),
        "melee": lambda: melee.cycle(*trees, windup, boons),
        "cast": lambda: casts.cycle(*trees, spirit, data.tokens),
    }
    for kind, source in sources.items():
        found = source()
        if found is not None:
            cycle, notes = found
            return kind, cycle, notes
    return None


def _check_hits(cycle: Cycle, horizon: float) -> None:
    """``BadRequest`` when the cycles that start within ``horizon`` hold more than ``MAX_HITS`` hits."""
    starts = 1 if cycle.period is None else math.ceil(horizon / cycle.period)
    count = starts * len(cycle.hits)
    if count > MAX_HITS:
        raise BadRequest(f"a window of {horizon:g} s holds {count:,} hits, more than the {MAX_HITS:,} a timeline sends: ask for fewer seconds or cycles")


def _level(params: Params, last: int) -> int:
    """``level`` as a whole number from 0 to ``last``; 0 if absent."""
    text = params.get("level", "0")
    try:
        level = int(text)
    except ValueError:
        raise BadRequest(f"level is not a whole number: {text!r}") from None
    if not 0 <= level <= last:
        raise BadRequest(f"level must be from 0 to {last}, got {text}")
    return level


def _level_notes(level: int, gained: Boons) -> list[str]:
    """The level and items the numbers assume; above level 0, what the boons add."""
    stated = f"Hero level {level}, no items: a build with items will differ."
    if level == 0:
        return [stated]
    adds = (
        f"+{gained.bullet:.3g} bullet damage per bullet, +{gained.light_melee:.3g} light and "
        f"+{gained.heavy_melee:.3g} heavy melee damage, +{gained.spirit:.3g} spirit power"
    )
    return [stated, f"Level {level} is {gained.count} boons: {adds}. Read from the data, not checked in-game."]


def _required(params: Params, name: str) -> str:
    if name not in params:
        raise BadRequest(f"missing parameter: {name}")
    return params[name]


def _number(params: Params, name: str, default: float, *, positive: bool = False) -> float:
    value = _optional_number(params, name, positive=positive)
    return default if value is None else value


def _optional_number(params: Params, name: str, *, positive: bool) -> float | None:
    """``name`` as a finite number, ``> 0`` if ``positive`` else ``>= 0``; ``None`` if absent."""
    if name not in params:
        return None
    text = params[name]
    try:
        value = float(text)
    except ValueError:
        raise BadRequest(f"{name} is not a number: {text!r}") from None
    if not math.isfinite(value):
        raise BadRequest(f"{name} is not a finite number: {text!r}")
    if value < 0 or (positive and value == 0):
        raise BadRequest(f"{name} must be {'> 0' if positive else '>= 0'}, got {text}")
    return value


def _hit(hit: Hit) -> JsonObj:
    return {"kind": "hit", "trigger": hit.trigger, "land": hit.land, "damage": hit.damage, "label": hit.label, "cycle": hit.cycle}


def _measure(measure: Measure) -> JsonObj:
    return {"kind": "measure", "name": measure.name, "label": measure.label, "value": measure.value, "unit": measure.unit, "check": measure.check}


def _note(text: str) -> JsonObj:
    return {"kind": "note", "text": text}
