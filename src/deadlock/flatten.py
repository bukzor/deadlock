"""Re-grain nested data to one leaf value per line (a git-trackable grain).

A nested record serialized as one JSON object per line makes huge lines, so a
single changed field rewrites the whole line and ``git diff`` can't show what
actually changed. Flattening to ``(path, value)`` leaves puts each scalar on its
own line: a change touches exactly one line and names both the path and the
value. This is the "grain-adjustment" step that turns bulky structured data into
files git tracks usefully.

Input must already be JSON-native (see ``deadlock.jsonl.to_jsonable``); empty
containers are emitted as their own leaf so they aren't silently dropped.
"""

from collections.abc import Iterator

from .types import is_sequence, is_str_mapping


def leaves(value: object, prefix: str = "") -> Iterator[tuple[str, object]]:
    """Yield ``(path, scalar)`` for every leaf, depth-first in source order."""
    if is_str_mapping(value):
        if not value:
            yield prefix, {}
            return
        for key, child in value.items():
            yield from leaves(child, f"{prefix}.{key}" if prefix else key)
    elif is_sequence(value):
        if not value:
            yield prefix, []
            return
        for index, item in enumerate(value):
            yield from leaves(item, f"{prefix}[{index}]")
    else:
        yield prefix, value
