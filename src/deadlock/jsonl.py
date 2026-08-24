"""Render values as JSONL (one compact, key-sorted JSON object per line).

JSONL is the project's preferred shape for usable data: line-oriented, so it
streams, greps, and diffs well. ``to_jsonable`` also flattens the KV3-specific
``flagged_value`` wrapper down to its underlying value, so decompiled game data
serializes cleanly.
"""

from __future__ import annotations

import json
from collections.abc import Iterable

import keyvalues3 as kv3

from .types import Lines, is_sequence, is_str_mapping


def to_jsonable(value: object) -> object:
    """Recursively convert KV3/native values into JSON-serializable form."""
    if isinstance(value, kv3.flagged_value):
        return to_jsonable(value.value)
    if is_str_mapping(value):
        return {k: to_jsonable(v) for k, v in value.items()}
    if is_sequence(value):
        return [to_jsonable(v) for v in value]
    return value


def dumps(obj: object) -> str:
    """Serialize one value to a single compact, key-sorted JSON line (no newline)."""
    return json.dumps(to_jsonable(obj), separators=(",", ":"), sort_keys=True)


def dump_lines(objs: Iterable[object]) -> Lines:
    """Serialize values to JSONL lines (one newline-terminated line per object)."""
    return (dumps(o) + "\n" for o in objs)
