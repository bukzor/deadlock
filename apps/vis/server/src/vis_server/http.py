"""The HTTP side of the JSONL protocol (``docs/dev/decisions.kb/vis-app.md``, "Protocol").

``GET /api`` lists the queries; ``GET /api/{query}?k=v`` answers one. Both
answer ``application/jsonl`` in ``jsonl``'s bytes, which the CLI prints too.
The built client, when present, is served at ``/``.
"""

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from deadlock.jsonl import dump_lines
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route
from starlette.staticfiles import StaticFiles

from .queries import QUERIES
from .types import BadRequest, JsonObj, Query

CLIENT = Path(__file__).parents[3] / "client/dist"
MEDIA_TYPE = "application/jsonl"


def app(queries: Mapping[str, Query] = QUERIES, client: Path = CLIENT) -> Starlette:
    """The API over ``queries``, plus ``client`` (Vite's build) at ``/`` if that directory exists then.

    A ``BadRequest`` is a 400 and an unknown query a 404, each one ``{"error"}``
    line; any other exception propagates, as a 500.
    """

    async def index(_: Request) -> Response:
        return _response(200, listing(queries))

    async def query(request: Request) -> Response:
        match request.path_params:
            case {"query": str(name)}:
                return _response(*answer(queries, name, request.query_params.multi_items()))
            case unmatched:
                raise AssertionError(unmatched)

    routes: list[BaseRoute] = [Route("/api", index), Route("/api/{query}", query)]
    if client.is_dir():
        routes.append(Mount("/", StaticFiles(directory=client, html=True)))
    return Starlette(routes=routes)


def listing(queries: Mapping[str, Query]) -> list[JsonObj]:
    """``{"query", "params"}`` for each query, in the registry's order."""
    return [{"query": name, "params": query.params} for name, query in queries.items()]


def answer(queries: Mapping[str, Query], name: str, pairs: Iterable[tuple[str, str]]) -> tuple[int, Sequence[JsonObj]]:
    """``(HTTP status, lines)`` for query ``name`` given ``pairs`` of parameters; the CLI's answer too.

    200 with the query's lines; 400 (a ``BadRequest``, including a repeated
    parameter) or 404 (no such query) with one ``{"error"}`` line.
    """
    if name not in queries:
        return 404, [_error(f"unknown query: {name} (accepted: {', '.join(queries)})")]
    try:
        return 200, queries[name].run(_params(pairs))
    except BadRequest as bad:
        return 400, [_error(str(bad))]


def _params(pairs: Iterable[tuple[str, str]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, value in pairs:
        if name in result:
            raise BadRequest(f"repeated parameter: {name}")
        result[name] = value
    return result


def _error(message: str) -> JsonObj:
    return {"error": message}


def jsonl(lines: Iterable[JsonObj]) -> str:
    """The response body: each line compact and key-sorted (``deadlock.jsonl.dumps``), newline-terminated."""
    return "".join(dump_lines(lines))


def _response(status: int, lines: Sequence[JsonObj]) -> Response:
    return Response(jsonl(lines), status_code=status, media_type=MEDIA_TYPE)
