"""Read a hero's decompiled VO soundevents: event name to its ``vsnd`` files.

Input is VRF's KV3 text of ``soundevents/vo/generated_vo_hero_<hero>.vsndevts_c``:
a root mapping of event name to a block whose ``vsnd_files`` is one path or a
list of them (``sounds/vo/<hero>/<clip>.vsnd``, the source name of the shipped
``.vsnd_c``). A hero with no VO decompiles to a ``null`` root.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from . import kv3text
from .types import is_sequence, is_str_mapping

PREFIX = "generated_vo_hero_"


def hero_of(path: Path) -> str:
    """The hero codename a soundevents file is named for."""
    assert path.stem.startswith(PREFIX), path
    return path.stem.removeprefix(PREFIX)


def load(path: Path) -> object:
    """The decompiled file's root value (impure: reads the file)."""
    with path.open(encoding="utf-8") as lines:
        return kv3text.parse(lines)


def _files(event: Mapping[str, object]) -> list[str]:
    files = event.get("vsnd_files", [])
    if isinstance(files, str):
        return [files]
    else:
        assert is_sequence(files), files
        assert all(isinstance(f, str) for f in files), files
        return [str(f) for f in files]


def clips(root: object) -> list[tuple[str, str]]:
    """``(event, vsnd)`` per file of each event, by event name, files in order.

    An event with no ``vsnd_files`` contributes nothing.
    """
    if root is None:
        return []
    else:
        assert is_str_mapping(root), type(root)
        out: list[tuple[str, str]] = []
        for name in sorted(root):
            event = root[name]
            assert is_str_mapping(event), (name, event)
            out += [(name, vsnd) for vsnd in _files(event)]
        return out
