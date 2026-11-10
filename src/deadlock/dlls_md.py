"""Markdown help pages over the ``data/dlls/<facet>.tsv`` declaration tables.

A page is a contents list, then one section per DLL: each declaration as a
list item, its head line, then its help, one source line per rendered line
(blank lines and leading/trailing whitespace dropped). Items sort by name; a
name declared more than once keeps one item per declaration, in queue order.
A null help and an empty one both render as no help.
"""

import re
from collections.abc import Callable, Sequence
from itertools import groupby

from . import dlls_tsv

_INLINE = re.compile(r"[\\`*\[\]<>&~]|(?<![0-9A-Za-z])_|_(?![0-9A-Za-z])")


def escape(line: str) -> str:
    """One line of plain text as Markdown that renders as that text.

    >>> escape("<MatchID> [Metadata Salt]")
    '\\\\<MatchID\\\\> \\\\[Metadata Salt\\\\]'
    """
    line = _INLINE.sub(lambda m: "\\" + m[0], line)
    line = re.sub(r"^[#+=-]", lambda m: "\\" + m[0], line)
    return re.sub(r"^(\d+)([.)])", r"\1\\\2", line)


def code(text: str) -> str:
    """One line of text as a code span that renders as exactly that text.

    >>> code("a`b"), code("`"), code(" x")
    ('``a`b``', '`` ` ``', '`  x `')
    """
    assert text and "\n" not in text, text
    fence = "`" * (1 + max((m.end() - m.start() for m in re.finditer("`+", text)), default=0))
    pad = " " if not text.isspace() and (text[0] in "` " or text[-1] in "` ") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def _anchor(heading: str) -> str:
    """GitHub's id for a heading."""
    return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


def item(head: str, help: str) -> str:
    """A list item: ``head``, then the help cell's text as its continuation lines."""
    text = dlls_tsv.uncell(help) or ""
    lines = [escape(line.strip()) for line in text.splitlines() if line.strip()]
    return "\\\n  ".join([f"- {head}", *lines])


type Row = Sequence[str]


def page(title: str, source: str, rows: Sequence[Row], render: Callable[[Row], str]) -> str:
    """The page over ``rows`` (dll first, name second, grouped by dll), each item by ``render``."""
    groups = [(dll, list(group)) for dll, group in groupby(rows, key=lambda row: row[0])]
    assert len({dll for dll, _ in groups}) == len(groups), "rows not grouped by dll"
    out = [
        f"# {title}\n",
        f"{len(rows)} declarations in {len(groups)} DLLs, from `{source}`.\n",
        *(f"- [{dll}](#{_anchor(dll)}) ({len(group)})" for dll, group in groups),
    ]
    for dll, group in groups:
        out += ["", f"## {dll}\n"]
        out += [render(row) for row in sorted(group, key=lambda row: row[1])]
    return "".join(f"{line}\n" for line in out)
