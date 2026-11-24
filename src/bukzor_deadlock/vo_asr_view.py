"""CLI: the Japanese VO lines with their best text, on stdout (``data/vo/japanese.tsv``).

    python -m bukzor_deadlock.vo_asr_view <lines.tsv> <asr_dir> <fixups.tsv>

Joins ``data/vo/lines.tsv``, each hero's ASR ledger ``<asr_dir>/<hero>.tsv``
(``vo_asr_ledger``) and the fix-ups, ``transcripts/fixups.tsv``, which may not
exist yet. Columns: ``hero event vsnd replacement translation source``, one
row per in-scope event of a hero that has a ledger, in ``lines.tsv`` order.

A clip's text is the fix-up of the strongest model's ASR text that has one,
and ``source`` is the fix-up's ``by``. Until a fix-up lands, ``replacement``
is the strongest model's raw ASR text, ``translation`` is empty, and
``source`` is that model's id (ids hold a ``/``; ``by`` values don't). A clip
with no ASR yet has three empty cells.

``fixups.tsv`` columns: ``asr_text replacement translation doubt by``, every
cell a ``dlls_tsv.cell``, keyed by ``asr_text``. The design:
``docs/dev/decisions.kb/ml-observations-are-committed-ledgers.md``.
"""

import sys
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import NamedTuple

from .dlls_tsv import cell, uncell
from .vo_asr import MODELS, load_lines
from .vo_asr_ledger import Row, clips, parse

HEADER = ("hero", "event", "vsnd", "replacement", "translation", "source")
FIXUP_HEADER = ("asr_text", "replacement", "translation", "doubt", "by")
STRENGTH = {model.id: rank for rank, model in enumerate(MODELS.values())}


class Fixup(NamedTuple):
    replacement: str
    translation: str
    doubt: str
    by: str


def best(asr: Sequence[Row], fixups: Mapping[str, Fixup]) -> tuple[str, str, str]:
    """``(replacement, translation, source)`` for one clip's ASR rows."""
    for row in asr:
        assert row.model in STRENGTH, row
    ranked = sorted(asr, key=lambda row: STRENGTH[row.model], reverse=True)
    for row in ranked:
        if row.text in fixups:
            fixup = fixups[row.text]
            return fixup.replacement, fixup.translation, fixup.by
    if ranked:
        return ranked[0].text, "", ranked[0].model
    else:
        return "", "", ""


def rows(
    lines: Iterable[Mapping[str, str]],
    ledgers: Mapping[str, Sequence[Row]],
    fixups: Mapping[str, Fixup],
) -> Iterator[tuple[str, str, str, str, str, str]]:
    lines = list(lines)
    by_hero = {hero: {clip.crc32 for clip in clips(lines, hero)} for hero in ledgers}
    for line in lines:
        hero, crc32 = line["hero"], line["crc32"]
        if crc32 not in by_hero.get(hero, ()):
            continue
        asr = [row for row in ledgers[hero] if row.crc32 == crc32]
        replacement, translation, source = best(asr, fixups)
        yield (
            hero,
            line["event"],
            line["vsnd"],
            cell(replacement),
            cell(translation),
            source,
        )


def parse_fixups(text: str) -> dict[str, Fixup]:
    header, *lines = text.splitlines()
    assert tuple(header.split("\t")) == FIXUP_HEADER, header
    fixups: dict[str, Fixup] = {}
    for line in lines:
        cells = [uncell(value) for value in line.split("\t")]
        asr_text, replacement, translation, doubt, by = [c or "" for c in cells]
        fixups[asr_text] = Fixup(replacement, translation, doubt, by)
    return fixups


def main(argv: list[str] | None = None) -> None:
    lines_file, asr_dir, fixups_file = map(
        Path, (sys.argv if argv is None else argv)[1:]
    )
    ledgers = {
        path.stem: parse(path.read_text()) for path in sorted(asr_dir.glob("*.tsv"))
    }
    fixups = parse_fixups(fixups_file.read_text()) if fixups_file.exists() else {}
    out = sys.stdout
    _ = out.write("\t".join(HEADER) + "\n")
    for row in rows(load_lines(lines_file), ledgers, fixups):
        _ = out.write("\t".join(row) + "\n")


if __name__ == "__main__":
    main()
