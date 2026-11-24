"""CLI: the forum CSV of suggested captions for foreign-language VO, on stdout.

The output is ``data/vo/forum.csv``.

    python -m bukzor_deadlock.vo_forum <foreign.tsv> <lines.tsv> <hero_names.txt>

One row per ``foreign.tsv`` row, sorted by hero display name then
``caption_token``. Columns: ``hero`` (display name), ``caption_token`` (the
event, the key in ``citadel_generated_vo_english.txt``), ``file`` (the vsnd),
``current_caption`` (what the game shows; empty if it has none),
``suggested_text`` (the replacement, in the spoken language),
``suggested_translation`` (English), ``note`` (``;``-joined, in this order:
"no caption in game", the spoken language where it isn't the one the caption
names, Ivy's pre-rename name, "verified by ear" for the owner's own
transcriptions, then the doubt). RFC 4180 quoting, UTF-8 with a BOM (Excel
needs it to show Japanese), CRLF line ends.
"""

import csv
import io
import re
import sys
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path

from . import loc
from .dlls_tsv import uncell
from .vo_asr import load_lines

HEADER = (
    "hero",
    "caption_token",
    "file",
    "current_caption",
    "suggested_text",
    "suggested_translation",
    "note",
)
OWNER = "@bukzor"
"""``foreign.tsv`` ``source`` of a row the owner transcribed by ear."""
SPOKEN_OTHER = {"tengu_unselect_03_02_hero_3d": "Spanish"}
"""Uncaptioned clips whose language is not English (a fact heard, not derived)."""
TENGU_PING = "_tengu_ping_2d"
"""Ivy's pings that name her: she says her pre-rename name."""

Row = tuple[str, str, str, str, str, str, str]

ASR = "speech recognition"
BIGGER = "a larger speech model"
BOTH = f"{ASR} and {BIGGER} both heard"
DOUBT_FORMS = (
    (
        re.compile(r"small: (.+?); turbo: (.+?)(?=;|$)"),
        rf'{ASR} heard "\1"; {BIGGER} heard "\2"',
    ),
    (re.compile(r"small and turbo both hear '(.+?)'(?=;|$)"), rf'{BOTH} "\1"'),
    (re.compile(r"both models hear ([^\s;]+)"), rf'{BOTH} "\1"'),
    (re.compile(r"small only"), f"only {ASR} heard it"),
)
"""Our whisper model names, rewritten for forum readers; the first match wins."""


def plain_doubt(doubt: str) -> str:
    """A fix-up's ``doubt`` for forum readers; a text fitting no form passes through.

    >>> plain_doubt("small: BOWBACK; turbo: Bow back")
    'Unsure: speech recognition heard "BOWBACK"; a larger speech model heard "Bow back"'
    """
    for form, replacement in DOUBT_FORMS:
        if form.search(doubt):
            return "Unsure: " + form.sub(replacement, doubt, count=1)
    return f"Unsure: {doubt}"


def notes(row: Mapping[str, str], caption: str, text: str) -> str:
    parts: list[str] = []
    if not caption:
        parts.append("no caption in game")
    if row["event"] in SPOKEN_OTHER:
        parts.append(f"spoken in {SPOKEN_OTHER[row['event']]}")
    if row["hero"] == "tengu" and TENGU_PING in row["event"] and "Tengu" in text:
        parts.append("she says her pre-rename name, Tengu")
    if row["source"] == OWNER:
        parts.append("verified by ear")
    doubt = uncell(row["doubt"]) or ""
    if doubt:
        parts.append(plain_doubt(doubt))
    return "; ".join(parts)


def rows(
    foreign: Iterable[Mapping[str, str]],
    lines: Iterable[Mapping[str, str]],
    names: Mapping[str, str],
) -> Iterator[Row]:
    captions = {line["vsnd"]: line["english"] for line in lines}
    out: list[Row] = []
    for row in foreign:
        hero = loc.look_up(names, f"hero_{row['hero']}")
        assert hero, row["hero"]
        caption = captions[row["vsnd"]]
        text = uncell(row["replacement"]) or ""
        out.append(
            (
                hero,
                row["event"],
                row["vsnd"],
                caption,
                text,
                uncell(row["translation"]) or "",
                notes(row, caption, text),
            )
        )
    yield from sorted(out, key=lambda r: (r[0], r[1]))


def render(table: Iterable[Row]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(HEADER)
    writer.writerows(table)
    return "﻿" + buffer.getvalue()


def main(argv: list[str] | None = None) -> None:
    foreign_file, lines_file, names_file = map(
        Path, (sys.argv if argv is None else argv)[1:]
    )
    with names_file.open(encoding="utf-8-sig") as name_lines:
        names = loc.tokens(name_lines)
    table = rows(load_lines(foreign_file), load_lines(lines_file), names)
    _ = sys.stdout.buffer.write(render(table).encode("utf-8"))


if __name__ == "__main__":
    main()
