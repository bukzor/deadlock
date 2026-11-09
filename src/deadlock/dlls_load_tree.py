"""Render ``data/dlls/load.tsv`` as a ``tree(1)``-style forest: who loads whom.

    python -m deadlock.dlls_load_tree < data/dlls/load.tsv > data/dlls/load.tree.txt

An ``ok`` row lists every module its DLL's load added: a closure, not the
direct imports. The edges are inferred from those closures (their transitive
reduction): X sits under Y when X is in Y's closure and in the closure of no
other module there. Only listed DLLs have a known closure, so a system DLL is
a leaf, and whatever it pulls in shows beside it rather than under it.

The roots are the listed DLLs no other listed DLL loads; a DLL whose load is
not ``ok`` is a root annotated with its outcome and detail. A shared subtree
(``tier0.dll``'s) is drawn once, where it first appears; later it is just its
name marked ``(*)``, as ``cargo tree`` does. A shared leaf simply repeats.
Names sort as ``load.tsv`` does; listed DLLs keep their listed case.
"""

import sys
from collections import Counter
from collections.abc import Iterator, Mapping, Set

from . import dlls_tsv
from .sparse import parse


def edges(closures: Mapping[str, Set[str]]) -> dict[str, list[str]]:
    """Each module's direct loads, given every known module's closure (itself excluded)."""
    for module, closure in closures.items():
        for other in closure:
            assert module not in closures.get(other, ()), ("load cycle", module, other)
    return {
        module: sorted(x for x in closure if not any(x in closures.get(y, ()) for y in closure - {x}))
        for module, closure in closures.items()
    }


def _branches(module: str, children: Mapping[str, list[str]], prefix: str, drawn: set[str]) -> Iterator[str]:
    """``module``'s subtree below it; a subtree already in ``drawn`` collapses to ``(*)``."""
    kids = children.get(module, [])
    for i, kid in enumerate(kids):
        last = i == len(kids) - 1
        branch = f"{prefix}{'└── ' if last else '├── '}{kid}"
        if kid in drawn:
            yield f"{branch} (*)"
            continue
        yield branch
        if children.get(kid):
            drawn.add(kid)
        yield from _branches(kid, children, prefix + ("    " if last else "│   "), drawn)


def tree(tsv: str) -> str:
    """The forest drawn from ``load.tsv``'s text, then a count of each outcome."""
    header, rows = parse(tsv)
    assert header == ["dll", "outcome", "detail"], header
    listed = {dll.lower(): dll for dll, _, _ in rows}
    assert len(listed) == len(rows), "basenames collide ignoring case"
    closures = {
        dll: {listed.get(m, m) for m in dlls_tsv.unlist_cell(detail)} - {dll}
        for dll, outcome, detail in rows
        if outcome == "ok"
    }
    children = {module: sorted(kids) for module, kids in edges(closures).items()}
    loaded = {m for closure in closures.values() for m in closure}
    lines: list[str] = []
    drawn: set[str] = set()
    for dll, outcome, detail in sorted(rows):
        if outcome != "ok":
            lines.append(f"{dll}  [{outcome}: {detail}]")
        elif dll not in loaded:
            lines += [dll, *_branches(dll, children, "", drawn)]
    counts = Counter(outcome for _, outcome, _ in rows)
    summary = ", ".join(f"{n} {outcome}" for outcome, n in sorted(counts.items()))
    return "".join(f"{line}\n" for line in lines) + f"\n{len(rows)} dlls: {summary}\n"


def main() -> None:
    _ = sys.stdout.write(tree(sys.stdin.read()))


if __name__ == "__main__":
    main()
