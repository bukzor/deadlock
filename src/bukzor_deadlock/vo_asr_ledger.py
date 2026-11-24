"""The ASR ledger: one hero's whisper transcripts, ``transcripts/asr/<hero>.tsv``.

Columns: ``crc32`` (the clip's key, from ``data/vo/lines.tsv``), ``vsnd`` (the
clip's name, a label only), ``model`` (a ``vo_asr.MODELS`` id, naming the decode
flags too), ``text`` (whisper's output, a ``dlls_tsv.cell``; empty when it heard
nothing). One row per clip and model, sorted by ``vsnd`` then ``model``.

The ledger is an observation, committed, never a redo output
(``docs/dev/decisions.kb/ml-observations-are-committed-ledgers.md``).
"""

import re
from collections.abc import Iterable, Mapping, Sequence
from typing import NamedTuple

from .dlls_tsv import cell, uncell

HEADER = ("crc32", "vsnd", "model", "text")
SPEAKS = re.compile(r"speaks (\w+)", re.IGNORECASE)
"""A caption that names the language spoken instead of transcribing it."""
LANGUAGES = {"japanese": "ja", "spanish": "es", "french": "fr"}
"""Caption language to whisper's ``-l`` code."""
AUTO = "auto"
"""whisper's ``-l`` for language detection, one per encoder window."""
PINNED_UNCAPTIONED = {"yamato": "ja"}
"""Heroes whose uncaptioned clips are pinned to a language, not detected:
Yamato's are alternate takes of her Japanese lines."""
EMOTE = "/emote/"


class Clip(NamedTuple):
    crc32: str
    vsnd: str
    lang: str
    """whisper's ``-l`` code, or ``AUTO``."""


def speaks(english: str) -> str | None:
    """The whisper code of a "Speaks <language>" caption, else None.

    >>> speaks("Speaks spanish"), speaks("My reputation speaks for itself.")
    ('es', None)
    """
    match = SPEAKS.fullmatch(english)
    if match is None:
        return None
    language = match[1].lower()
    assert language in LANGUAGES, ("no whisper code", language)
    return LANGUAGES[language]


class Row(NamedTuple):
    crc32: str
    vsnd: str
    model: str
    text: str


def clips(lines: Iterable[Mapping[str, str]], hero: str) -> list[Clip]:
    """The hero's clips in ASR scope, one per CRC (its first name), by name.

    In scope: clips captioned "Speaks <language>", pinned to that language,
    and, for a hero with any such clip, the uncaptioned clips outside
    ``emote/`` (grunts), whose language is detected (``AUTO``) unless the
    hero is in ``PINNED_UNCAPTIONED``. A clip the paks don't ship (no CRC) is
    out.
    """
    mine = [line for line in lines if line["hero"] == hero and line["crc32"]]
    if not any(speaks(line["english"]) for line in mine):
        return []
    uncaptioned = PINNED_UNCAPTIONED.get(hero, AUTO)
    by_crc: dict[str, Clip] = {}
    for line in mine:
        english, vsnd, crc32 = line["english"], line["vsnd"], line["crc32"]
        lang = speaks(english) or (
            uncaptioned if not english and EMOTE not in vsnd else None
        )
        if lang and (crc32 not in by_crc or vsnd < by_crc[crc32].vsnd):
            by_crc[crc32] = Clip(crc32, vsnd, lang)
    return sorted(by_crc.values())


def decoded_id(model_id: str, lang: str) -> str:
    """The ledger's ``model`` cell for a clip decoded with ``lang``: it names
    language detection, so detected and pinned rows never mix.

    >>> decoded_id("small/dtw/greedy", "auto"), decoded_id("small/dtw/greedy", "ja")
    ('small/dtw/greedy/auto', 'small/dtw/greedy')
    """
    return f"{model_id}/{AUTO}" if lang == AUTO else model_id


def pending(wanted: Sequence[Clip], ledger: Iterable[Row], model: str) -> list[Clip]:
    """The wanted clips that have no row for ``model``, decoded as each wants."""
    done = {(row.crc32, row.model) for row in ledger}
    return [
        clip
        for clip in wanted
        if (clip.crc32, decoded_id(model, clip.lang)) not in done
    ]


def merge(old: Iterable[Row], new: Iterable[Row], wanted: Iterable[Clip]) -> list[Row]:
    """The ledger after ``new``: a new row replaces its clip and model's old one,
    rows of clips no longer wanted, or decoded unlike their clip (detected
    against pinned), are dropped (git history keeps them), and each row takes
    its clip's current name."""
    clip = {c.crc32: c for c in wanted}
    rows = {(row.crc32, row.model): row for row in (*old, *new)}
    kept = [
        row._replace(vsnd=clip[row.crc32].vsnd)
        for row in rows.values()
        if row.crc32 in clip
        and row.model.endswith(f"/{AUTO}") == (clip[row.crc32].lang == AUTO)
    ]
    return sorted(kept, key=lambda row: (row.vsnd, row.model))


def render(rows: Iterable[Row]) -> str:
    lines = ["\t".join(HEADER)]
    lines += ["\t".join((*row[:3], cell(row.text))) for row in rows]
    return "\n".join(lines) + "\n"


def parse(text: str) -> list[Row]:
    header, *lines = text.splitlines()
    assert tuple(header.split("\t")) == HEADER, header
    rows: list[Row] = []
    for line in lines:
        crc32, vsnd, model, value = line.split("\t")
        unescaped = uncell(value)
        assert unescaped is not None, line
        rows.append(Row(crc32, vsnd, model, unescaped))
    return rows
