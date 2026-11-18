"""Shared type definitions."""

from collections.abc import Mapping, Sequence

type Json = None | bool | int | float | str | Sequence[Json] | Mapping[str, Json]
type JsonObj = Mapping[str, Json]
type Params = Mapping[str, str]  # a query's arguments: URL query string or CLI key=value


class BadRequest(ValueError):
    """The caller asked for something that doesn't exist or can't be parsed."""
