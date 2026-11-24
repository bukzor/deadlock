"""CLI: every VO caption in every locale, as one long TSV on stdout.

    python -m bukzor_deadlock.vo_captions <caption_dir>

``caption_dir`` holds ``citadel_generated_vo_<lang>.txt``. Output columns are
``event``, ``lang``, ``caption``, one row per (event, lang) that has a
caption, sorted. A caption token is its sound event's name. The format is in
``docs/dev/formats.kb/vo-captions.md``.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator, Mapping
from pathlib import Path

import vdf

from .dlls_tsv import cell
from .types import is_str_mapping

PREFIX = "citadel_generated_vo_"
HEADER = ("event", "lang", "caption")


def tokens(text: str) -> dict[str, str]:
    """A caption file's ``{token: caption}`` table, escapes (``\\"``) undone."""
    root: object = vdf.loads(text)
    assert is_str_mapping(root), type(root)
    [lang] = root.values()
    assert is_str_mapping(lang), lang
    table = lang["Tokens"]
    assert is_str_mapping(table), table
    out: dict[str, str] = {}
    for token, caption in table.items():
        assert isinstance(caption, str), (token, caption)
        out[token] = caption
    return out


def lang_of(path: Path) -> str:
    """The locale named by a caption file's name."""
    assert path.stem.startswith(PREFIX), path
    return path.stem.removeprefix(PREFIX)


def rows(tables: Mapping[str, Mapping[str, str]]) -> Iterator[tuple[str, str, str]]:
    """``(event, lang, caption)`` for every caption, sorted by event then lang.

    A caption is a ``dlls_tsv.cell``: a newline in one renders as ``\\n``.
    """
    return iter(
        sorted(
            (token, lang, cell(caption))
            for lang, table in tables.items()
            for token, caption in table.items()
        )
    )


def load_tables(caption_dir: Path) -> dict[str, dict[str, str]]:
    """Every locale's token table in ``caption_dir``, by locale."""
    return {
        lang_of(path): tokens(path.read_text(encoding="utf-8-sig"))
        for path in sorted(caption_dir.glob(f"{PREFIX}*.txt"))
    }


def main(argv: list[str]) -> None:
    [caption_dir] = argv[1:]
    out = sys.stdout
    _ = out.write("\t".join(HEADER) + "\n")
    for row in rows(load_tables(Path(caption_dir))):
        _ = out.write("\t".join(row) + "\n")


if __name__ == "__main__":
    main(sys.argv)
