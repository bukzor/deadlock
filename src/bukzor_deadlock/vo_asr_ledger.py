"""The ASR ledger: one hero's whisper transcripts, ``transcripts/asr/<hero>.tsv``.

Columns: ``crc32`` (the clip's key, from ``data/vo/lines.tsv``), ``vsnd`` (the
clip's name, a label only), ``model`` (a ``vo_asr.MODELS`` id, naming the decode
flags too), ``text`` (whisper's output, a ``dlls_tsv.cell``; empty when it heard
nothing). One row per clip and model, sorted by ``vsnd`` then ``model``.

The ledger is an observation, committed, never a redo output
(``docs/dev/decisions.kb/ml-observations-are-committed-ledgers.md``).
"""

from collections.abc import Iterable, Mapping, Sequence
from typing import NamedTuple

from .dlls_tsv import cell, uncell

HEADER = ("crc32", "vsnd", "model", "text")
SPEAKS_JAPANESE = "Speaks Japanese"
EMOTE = "/emote/"


class Clip(NamedTuple):
    crc32: str
    vsnd: str


class Row(NamedTuple):
    crc32: str
    vsnd: str
    model: str
    text: str


def clips(lines: Iterable[Mapping[str, str]], hero: str) -> list[Clip]:
    """The hero's clips in ASR scope, one per CRC (its first name), by name.

    In scope: clips captioned "Speaks Japanese", and, for a hero with any such
    clip, the uncaptioned clips outside ``emote/`` (grunts). A clip the paks
    don't ship (no CRC) is out.
    """
    mine = [line for line in lines if line["hero"] == hero and line["crc32"]]
    if not any(line["english"] == SPEAKS_JAPANESE for line in mine):
        return []
    by_crc: dict[str, str] = {}
    for line in mine:
        english, vsnd = line["english"], line["vsnd"]
        if english == SPEAKS_JAPANESE or (not english and EMOTE not in vsnd):
            by_crc[line["crc32"]] = min(vsnd, by_crc.get(line["crc32"], vsnd))
    return sorted(Clip(crc32, vsnd) for crc32, vsnd in by_crc.items())


def pending(wanted: Sequence[Clip], ledger: Iterable[Row], model: str) -> list[Clip]:
    """The wanted clips that have no row for ``model``."""
    done = {row.crc32 for row in ledger if row.model == model}
    return [clip for clip in wanted if clip.crc32 not in done]


def merge(old: Iterable[Row], new: Iterable[Row], wanted: Iterable[Clip]) -> list[Row]:
    """The ledger after ``new``: a new row replaces its clip and model's old one,
    rows of clips no longer wanted are dropped (git history keeps them), and
    each row takes its clip's current name."""
    name = {clip.crc32: clip.vsnd for clip in wanted}
    rows = {(row.crc32, row.model): row for row in (*old, *new)}
    kept = [
        row._replace(vsnd=name[row.crc32]) for row in rows.values() if row.crc32 in name
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
