"""Render ``data/dlls/concommands.tsv`` as a Markdown help page.

    python -m deadlock.dlls_concommands_md < data/dlls/concommands.tsv > data/concommands.md

The page is ``deadlock.dlls_md``'s; an item's head is the command's name,
then its flags.
"""

import sys

from . import dlls_md
from .sparse import parse


def _item(row: dlls_md.Row) -> str:
    _, name, flags, help = row
    return dlls_md.item(dlls_md.code(name) + (f" · *{flags}*" if flags else ""), help)


def page(tsv: str) -> str:
    header, rows = parse(tsv)
    assert header == ["dll", "name", "flags", "help"], header
    return dlls_md.page("Console commands", "data/dlls/concommands.tsv", rows, _item)


def main() -> None:
    _ = sys.stdout.write(page(sys.stdin.read()))


if __name__ == "__main__":
    main()
