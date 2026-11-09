"""Split a dense TSV view into a sparse view plus its defaults sidecar, losslessly.

A column that holds one value in every row says nothing about any row, but in a
wide view it still costs a cell on every line. So a committed view ``X.tsv``
keeps only the columns that vary, and the optional sidecar ``X.defaults.tsv``
records each single-valued column once, as ``column<TAB>value`` rows. No
sidecar means no column was moved.

Lossless: ``join`` restores every column and value. The one thing it does not
restore is column position (default columns come back last), since recording
positions would make every added column renumber the rest, churning the diff.

The leading column is the row key and always stays, so ``X.tsv`` rows remain
identifiable even when the key happens to be single-valued (a one-row table).

    python -m deadlock.sparse sparse   < dense.tsv   # the sparse view
    python -m deadlock.sparse defaults < dense.tsv   # its sidecar (empty: none)
    python -m deadlock.sparse dense X.tsv [X.defaults.tsv]   # rejoin
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path

type Table = tuple[list[str], list[list[str]]]

DEFAULTS_HEADER = ["column", "value"]


def split(dense: Table) -> tuple[Table, dict[str, str]]:
    """The dense table without its single-valued non-key columns, and those columns' values."""
    header, rows = dense
    assert len(set(header)) == len(header), header
    assert all(len(row) == len(header) for row in rows), header
    moved = {
        name: rows[0][i]
        for i, name in enumerate(header)
        if i > 0 and rows and all(row[i] == rows[0][i] for row in rows)
    }
    kept = [i for i, name in enumerate(header) if name not in moved]
    return ([header[i] for i in kept], [[row[i] for i in kept] for row in rows]), moved


def join(sparse: Table, defaults: Mapping[str, str]) -> Table:
    """Inverse of ``split``: restore each default column, appended after the sparse ones."""
    header, rows = sparse
    assert not set(header) & set(defaults), (header, defaults)
    values = list(defaults.values())
    return [*header, *defaults], [[*row, *values] for row in rows]


def parse(text: str) -> Table:
    header, *rows = (line.split("\t") for line in text.splitlines())
    return header, rows


def render(table: Table) -> str:
    header, rows = table
    return "".join("\t".join(row) + "\n" for row in [header, *rows])


def defaults_table(defaults: Mapping[str, str]) -> Table:
    return DEFAULTS_HEADER, [[name, value] for name, value in defaults.items()]


def defaults_of(table: Table) -> dict[str, str]:
    header, rows = table
    assert header == DEFAULTS_HEADER, header
    return {name: value for name, value in rows}


def main() -> None:
    match sys.argv[1:]:
        case ["sparse"]:
            _ = sys.stdout.write(render(split(parse(sys.stdin.read()))[0]))
        case ["defaults"]:
            defaults = split(parse(sys.stdin.read()))[1]
            if defaults:
                _ = sys.stdout.write(render(defaults_table(defaults)))
        case ["dense", sparse, *sidecar] if len(sidecar) <= 1:
            defaults = defaults_of(parse(Path(sidecar[0]).read_text())) if sidecar else {}
            _ = sys.stdout.write(render(join(parse(Path(sparse).read_text()), defaults)))
        case argv:
            sys.exit(f"usage: python -m deadlock.sparse sparse|defaults < dense.tsv | dense X.tsv [X.defaults.tsv]\n got: {argv}")


if __name__ == "__main__":
    main()
