"""Render ``data/dlls/concommands.tsv`` as a Markdown help page.

    python -m deadlock.dlls_concommands_md < data/dlls/concommands.tsv > data/dlls/concommands.md

A contents list, then one section per module: each declaration as a list item,
its name, its flags, then its help, one source line per rendered line (blank
lines and leading/trailing whitespace dropped). Items sort by name; a name
declared more than once keeps one item per declaration, in queue order. A
null help and an empty one both render as no help.
"""

import re
import sys
from itertools import groupby

from . import dlls_tsv
from .sparse import parse

_INLINE = re.compile(r"[\\`*\[\]<>&~]|(?<![0-9A-Za-z])_|_(?![0-9A-Za-z])")


def escape(line: str) -> str:
    """One line of plain text as Markdown that renders as that text.

    >>> escape("<MatchID> [Metadata Salt]")
    '\\\\<MatchID\\\\> \\\\[Metadata Salt\\\\]'
    """
    line = _INLINE.sub(lambda m: "\\" + m[0], line)
    line = re.sub(r"^[#+=-]", lambda m: "\\" + m[0], line)
    return re.sub(r"^(\d+)([.)])", r"\1\\\2", line)


def _anchor(heading: str) -> str:
    """GitHub's id for a heading."""
    return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


def _item(name: str, flags: str, help: str) -> str:
    assert "`" not in name, name
    head = f"- `{name}`" + (f" · *{flags}*" if flags else "")
    text = dlls_tsv.uncell(help) or ""
    lines = [escape(line.strip()) for line in text.splitlines() if line.strip()]
    return "\\\n  ".join([head, *lines])


def page(tsv: str) -> str:
    header, rows = parse(tsv)
    assert header == ["module", "name", "flags", "help"], header
    modules = [(module, list(group)) for module, group in groupby(rows, key=lambda row: row[0])]
    assert len({module for module, _ in modules}) == len(modules), "rows not grouped by module"
    out = [
        "# Console commands\n",
        f"{len(rows)} declarations in {len(modules)} modules, from `data/dlls/concommands.tsv`.\n",
        *(f"- [{module}](#{_anchor(module)}) ({len(group)})" for module, group in modules),
    ]
    for module, group in modules:
        out += ["", f"## {module}\n"]
        out += [_item(name, flags, help) for _, name, flags, help in sorted(group, key=lambda row: row[1])]
    return "".join(f"{line}\n" for line in out)


def main() -> None:
    _ = sys.stdout.write(page(sys.stdin.read()))


if __name__ == "__main__":
    main()
