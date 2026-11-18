"""Shared type definitions."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

type Json = None | bool | int | float | str | Sequence[Json] | Mapping[str, Json]
type JsonObj = Mapping[str, Json]
type Kind = Literal["gun", "melee", "cast"]  # the source that models an ability
type Params = Mapping[str, str]  # a query's arguments: URL query string or CLI key=value


class BadRequest(ValueError):
    """The caller asked for something that doesn't exist or can't be parsed."""


@dataclass(frozen=True)
class Query:
    """One named query of the JSONL protocol (``docs/dev/decisions.kb/vis-app.md``, "Protocol").

    ``params`` is every parameter ``run`` accepts, as ``{name: description}``;
    a description says the unit and the default, or that the parameter is
    required. ``run`` returns the response's lines, each a JSON object, in
    order. It raises ``BadRequest`` for an unknown, missing or unparseable
    parameter, or a value that names nothing in the data; any other exception
    is a bug.
    """

    params: Mapping[str, str]
    run: Callable[[Params], Sequence[JsonObj]]
