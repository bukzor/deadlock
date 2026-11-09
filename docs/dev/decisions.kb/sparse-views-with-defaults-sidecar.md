---
status: accepted
date: "2026-11-05"
---

# Commit views sparse, with a lossless defaults sidecar

A committed view `X.tsv` keeps only the columns that vary. Each column holding
one value in every row moves to an optional sidecar, `X.defaults.tsv`, as a
`column<TAB>value` row. With no such column there is no sidecar. The full,
dense view is still built, locally and gitignored, in
`data/gamedata.dense.tsv/`. The committed pair is split from it by
`deadlock.sparse`, and `python -m deadlock.sparse dense X.tsv X.defaults.tsv`
rejoins it.

## Why

Wide views were mostly noise: in `heroes.tsv`, 17 of 43 columns held a single
value across all 68 heroes (3 of them always empty). Each cost a cell on every
line and buried the columns that discriminate. Dropping them would lose data:
the view could no longer say what a stat *is*, only which heroes differ. The
sidecar keeps every value once, so the pair stays a complete record. A stat
that starts to vary moves back into `X.tsv` as one column, and leaves the
sidecar as one line.

The split is a generic post-pass, not per-view code, so every view gets it for
free. The view modules stay simple dense-table emitters.

## Lossless, except for column position

`join` restores every column and value, but appends the default columns after
the sparse ones. Recording positions would make one added column renumber every
column after it, churning the diff this layout exists to keep small. Column
order is presentation, so it is not worth that cost.

The leading column is the row key and never moves, so rows in `X.tsv` stay
identifiable even in a one-row table.

## What would change this

The threshold is 100% today: a column moves only if every row agrees. Lowering
it (to 90%, say) to also move *mostly*-constant columns needs a way to mark
"this cell takes the default" in `X.tsv`. An empty cell can't do that job,
because empty is already a real value (a hero-unique stat that `hero_base`
doesn't define). Picking a marker that diffs well is that decision's work.

## Alternatives weighed

- **Dropping constant columns outright:** loses data, the thing ruled out above.
- **Diffing against the `hero_base` row:** fits only `heroes.tsv`. Its constant
  columns would still sit on every row, and any view without a base row would
  get nothing.
- **Long form (`entity, stat, value`) for wide views:** good grain, but it
  stops heroes reading side by side, which is the point of `heroes.tsv`. It
  stays open as a per-view choice, and the sidecar works for either shape.
