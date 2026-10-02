"""Convert one decompiled KV3 game-data file to JSON.

    python -m deadlock.gamedata < scripts/heroes.vdata > scripts/heroes.json

A local cache, never committed (see
``docs/dev/decisions.kb/commit-diffable-data-let-git-diff.md``): the views
``load`` it rather than re-parse KV3, which is ~25x slower. Keys keep source
order and KV3 ``flagged_value`` wrappers are unwrapped. Indented, so the caches
from two builds ``diff`` usefully.
"""

import json
import sys
from collections.abc import Mapping
from typing import IO

import typed_json

from . import jsonl, kv3
from .types import is_str_mapping


def dumps(root: Mapping[str, object]) -> str:
    """Serialize a parsed game-data root, newline-terminated."""
    return json.dumps(jsonl.to_jsonable(root), indent=2) + "\n"


def load(file: IO[str]) -> Mapping[str, object]:
    """Read a game-data root written by ``dumps``."""
    root = typed_json.load(file)
    assert is_str_mapping(root), type(root)
    return root


def main() -> None:
    _ = sys.stdout.write(dumps(kv3.load(sys.stdin)))


if __name__ == "__main__":
    main()
