"""Load and validate the readings files shipped beside the package.

The files are checked against `data/readings.schema.json`'s shape: unknown
or missing keys and wrong types raise `ReadingsError` naming the path.
"""

from pathlib import Path
from typing import cast

import yaml

from .records import Dummy, Experiment, Health, Hero, Scenario

# Data lives outside src/, at the package root (the repo's `data/` is
# generated output).
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

Obj = dict[str, object]


class ReadingsError(ValueError):
    pass


def _obj(
    x: object, where: str, required: set[str], optional: frozenset[str] | None = None
) -> Obj:
    if not isinstance(x, dict):
        raise ReadingsError(f"{where}: expected a mapping")
    d = cast(Obj, x)
    optional = optional or frozenset()
    if missing := required - d.keys():
        raise ReadingsError(f"{where}: missing {sorted(missing)}")
    if extra := d.keys() - required - optional:
        raise ReadingsError(f"{where}: unknown keys {sorted(extra)}")
    return d


def _int(x: object, where: str) -> int:
    if type(x) is not int:
        raise ReadingsError(f"{where}: expected an integer, got {x!r}")
    return x


def _num(x: object, where: str) -> float:
    if type(x) is not int and type(x) is not float:
        raise ReadingsError(f"{where}: expected a number, got {x!r}")
    return x


def _str(x: object, where: str) -> str:
    if not isinstance(x, str) or not x:
        raise ReadingsError(f"{where}: expected a non-empty string, got {x!r}")
    return x


def _list(x: object, where: str) -> list[object]:
    if not isinstance(x, list):
        raise ReadingsError(f"{where}: expected a list")
    return cast(list[object], x)


def _opt_int(d: Obj, key: str, where: str) -> int | None:
    return _int(d[key], f"{where}.{key}") if key in d else None


def _health(x: object, where: str) -> Health:
    d = _obj(x, where, {"max", "start"}, frozenset({"initial", "after"}))
    return Health(
        max=_int(d["max"], f"{where}.max"),
        start=_int(d["start"], f"{where}.start"),
        initial=_opt_int(d, "initial", where),
        after=_opt_int(d, "after", where),
    )


def _scenario(x: object, where: str) -> Scenario:
    d = _obj(x, where, {"name", "items", "hero"}, frozenset({"damage_popups"}))
    hero = _obj(d["hero"], f"{where}.hero", {"spirit", "health"})
    items = _list(d["items"], f"{where}.items")
    popups = _list(d.get("damage_popups", []), f"{where}.damage_popups")
    return Scenario(
        name=_str(d["name"], f"{where}.name"),
        items=tuple(_str(i, f"{where}.items") for i in items),
        hero=Hero(
            spirit=_int(hero["spirit"], f"{where}.hero.spirit"),
            health=_health(hero["health"], f"{where}.hero.health"),
        ),
        damage_popups=tuple(_int(p, f"{where}.damage_popups") for p in popups),
    )


def _dummy(x: object, where: str) -> Dummy:
    d = _obj(x, where, {"max_health", "spirit_resist", "regen", "scenarios"})
    resist = _num(d["spirit_resist"], f"{where}.spirit_resist")
    if not 0 <= resist <= 1:
        raise ReadingsError(f"{where}.spirit_resist: outside 0..1")
    regen = _list(d["regen"], f"{where}.regen")
    scenarios = _list(d["scenarios"], f"{where}.scenarios")
    return Dummy(
        max_health=_int(d["max_health"], f"{where}.max_health"),
        spirit_resist=resist,
        regen=tuple(_num(r, f"{where}.regen") for r in regen),
        scenarios=tuple(
            _scenario(s, f"{where}.scenarios[{i}]") for i, s in enumerate(scenarios)
        ),
    )


def parse(doc: object, where: str = "<doc>") -> Experiment:
    """Validate a parsed YAML document and build its records."""
    d = _obj(doc, where, {"experiment", "dummies"})
    dummies = _list(d["dummies"], f"{where}.dummies")
    if not dummies:
        raise ReadingsError(f"{where}.dummies: empty")
    return Experiment(
        name=_str(d["experiment"], f"{where}.experiment"),
        dummies=tuple(
            _dummy(x, f"{where}.dummies[{i}]") for i, x in enumerate(dummies)
        ),
    )


def load(path: Path) -> Experiment:
    doc = cast(object, yaml.safe_load(path.read_text()))
    return parse(doc, path.name)


def load_all(data_dir: Path = DATA_DIR) -> tuple[Experiment, ...]:
    """Every `*.yaml` experiment in `data_dir`, in name order."""
    return tuple(load(p) for p in sorted(data_dir.glob("*.yaml")))
