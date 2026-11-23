"""Read a Valve localization file (``*_english.txt``) as a flat token table.

These files are KV1 text: a ``"lang"`` block wrapping ``"Tokens"``, whose body
is one ``"token" "translation"`` pair per line (UTF-8 BOM, CRLF, ``//``
comments). We want only the mapping, so this parser stays deliberately dumb —
it collects every quoted pair and ignores the block structure entirely. Nesting
never repeats a key here, and a duplicate would be a surprise worth failing on.
Open the file as ``utf-8-sig``; the BOM is the caller's problem, not ours.

Tokens carry a grammatical-case suffix (``hero_astro:n``, the nominative);
``look_up`` resolves a bare name through it. Translations are kept verbatim.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

_PAIR = re.compile(r'^\s*"([^"]*)"(?:\s*"([^"]*)")?\s*$')


def tokens(lines: Iterable[str]) -> dict[str, str]:
    """The ``{token: translation}`` table; a lone quoted string maps to ``""``.

    >>> tokens(['\\t\\t"hero_astro:n" "Holliday"\\r\\n'])
    {'hero_astro:n': 'Holliday'}
    """
    table: dict[str, str] = {}
    for line in lines:
        match = _PAIR.match(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        assert key not in table, (key, table[key], value)
        table[key] = value or ""
    return table


def look_up(tokens: Mapping[str, str], name: str) -> str | None:
    """One token's translation, preferring the nominative case; ``None`` if absent.

    >>> look_up({'hero_astro:n': 'Holliday'}, 'hero_astro')
    'Holliday'
    """
    return tokens.get(f"{name}:n", tokens.get(name))
