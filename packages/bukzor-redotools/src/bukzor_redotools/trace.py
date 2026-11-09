"""redo-trace: turn redo's build logs into a chrome://tracing timeline.

redo keeps the log of each target's most recent build in `.redo/log.N`, N being
the target's rowid in the state database's Files table. Mixed into the target's
stderr are machine-readable lines for each child it built:

    @@REDO:do:PID:UNIXTIME@@ CHILD
    @@REDO:done:PID:UNIXTIME@@ RV CHILD

with CHILD relative to the target's own directory. Chaining those down from a
root target gives one build's tree of spans. A child's log is followed only if
every line in it falls inside the child's span; otherwise it's from a later
build of that child, and the subtree is left out rather than misplaced.

The root's own start and end go to the terminal, not to any log, so its span is
taken from the first to the last line of its log.

Usage: redo-trace [TARGET] > trace.json   # then load it in chrome://tracing
TARGET defaults to the most recent build, finished or not.
"""

import json
import math
import os
import sqlite3
import sys
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

type Event = dict[str, object]


@dataclass(frozen=True)
class Meta:
    kind: str
    when: float
    text: str


@dataclass(frozen=True)
class Span:
    target: str
    start: float
    end: float
    rv: int | None  # None: the root (redo doesn't log its exit), or unfinished
    children: tuple["Span", ...] = ()


def parse_meta(log: str) -> list[Meta]:
    metas: list[Meta] = []
    for line in log.splitlines():
        head, sep, text = line.partition("@@ ")
        if sep and head.startswith("@@REDO:"):
            kind, _pid, when = head.removeprefix("@@REDO:").split(":")
            metas.append(Meta(kind, float(when), text))
    return metas


def child_spans(target: str, metas: Sequence[Meta]) -> list[Span]:
    """The children `target` built, as yet-childless spans in start order."""
    here = os.path.dirname(target)
    started: dict[str, float] = {}
    spans: list[Span] = []
    for meta in metas:
        if meta.kind == "do":
            started[os.path.normpath(os.path.join(here, meta.text))] = meta.when
        elif meta.kind == "done":
            rv, rel = meta.text.split(" ", 1)
            name = os.path.normpath(os.path.join(here, rel))
            spans.append(Span(name, started.pop(name), meta.when, int(rv)))
    # no `done` yet: still building, or the build was interrupted
    spans.extend(Span(name, start, math.inf, None) for name, start in started.items())
    return sorted(spans, key=lambda s: s.start)


def _within(span: Span, metas: Sequence[Meta]) -> bool:
    return all(span.start <= m.when <= span.end for m in metas)


def build_tree(root: str, logs: Mapping[str, str]) -> Span:
    metas = parse_meta(logs[root])
    assert metas, root
    kids = tuple(_expand(span, logs) for span in child_spans(root, metas))
    return Span(root, metas[0].when, max([metas[-1].when, *(k.end for k in kids)]), None, kids)


def _expand(span: Span, logs: Mapping[str, str]) -> Span:
    metas = parse_meta(logs.get(span.target, ""))
    if not _within(span, metas):
        metas = []  # its log is from a later build
    kids = tuple(_expand(kid, logs) for kid in child_spans(span.target, metas))
    if span.end == math.inf:  # unfinished: end it at the last thing known of it
        span = replace(span, end=max([span.start, *(m.when for m in metas), *(k.end for k in kids)]))
    return replace(span, children=kids)


def latest_root(logs: Mapping[str, str]) -> str:
    """The most recently active build: of the logs no parent's span accounts
    for, the one whose last line is latest."""
    metas = {name: m for name, log in logs.items() if (m := parse_meta(log))}
    claimed = {
        kid.target
        for name, m in metas.items()
        for kid in child_spans(name, m)
        if kid.target in metas and _within(kid, metas[kid.target])
    }
    return max(metas.keys() - claimed, key=lambda name: metas[name][-1].when)


def _walk(span: Span, depth: int = 0) -> Iterator[tuple[int, Span]]:
    yield depth, span
    for kid in span.children:
        yield from _walk(kid, depth + 1)


def _place(span: Span, lanes: list[list[float]]) -> int:
    """First lane where `span` nests inside whatever is still open there.

    Spans must arrive in start order, so anything ended by now is done for good.
    """
    for i, open_ends in enumerate(lanes):
        while open_ends and open_ends[-1] <= span.start:
            _ = open_ends.pop()
        if not open_ends or span.end <= open_ends[-1]:
            open_ends.append(span.end)
            return i
    lanes.append([span.end])
    return len(lanes) - 1


def _event(span: Span, lane: int, t0: float) -> Event:
    event: Event = {
        "name": span.target,
        "ph": "X",
        "ts": round((span.start - t0) * 1e6),
        "dur": round((span.end - span.start) * 1e6),
        "pid": 1,
        "tid": lane,
        "args": {"rv": span.rv},
    }
    if span.rv:
        event["cname"] = "terrible"  # one of the trace viewer's named colors
    return event


def to_trace(root: Span) -> list[Event]:
    """Trace events, lanes packed so each lane's spans nest properly."""
    lanes: list[list[float]] = []
    ordered = sorted(_walk(root), key=lambda ds: (ds[1].start, -ds[1].end, ds[0]))
    events = [_event(span, _place(span, lanes), root.start) for _, span in ordered]
    title: Event = {"name": "process_name", "ph": "M", "pid": 1, "args": {"name": f"redo {root.target}"}}
    return [title, *events]


def find_base(cwd: Path) -> Path:
    """The nearest directory holding redo's `.redo` state, as redo finds it."""
    for base in (cwd, *cwd.parents):
        if (base / ".redo").is_dir():
            return base
    sys.exit(f"redo-trace: no .redo directory at or above {cwd}")


def load_logs(base: Path) -> dict[str, str]:
    """Each target's latest build log, by its name relative to `base`."""
    redo = base / ".redo"
    db = sqlite3.connect(f"{(redo / 'db.sqlite3').absolute().as_uri()}?mode=ro", uri=True)
    rows: list[tuple[int, str]] = db.execute("select rowid, name from Files").fetchall()
    db.close()
    logs: dict[str, str] = {}
    for fid, name in rows:
        log = redo / f"log.{fid}"
        if log.exists():
            logs[name] = log.read_text(errors="replace")
    return logs


def main(argv: list[str] | None = None) -> None:
    args = (sys.argv if argv is None else argv)[1:]
    if len(args) > 1:
        sys.exit("usage: redo-trace [TARGET] > trace.json")
    base = find_base(Path.cwd().absolute())
    logs = load_logs(base)
    root = os.path.relpath(Path(args[0]).absolute(), base) if args else latest_root(logs)
    if root not in logs:
        sys.exit(f"redo-trace: no build log for {root}")
    json.dump({"traceEvents": to_trace(build_tree(root, logs))}, sys.stdout)


if __name__ == "__main__":
    main(sys.argv)
