"""Re-grain nested data to one leaf value per line (a git-trackable grain).

A nested record serialized as one JSON object per line makes huge lines, so a
single changed field rewrites the whole line and ``git diff`` can't show what
actually changed. Flattening to ``(path, value)`` leaves puts each scalar on its
own line: a change touches exactly one line and names both the path and the
value. This is the "grain-adjustment" step that turns bulky structured data into
files git tracks usefully.

Input must already be JSON-native (see ``deadlock.jsonl.to_jsonable``); empty
containers are emitted as their own leaf so they aren't silently dropped.

``unflatten`` is the inverse, for consumers that want the structure back rather
than regexes over path strings. A mapping key that is empty or contains ``.``,
``[`` or ``]`` would be indistinguishable from structure, so it is written as a
JSON string in brackets (``["Impact.Concrete"].x``); other keys are unchanged.
Mapping key order is not preserved (the flat files are sorted), and rows may
arrive in any order.
"""

import json
import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field

import typed_json

from .types import is_sequence, is_str_mapping

_STEP = re.compile(r'(?:^|\.)([^.\[\]]+)|\[(\d+)\]|\[("(?:[^"\\]|\\.)*")\]')
_HOLE = object()


def leaves(value: object, prefix: str = "") -> Iterator[tuple[str, object]]:
    """Yield ``(path, scalar)`` for every leaf, depth-first in source order."""
    if is_str_mapping(value):
        if not value:
            yield prefix, {}
            return
        for key, child in value.items():
            yield from leaves(child, _join(prefix, key))
    elif is_sequence(value):
        if not value:
            yield prefix, []
            return
        for index, item in enumerate(value):
            yield from leaves(item, f"{prefix}[{index}]")
    else:
        yield prefix, value


def _join(prefix: str, key: str) -> str:
    if key and not set(key) & set(".[]"):
        return f"{prefix}.{key}" if prefix else key
    return f"{prefix}[{json.dumps(key, ensure_ascii=False)}]"


@dataclass
class _Node:
    children: dict[str | int, "_Node"] = field(default_factory=dict)
    leaf: object = _HOLE


def unflatten(rows: Iterable[tuple[str, object]]) -> object:
    """Rebuild the nested value from ``(path, scalar)`` rows; inverse of ``leaves``."""
    root = _Node()
    for path, value in rows:
        node = root
        for step in _steps(path):
            node = node.children.setdefault(step, _Node())
        assert node.leaf is _HOLE, path
        node.leaf = value
    return _build(root, "")


def tree(records: Iterable[Mapping[str, object]]) -> Mapping[str, object]:
    """Unflatten JSONL ``{"path", "value"}`` records into the root mapping."""
    root = unflatten(_pair(record) for record in records)
    assert is_str_mapping(root), type(root)
    return root


def _pair(record: Mapping[str, object]) -> tuple[str, object]:
    path = record["path"]
    assert isinstance(path, str), path
    return path, record["value"]


def _steps(path: str) -> list[str | int]:
    """Split ``a.b[0].c`` into ``["a", "b", 0, "c"]``; assert it all parses."""
    matches = list(_STEP.finditer(path))
    assert sum(len(match.group()) for match in matches) == len(path), path
    return [_step(match) for match in matches]


def _step(match: re.Match[str]) -> str | int:
    bare, index, quoted = match.groups()
    if bare is not None:
        return bare
    if index is not None:
        return int(index)
    key = typed_json.loads(quoted)
    assert isinstance(key, str), key
    return key


def _build(node: _Node, path: str) -> object:
    if node.leaf is not _HOLE:
        assert not node.children, path
        return node.leaf
    assert node.children, path
    keys = list(node.children)
    if all(isinstance(key, int) for key in keys):
        assert sorted(keys) == list(range(len(keys))), (path, keys)
        return [_build(node.children[index], f"{path}[{index}]") for index in range(len(keys))]
    assert all(isinstance(key, str) for key in keys), (path, keys)
    return {str(key): _build(child, f"{path}.{key}" if path else str(key)) for key, child in node.children.items()}
