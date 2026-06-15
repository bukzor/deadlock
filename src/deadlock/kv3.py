"""Load KV3 (KeyValues3) data into native Python via the keyvalues3 library.

KV3 holds Deadlock's game data (heroes, abilities, modifiers, …). Source 2
stores it as a binary block inside ``vdata_c``; decompiling with VRF yields text
KV3 (see ``deadlock.extract``), which this module reads back into Python.

The root of a game-data file is always a mapping; ``load`` asserts that and
returns it, so callers narrow from a known shape rather than ``object``.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import TypeGuard

import keyvalues3 as kv3


def _is_str_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping)


def load(path: Path) -> Mapping[str, object]:
    """Read a KV3 file and return its root mapping."""
    root = kv3.read(path).value
    assert _is_str_mapping(root), type(root)
    return root
