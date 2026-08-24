"""Load KV3 (KeyValues3) data into native Python.

KV3 holds Deadlock's game data (heroes, abilities, modifiers, …). Source 2
stores it as a binary block inside ``vdata_c``; decompiling with VRF yields text
KV3 (see ``deadlock.extract``), which this module reads back into Python via
``deadlock.kv3text`` (a fast reader for VRF's output subset — the ``keyvalues3``
library parses identically but ~25x slower; see kv3text's docstring).

The root of a game-data file is always a mapping; ``load`` asserts that and
returns it, so callers narrow from a known shape rather than ``object``.
"""

from collections.abc import Mapping
from pathlib import Path

from . import kv3text
from .types import is_str_mapping


def load(path: Path) -> Mapping[str, object]:
    """Read a KV3 file and return its root mapping."""
    root = kv3text.parse(path.read_text(encoding="utf-8"))
    assert is_str_mapping(root), type(root)
    return root
