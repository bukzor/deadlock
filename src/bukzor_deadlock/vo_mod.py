"""CLI: the caption mod's files, from ``data/vo/foreign.tsv``.

    python -m bukzor_deadlock.vo_mod <caption_dir> <foreign.tsv> <lines.tsv> \\
        <locale-translations.tsv> <out_dir>

``caption_dir`` is the game's ``citadel_generated_vo/``; the translations
ledger may not exist yet. Writes, for every real locale (a game file over
1 KB):

- ``<out_dir>/tree/resource/localization/citadel_generated_vo/citadel_generated_vo_<locale>.txt``:
  the mod's file, holding only our tokens, under the game file's own header.
- ``<out_dir>/diffs/<locale>.diff``: a unified diff from the game file to the
  game file with our tokens substituted in place (a token it lacks is
  appended), paths relative to the install root.

Every row with a fix-up (a non-empty ``translation``) is in every locale; a
row without one holds raw ASR text and is left out. Each written file is
parsed back with ``vo_captions.tokens`` and checked against what was meant,
and every token must be in the English game file or be an uncaptioned event
(empty ``english`` in ``lines.tsv``).
Layout and styling rules: ``docs/dev/formats.kb/caption-mod.md``.
"""

import difflib
import re
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path

from .dlls_tsv import uncell
from .vo_asr import load_lines
from .vo_captions import PREFIX, lang_of, tokens
from .vo_forum import SPOKEN_OTHER

BR = "<br>"
"""The line break the game's localization uses (no ``<cr>`` or ``\\n``)."""
NATIVE = {
    "ja": ("japanese",),
    "es": ("spanish", "latam"),
    "fr": ("french",),
    "en": ("english",),
}
"""The locales whose players read a spoken language: they get no bracket."""
LANG_OF_NAME = {"Spanish": "es"}
"""``vo_forum.SPOKEN_OTHER``'s language names as ``NATIVE`` keys."""
CAPTION_DIR = "resource/localization/citadel_generated_vo"
INSTALL_DIR = f"game/citadel/{CAPTION_DIR}"
REAL = 1024
"""Bytes above which a game caption file is a real locale, not a stub."""
ENTRY = re.compile(r'^\t\t"(?P<token>[^"\\]*)"\t\t"(?P<caption>(?:[^"\\]|\\.)*)"', re.M)
CLOSE = re.compile(r"^\t*\}\r\n\}\r\n\Z", re.M)
"""The end of the ``Tokens`` block and the file; its brace is indented once or twice."""


def spoken(row: Mapping[str, str]) -> str:
    """The ``NATIVE`` key of the language a row's clip speaks.

    Whisper's ``auto`` rows are English but for the heard exceptions; a ``ja``
    row in Latin script is English, by the replacement's orthography rule.
    """
    lang = row["lang"]
    if lang == "auto":
        other = SPOKEN_OTHER.get(row["event"])
        return "en" if other is None else LANG_OF_NAME[other]
    elif lang == "ja" and row["replacement"].isascii():
        return "en"
    else:
        assert lang in NATIVE, row
        return lang


def caption(
    row: Mapping[str, str], locale: str, translations: Mapping[tuple[str, str], str]
) -> str:
    """A row's caption in ``locale``: the spoken text, then on a new line its
    translation in brackets, unless the locale reads the spoken language or
    the translation only repeats the text.

    ``translations`` maps (English translation, locale) to that locale's
    text; English stands in where it has none.
    """
    text, english = row["replacement"], row["translation"]
    bracket = translations.get((english, locale), english)
    if locale in NATIVE[spoken(row)] or bracket == text:
        return text
    else:
        return f"{text}{BR}[{bracket}]"


def escape(text: str) -> str:
    r"""``text`` quoted the way the game's caption files quote it.

    >>> print(escape('a "b" \\ c'))
    "a \"b\" \\ c"
    """
    assert "\n" not in text and "\r" not in text, text
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def entry(token: str, text: str) -> str:
    return f"\t\t{escape(token)}\t\t{escape(text)}\r\n"


def render(game: str, ours: Mapping[str, str]) -> str:
    """A caption file holding only ``ours``, under ``game``'s header."""
    head = game[: game.index("\t{\r\n", game.index('"Tokens"')) + 4]
    return head + "".join(entry(t, c) for t, c in ours.items()) + game[close(game) :]


