"""Shared type definitions and narrowing guards.

Parsed KV3 / JSON data arrives as ``object``; these ``TypeGuard``s narrow it to
known structural types at each access step (preferred over ``cast``).
"""

from collections.abc import Mapping, Sequence
from typing import TypeGuard


def is_str_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping)


def is_sequence(value: object) -> TypeGuard[Sequence[object]]:
    """True for list/tuple sequences (not str/bytes, which are also Sequences)."""
    return isinstance(value, (list, tuple))
