"""Render ``data/dlls/convars.tsv`` as a Markdown help page.

    python -m deadlock.dlls_convars_md < data/dlls/convars.tsv > data/convars.md

The page is ``deadlock.dlls_md``'s; an item's head is the convar's name, its
type, then whichever it has of a default (``= …``; an empty string as
*empty*), a min, a max, a nonzero version, and flags. Values show as their
``convars.tsv`` cells read (``deadlock.dlls_convars``).
"""

import sys

from . import dlls_md
from . import dlls_tsv
from .sparse import parse


def _value(cell: str) -> str:
    text = dlls_tsv.uncell(cell)
    assert text is not None, cell
    return dlls_md.code(text) if text else "*empty*"


def _item(row: dlls_md.Row) -> str:
    _, name, type_, version, default, min_, max_, flags, help = row
    head = f"{dlls_md.code(name)} · {type_}"
    if dlls_tsv.uncell(default) is not None:
        head += f" = {_value(default)}"
    for label, cell in [("min", min_), ("max", max_)]:
        if dlls_tsv.uncell(cell) is not None:
            head += f" · {label} {_value(cell)}"
    if version != "0":
        head += f" · version {version}"
    if flags:
        head += f" · *{flags}*"
    return dlls_md.item(head, help)


def page(tsv: str) -> str:
    header, rows = parse(tsv)
    assert header == ["dll", "name", "type", "version", "default", "min", "max", "flags", "help"], header
    return dlls_md.page("Console variables", "data/dlls/convars.tsv", rows, _item)


def main() -> None:
    _ = sys.stdout.write(page(sys.stdin.read()))


if __name__ == "__main__":
    main()