def substitute(game: str, ours: Mapping[str, str]) -> str:
    """``game`` with each of ``ours`` replaced in place; the tokens it lacks
    are appended, in ``ours``'s order. All else is kept byte for byte."""
    seen: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        token = match["token"]
        if token in ours:
            seen.add(token)
            return entry(token, ours[token]).removesuffix("\r\n")
        else:
            return match[0]

    out = ENTRY.sub(replace, game)
    end = close(out)
    added = "".join(entry(t, c) for t, c in ours.items() if t not in seen)
    return out[:end] + added + out[end:]


def close(text: str) -> int:
    """Where a caption file's closing braces start."""
    match = CLOSE.search(text)
    assert match, text[-20:]
    return match.start()


def diff(locale: str, game: str, changed: str) -> str:
    """A unified diff from ``game`` to ``changed``, split at ``\n`` only:
    ``str.splitlines`` also splits at characters a caption may hold."""
    path = f"{INSTALL_DIR}/{PREFIX}{locale}.txt"
    return "".join(
        difflib.unified_diff(
            re.split(r"(?<=\n)(?=.)", game, flags=re.S),
            re.split(r"(?<=\n)(?=.)", changed, flags=re.S),
            f"a/{path}",
            f"b/{path}",
        )
    )


def load_translations(path: Path) -> dict[tuple[str, str], str]:
    """The ``locale-translations.tsv`` ledger by (translation, locale); empty
    if it does not exist yet."""
    if not path.exists():
        return {}
    return {(r["translation"], r["locale"]): r["text"] for r in load_lines(path)}


def ready(foreign: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    """The rows with a fix-up, their cells unescaped."""
    out: list[dict[str, str]] = []
    for row in foreign:
        cells = {k: uncell(v) or "" for k, v in row.items()}
        if cells["translation"]:
            out.append(cells)
    return out


def write_locale(
    out_dir: Path, locale: str, game: str, ours: Mapping[str, str]
) -> None:
    mod_file = out_dir / "tree" / CAPTION_DIR / f"{PREFIX}{locale}.txt"
    mod_file.parent.mkdir(parents=True, exist_ok=True)
    _ = mod_file.write_bytes(render(game, ours).encode("utf-8"))
    changed = substitute(game, ours)
    diff_file = out_dir / "diffs" / f"{locale}.diff"
    diff_file.parent.mkdir(parents=True, exist_ok=True)
    _ = diff_file.write_bytes(diff(locale, game, changed).encode("utf-8"))
    check(mod_file.read_bytes().decode("utf-8-sig"), changed, game, ours)


def check(mod: str, changed: str, game: str, ours: Mapping[str, str]) -> None:
    """The mod file parses back to exactly ``ours``, and the substituted game
    file to the game's tokens updated by ``ours``."""
    assert tokens(mod) == ours, set(tokens(mod).items()) ^ set(ours.items())
    expected = tokens(game.removeprefix("\ufeff")) | dict(ours)
    assert tokens(changed.removeprefix("\ufeff")) == expected


def main(argv: list[str] | None = None) -> None:
    caption_dir, foreign_file, lines_file, translations_file, out_dir = map(
        Path, (sys.argv if argv is None else argv)[1:]
    )
    rows = ready(load_lines(foreign_file))
    uncaptioned = {r["event"] for r in load_lines(lines_file) if not r["english"]}
    english = (caption_dir / f"{PREFIX}english.txt").read_text(encoding="utf-8-sig")
    unknown = {r["event"] for r in rows} - tokens(english).keys() - uncaptioned
    assert not unknown, unknown
    translations = load_translations(translations_file)
    for path in sorted(caption_dir.glob(f"{PREFIX}*.txt")):
        if path.stat().st_size <= REAL:
            continue
        locale = lang_of(path)
        game = path.read_bytes().decode("utf-8")
        ours = {r["event"]: caption(r, locale, translations) for r in rows}
        write_locale(out_dir, locale, game, ours)
        print(f"{locale}: {len(ours)} tokens", file=sys.stderr)


if __name__ == "__main__":
    main()
