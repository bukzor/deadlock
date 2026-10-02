"""Shared type definitions and narrowing guards.

Parsed KV3 / JSON data arrives as ``object``; these ``TypeGuard``s narrow it to
known structural types at each access step (preferred over ``cast``).
"""

from collections.abc import Iterator, Mapping, Sequence
from typing import TypeGuard

type Line = str  # newline-terminated
type Lines = Iterator[Line]


def is_str_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping)


def is_sequence(value: object) -> TypeGuard[Sequence[object]]:
    """True for list/tuple sequences (not str/bytes, which are also Sequences)."""
    return isinstance(value, (list, tuple))


def dig(node: object, *keys: str) -> object:
    """Follow ``keys`` through nested mappings; ``None`` if the path ends early."""
    for key in keys:
        if not is_str_mapping(node):
            return None
        node = node.get(key)
    return node
