"""Parse a console log from ``bin/cvarlist-capture``: the engine's ``cvarlist``
listing and the ``differences`` table after it
(``docs/dev/game-runtime.kb/cvarlist-capture.md``).

The listing is one message: ``cvar list``, a ``--------------`` rule, one
``[Console]`` line per name (``%-80s : %-16s : %-32s : %s``: name, current
value, comma-separated flag words, help), the rule again, and a
``N total convars/concommands`` line. Lines after a message's first carry no
``MM/DD HH:MM:SS [Channel]`` prefix. ``differences`` prints ``no results``, or a
table of the names whose value isn't their default: a header, a rule of one
``_`` run per column (``name value default flags help``, each column as wide as
its run), then one ``[Console]`` line per name. The text is the log decoded,
without its BOM; any departure from that shape is an ``AssertionError``.
"""

import re
from collections.abc import Sequence
from typing import NamedTuple

_CONSOLE = re.compile(r"\d\d/\d\d \d\d:\d\d:\d\d \[Console\] ")
_RULE = "--------------"
_TOTAL = re.compile(r"(\d+) total convars/concommands")


class Entry(NamedTuple):
    """One listing row, as printed: help with ``\\n`` and ``\\t`` as spaces, ``"`` as ``'``."""

    name: str
    value: str
    flags: tuple[str, ...]
    help: str


class Difference(NamedTuple):
    """One ``differences`` row: flags as full words (``client``, not ``cl``)."""

    name: str
    value: str
    default: str
    flags: tuple[str, ...]
    help: str


class Capture(NamedTuple):
    entries: Sequence[Entry]
    total: int
    """The listing's own count of its rows."""
    differences: Sequence[Difference]


def _console(line: str) -> str | None:
    """The body of a ``[Console]`` message's first line; ``None`` for any other line."""
    match = _CONSOLE.match(line)
    return line[match.end() :] if match else None


def _entry(line: str) -> Entry:
    body = _console(line)
    cells = body.split(" : ", 3) if body is not None else []
    assert len(cells) == 4, ("not a listing row", line)
    name, value, flags, help_ = cells
    words = flags.rstrip()
    return Entry(name.rstrip(), value.rstrip(), tuple(words.split(", ")) if words else (), help_)


def _cells(body: str, widths: Sequence[int]) -> list[str]:
    """``body`` cut into ``len(widths) + 1`` cells, each before the last
    ``widths[i]`` wide (padded), one space apart."""
    cells: list[str] = []
    start = 0
    for width in widths:
        end = start + width
        assert body[end : end + 1] in ("", " "), ("differences cell overflows its column", body)
        cells.append(body[start:end].rstrip())
        start = end + 1
    return [*cells, body[start:]]


def _differences(lines: Sequence[str]) -> list[Difference]:
    """The ``differences`` output that opens ``lines``."""
    first = _console(lines[0]) if lines else None
    if first == "no results":
        return []
    assert first is not None and first.startswith("name "), ("no differences output", lines[:1])
    rule = _console(lines[1])
    assert rule is not None and set(rule) == {"_", " "}, ("no differences rule", lines[1])
    widths = [len(run) for run in rule.split(" ")]
    assert len(widths) == 5, ("differences columns", rule)
    rows: list[Difference] = []
    for line in lines[2:]:
        if (body := _console(line)) is None:
            break
        name, value, default, flags, help_ = _cells(body, widths[:-1])
        rows.append(Difference(name, value, default, tuple(flags.split()), help_))
    return rows


def parse(text: str) -> Capture:
    """The listing and ``differences`` in the console log ``text``."""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if _console(line) == "cvar list"]
    assert len(starts) == 1, ("no cvar list, or more than one", starts)
    start = starts[0] + 1
    assert lines[start : start + 1] == [_RULE], ("no rule after cvar list", lines[start : start + 1])
    end = next((i for i in range(start + 1, len(lines)) if _console(lines[i]) == _RULE), None)
    assert end is not None, "listing never closes"
    entries = [_entry(line) for line in lines[start + 1 : end]]
    total = _TOTAL.fullmatch(lines[end + 1]) if end + 1 < len(lines) else None
    assert total, ("no total after the listing", lines[end + 1 : end + 2])
    return Capture(entries, int(total[1]), _differences(lines[end + 2 :]))
