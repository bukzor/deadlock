"""Cells and document loading shared by the ``deadlock.dlls_<facet>`` views.

Each view turns one facet's per-DLL JSON documents (``data/dlls/<facet>/<dll>.json``)
into ``data/dlls/<facet>.tsv``, the facet's lossless aggregate. Cells use
PostgreSQL's ``COPY`` text format, so the TSV keeps everything the JSON holds:

- ``\\``, tab, newline and carriage return are escaped as ``\\\\``, ``\\t``,
  ``\\n``, ``\\r``: real help strings contain tabs, newlines and backslashes,
  and the scanner admits no other control characters.
- ``null`` is ``\\N``, and ``""`` is an empty cell. A help that is literally
  ``\\N`` renders as ``\\\\N``, so the two never collide.
- A list is its items joined by single spaces. Its items are names (flags,
  modules), asserted free of anything that would need escaping, so
  ``git diff --word-diff`` shows an added item as one added word.
"""

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import TypeGuard

import typed_json

from .types import is_sequence

NULL = "\\N"
_UNESCAPES = {"\\\\": "\\", "\\t": "\t", "\\n": "\n", "\\r": "\r"}
_ESCAPES = str.maketrans({raw: escaped for escaped, raw in _UNESCAPES.items()})


def cell(value: str | None) -> str:
    r"""One escaped cell; ``\N`` for ``None``.

    >>> cell("Heals the player.\n\tArguments: <health to gain>")
    'Heals the player.\\n\\tArguments: <health to gain>'
    """
    return NULL if value is None else value.translate(_ESCAPES)


def uncell(text: str) -> str | None:
    """The value ``cell`` rendered as ``text``; ``KeyError`` on an escape it
    never writes."""
    if text == NULL:
        return None
    return re.sub(r"\\.", lambda m: _UNESCAPES[m[0]], text)


def list_cell(items: Sequence[str]) -> str:
    """Space-joined names; an empty list is an empty cell."""
    for item in items:
        assert item and " " not in item and cell(item) == item, (item, items)
    return " ".join(items)


def unlist_cell(text: str) -> list[str]:
    """The items ``list_cell`` rendered as ``text``."""
    return text.split(" ") if text else []


def load_documents[D](paths: Iterable[str], is_document: Callable[[object], TypeGuard[D]]) -> Mapping[str, D]:
    """Read each ``<dll>.json`` document, keyed by its DLL basename; assert its shape."""
    documents: dict[str, D] = {}
    for path in map(Path, paths):
        dll = path.name.removesuffix(".json")
        assert dll != path.name, path
        assert dll not in documents, path
        document = typed_json.loads(path.read_text())
        assert is_document(document), (path, document)
        documents[dll] = document
    return documents


def is_str_sequence(value: object) -> TypeGuard[Sequence[str]]:
    return is_sequence(value) and all(isinstance(item, str) for item in value)
