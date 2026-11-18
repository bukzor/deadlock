"""``vis-server``: ``serve`` the JSONL protocol over HTTP, or answer one ``query`` on stdout.

``vis-server query NAME k=v ...`` prints the same bytes ``GET /api/NAME?k=v``
answers. A bad request prints its ``{"error"}`` line to stderr and exits 2.
"""

import argparse
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

import deadlock
import uvicorn

from .http import answer, app, jsonl
from .queries import QUERIES
from .types import Query

# What ``serve --reload`` watches: this package and the ``deadlock`` one it reads.
RELOAD_DIRS = (Path(__file__).parent, Path(deadlock.__file__).parent)


class Args(argparse.Namespace):
    command: str = ""
    host: str = ""
    port: int = 0
    reload: bool = False
    name: str = ""
    params: list[tuple[str, str]] = []


def main(argv: Sequence[str] | None = None, queries: Mapping[str, Query] = QUERIES) -> int:
    """Run ``argv`` (default ``sys.argv[1:]``) against ``queries``; the exit status."""
    args = _parser().parse_args(argv, namespace=Args())
    match args.command:
        case "serve":
            if args.reload:
                # uvicorn restarts the worker on a source change, so it needs an import string.
                uvicorn.run(
                    "vis_server.http:app",
                    factory=True,
                    host=args.host,
                    port=args.port,
                    reload=True,
                    reload_dirs=[str(d) for d in RELOAD_DIRS],
                )
            else:
                uvicorn.run(app(queries), host=args.host, port=args.port)
            return 0
        case "query":
            status, lines = answer(queries, args.name, args.params)
            if status == 200:
                _ = sys.stdout.write(jsonl(lines))
                return 0
            else:
                _ = sys.stderr.write(jsonl(lines))
                return 2
        case _:
            raise AssertionError(args.command)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vis-server", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="serve the API (and client/dist, if built) over HTTP")
    _ = serve.add_argument("--host", default="127.0.0.1")
    _ = serve.add_argument("--port", type=int, default=8787)
    _ = serve.add_argument("--reload", action="store_true", help="restart on a change to the server or deadlock sources")
    query = commands.add_parser("query", help="print one query's JSONL lines (see GET /api for the queries)")
    _ = query.add_argument("name")
    _ = query.add_argument("params", nargs="*", type=_pair, metavar="k=v")
    return parser


def _pair(arg: str) -> tuple[str, str]:
    name, equals, value = arg.partition("=")
    if not equals:
        raise argparse.ArgumentTypeError(f"expected k=v, got {arg!r}")
    return name, value


if __name__ == "__main__":
    sys.exit(main())
