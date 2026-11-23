"""The real ``Lookup``: ``data/``'s game-data trees and the install's English localization, read once per process."""

from collections.abc import Mapping
from functools import cache

from bukzor_deadlock import gamedata, items, loc, paths

from .lookup import Lookup

# hero names; ability names; item names; property labels (the files share no token they disagree on)
FILES = (
    "citadel_gc_hero_names",
    "citadel_heroes",
    "citadel_gc_mod_names",
    "citadel_attributes",
)
HEADER = (
    "Language",
    "Language_search",
)  # each file's own language tag, not a name; spelled differently per file


@cache
def load() -> Lookup:
    """``data/gamedata.json/scripts/``'s heroes, abilities and item prices, with ``load_tokens``; read at the first call."""
    scripts = paths.data_dir() / "gamedata.json/scripts"
    trees: dict[str, Mapping[str, object]] = {}
    for name in ("heroes", "abilities", "generic_data"):
        with (scripts / f"{name}.json").open() as file:
            trees[name] = gamedata.load(file)
    return Lookup(
        trees["heroes"],
        trees["abilities"],
        items.prices(trees["generic_data"]),
        load_tokens(),
    )


def load_tokens() -> dict[str, str]:
    """``FILES``' English token tables from the install, merged, less their ``HEADER``; a token in two files must agree."""
    root = paths.citadel_dir() / "resource/localization"
    merged: dict[str, str] = {}
    for name in FILES:
        with (root / name / f"{name}_english.txt").open(encoding="utf-8-sig") as file:
            table = {k: v for k, v in loc.tokens(file).items() if k not in HEADER}
        clashes = sorted(
            k for k in table.keys() & merged.keys() if table[k] != merged[k]
        )
        assert not clashes, (name, clashes)
        merged |= table
    return merged
