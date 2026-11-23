"""Load the readings files shipped beside the package.

`data/readings.schema.json` is the one home of a file's shape: a violation
raises `ReadingsError` naming the file and the offending path. The builders
below assume that shape.
"""

import json
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import cast

import yaml
from jsonschema import Draft7Validator, ValidationError

from .records import Dummy, Experiment, Health, Hero, Scenario

# Data lives outside src/, at the package root (the repo's `data/` is
# generated output).
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SCHEMA = DATA_DIR / "readings.schema.json"

Obj = dict[str, object]


class ReadingsError(ValueError):
    pass


def _validate(doc: object, where: str) -> None:
    validator = Draft7Validator(cast(Obj, json.loads(SCHEMA.read_text())))
    iter_errors = cast(
        "Callable[[object], Iterable[ValidationError]]", validator.iter_errors
    )
    problems = sorted((e.json_path[1:], e.message) for e in iter_errors(doc))
    if problems:
        raise ReadingsError("; ".join(f"{where}{p}: {m}" for p, m in problems))


def _health(d: Obj) -> Health:
    return Health(
        max=cast(int, d["max"]),
        start=cast(int, d["start"]),
        initial=cast("int | None", d.get("initial")),
        after=cast("int | None", d.get("after")),
    )


def _scenario(d: Obj) -> Scenario:
    hero = cast(Obj, d["hero"])
    return Scenario(
        name=cast(str, d["name"]),
        items=tuple(cast("list[str]", d["items"])),
        hero=Hero(
            spirit=cast(int, hero["spirit"]),
            health=_health(cast(Obj, hero["health"])),
        ),
        damage_popups=tuple(cast("list[int]", d.get("damage_popups", []))),
    )


def _dummy(d: Obj) -> Dummy:
    return Dummy(
        max_health=cast(int, d["max_health"]),
        spirit_resist=float(cast(float, d["spirit_resist"])),
        regen=tuple(float(r) for r in cast("list[float]", d["regen"])),
        scenarios=tuple(_scenario(s) for s in cast("list[Obj]", d["scenarios"])),
    )


def parse(doc: object, where: str = "<doc>") -> Experiment:
    """Validate a parsed YAML document against the schema and build its records."""
    _validate(doc, where)
    d = cast(Obj, doc)
    return Experiment(
        name=cast(str, d["experiment"]),
        dummies=tuple(_dummy(x) for x in cast("list[Obj]", d["dummies"])),
    )


def load(path: Path) -> Experiment:
    doc = cast(object, yaml.safe_load(path.read_text()))
    return parse(doc, path.name)


def load_all(data_dir: Path = DATA_DIR) -> tuple[Experiment, ...]:
    """Every `*.yaml` experiment in `data_dir`, in name order."""
    return tuple(load(p) for p in sorted(data_dir.glob("*.yaml")))
