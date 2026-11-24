"""CLI: one TSV row per hero VO clip, on stdout.

    python -m bukzor_deadlock.vo_lines <soundevents_dir> <sounds_vo_dir> <english_captions>

``soundevents_dir`` holds VRF-decompiled ``generated_vo_hero_<hero>.vsndevts``
(other files there are ignored); ``sounds_vo_dir`` is the exploded VPK
directory ``sounds/vo``; ``english_captions`` is
``citadel_generated_vo_english.txt``.

Columns: ``hero``, ``event`` (the sound event, which is also its caption
token), ``vsnd`` (the clip as the event names it), ``crc32`` (of the shipped
``.vsnd_c``, 8 hex digits: the key for anything derived from the audio;
empty for a clip the paks don't ship), and
``english`` (the English caption as a ``dlls_tsv.cell``, empty when there is
none). Sorted by hero,
then event; an event with several clips gets one row each, in the event's
order. Other locales' captions are ``bukzor_deadlock.vo_captions``' table,
joined on ``event``.
"""

from __future__ import annotations

import sys
import zlib
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path

from . import vo_captions, vo_soundevents
from .dlls_tsv import cell

HEADER = ("hero", "event", "vsnd", "crc32", "english")
VO = "sounds/vo/"

Clip = tuple[str, str]
Row = tuple[str, str, str, str, str]


def audio_file(sounds_vo_dir: Path, vsnd: str) -> Path:
    """Where the exploded tree holds the compiled clip an event names."""
    assert vsnd.startswith(VO) and vsnd.endswith(".vsnd"), vsnd
    return sounds_vo_dir / f"{vsnd.removeprefix(VO)}_c"


def rows(
    clips: Mapping[str, Sequence[Clip]],
    crc_of: Callable[[str], int | None],
    english: Mapping[str, str],
) -> Iterator[Row]:
    """The table's rows: each hero's clips with CRC and English caption."""
    for hero in sorted(clips):
        for event, vsnd in clips[hero]:
            crc = crc_of(vsnd)
            hex8 = "" if crc is None else f"{crc:08x}"
            yield (hero, event, vsnd, hex8, cell(english.get(event, "")))


def load_clips(soundevents_dir: Path) -> dict[str, list[Clip]]:
    """Every hero's clips, by hero (impure: reads the decompiled files)."""
    return {
        vo_soundevents.hero_of(path): vo_soundevents.clips(vo_soundevents.load(path))
        for path in sorted(soundevents_dir.glob(f"{vo_soundevents.PREFIX}*.vsndevts"))
    }


def main(argv: list[str]) -> None:
    soundevents_dir, sounds_vo_dir, english_file = argv[1:]
    english = vo_captions.tokens(Path(english_file).read_text(encoding="utf-8-sig"))

    def crc_of(vsnd: str) -> int | None:
        path = audio_file(Path(sounds_vo_dir), vsnd)
        return zlib.crc32(path.read_bytes()) if path.exists() else None

    out = sys.stdout
    _ = out.write("\t".join(HEADER) + "\n")
    for row in rows(load_clips(Path(soundevents_dir)), crc_of, english):
        _ = out.write("\t".join(row) + "\n")


if __name__ == "__main__":
    main(sys.argv)
