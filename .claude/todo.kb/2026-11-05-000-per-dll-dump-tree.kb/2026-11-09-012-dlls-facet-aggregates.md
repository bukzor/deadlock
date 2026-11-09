---
managed-by: Skill(llm-subtask)
status: open
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-000-dllscan-document-types.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-006-dllscan-entries-names-help-flags.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - docs/dev/convar-dump.kb/output-views.md
  - docs/dev/decisions.kb/commit-diffable-data-let-git-diff.md
  - docs/dev/decisions.kb/sparse-views-with-defaults-sidecar.md
  - data/gamedata.dense.tsv/default.tsv.do
  - data/gamedata.tsv/default.tsv.do
---

# `deadlock.dlls_{file,load,concommands}` and `data/dlls/default.tsv.do`

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (Wave 6; row
`dlls_<facet>`, tree rows `data/dlls/default.tsv.do`, `data/dlls/<facet>.tsv`)

## Problem Statement

One aggregator per facet: that facet's JSON documents → `data/dlls/<facet>.tsv`,
the facet's lossless aggregate, one row per item. This is the view layer: it
adapts the documents' typed values to TSV (`output-views.md`, JSON content
rules). Units 010 and 011 produce the documents concurrently; build
against the `dllscan.document` types with fixtures, and run for real once
they land.

- **`deadlock.dlls_file`:** one row per DLL: basename, size, sha256.
- **`deadlock.dlls_load`:** one row per DLL: basename, outcome, then the
  detail (the added modules, the error, or the reason). Design the
  columns/rows so a module added to one DLL's load is a small diff.
- **`deadlock.dlls_concommands`:** columns `module, name, flags, help`.
  Rows are sorted by module, then in queue order, because a row's ordinal
  within its module *is* its queue index (`output-views.md`). Add a test
  asserting ordinal == list position. Keep duplicates.
- **Cells:** every cell reads back to the document value it came from (the
  aggregate is lossless). Start from the repo's TSV conventions (how
  `gamedata.*.tsv` renders cells and absent values) and justify any departure
  in Decisions. Flags: a list of names in one cell; pick the separator.
- **`data/dlls/default.tsv.do`:** a case table on `$2` = facet, as
  `gamedata.dense.tsv/default.tsv.do` has.
  - One `redo-ifchange` over the facet's documents. Make it a single call,
    so redo parallelises.
  - For load-time facets (`concommands`), first `redo-ifchange` every `load`
    document, then take only the `ok` DLLs.
  - DLL basenames come from `data/dlls.list` (contract: 009's Problem
    Statement).

**Real run** once 010 and 011 land: build all three TSVs, check the
concommands row count against 011's total, rebuild and confirm the output is
byte-identical, and paste the first few rows of each.

**Scope:** `src/deadlock/dlls_{file,load,concommands}.py` (+ tests), a shared
TSV/document-loading helper if one pays for itself, and `data/dlls/default.tsv.do`.

## Steps

- [x] Read conventions: `gamedata.*.tsv` never escapes (no cell holds a tab
      or newline), renders absent as an empty cell, and joins lists with `,`
      (`components`) or a space (`cooldown`)
- [x] Census of the 6860 help strings (`trash/help-census/out/`): 168 command
      helps contain `\n`, 129 contain `\t`, 11 convar helps contain `\n`, and 1
      contains `\`. Escaping is required
- [x] `deadlock.dlls_tsv` + test: 14 red against a stub, then green
- [x] `deadlock.dlls_{file,load,concommands}` + tests: 40 red, then green.
      42 hand mutants (`trash/dlls-aggregates-mutants/run.py`, `-B`): one
      survived (the `failed` key-set check), so I added a test; all killed
- [x] `data/dlls/default.tsv.do`. Real `file.tsv`; `load`/`concommands`
      through a fake tree (`trash/dlls-aggregates-fake/`: 3 DLLs, one
      `failed`, real server document → 493 rows); `convars` fails loudly
- [x] `pytest src/deadlock` and `pyright` on the touched files: clean
- [~] Real `load`/`concommands` run: waiting for 011

## Decisions

- **Cells: PostgreSQL `COPY` text format** (`dlls_tsv.cell`): `\` `\t` `\n`
  `\r` escaped, `null` is `\N`, `""` an empty cell. Escaping is required
  (census above), and `cstr_in` admits only printables plus `\t\r\n`, so
  these four are complete. One known convention covers escaping and null
  together, and a reader can undo it mechanically. A literal `\N` help would
  render `\\N`, so the two never collide.
- **Null help and `""` stay distinct.** The aggregate is meant to be lossless,
  and 006's census shows the distinction carries information. Diff stability
  doesn't argue for merging them: a rendering is stable either way, and a
  null↔`""` flip is one changed cell. Merged, that flip would be invisible,
  and `output-views.md` allows "over-sensitive, never blind". The cost is 2
  bytes on the null rows (24 commands; 3248 convars later).
- **Why `\N` for null, not a marker for `""`.** gamedata renders absent as
  empty, but there empty can't be a real value. Here it can (`""`), so one
  side needs a marker. A marker for null is the standard one; inventing a
  marker for `""` would be ours alone.
- **Lists: space-separated** (`list_cell`), as gamedata's `cooldown` is.
  Every item is asserted non-empty and free of anything that needs escaping.
  With `git diff --word-diff`, an added flag or module is one added word; a
  `,`-joined cell is a single word.
- **`load.tsv`: `dll outcome detail`**, one row per DLL as the brief says.
  `detail` means modules, error or reason, as the outcome says. A module
  added to one DLL's load changes one line by one word. Considered: long form
  (one row per module). One added line is a smaller diff, but it is not
  "one row per DLL", and it would need a blank row per DLL that added no
  modules.
- **Keys:** `file`/`load` key on the `dlls.list` basename (from the document's
  filename, mixed case). `concommands.module` is the document's own value
  (lowercased by `facets`), asserted equal to the basename ignoring case.
  Sorting by `module` and by basename agree except on case.
- **Shared helper `dlls_tsv`:** cells, `load_documents` (filename → basename,
  shape asserted by each facet's `TypeGuard`), `is_str_sequence`. Rendering
  reuses `sparse.render`/`Table`.
- **`.do`:** the shape follows 010 (write `$3`, then `redo-stamp <"$3"`). The
  `concommands` DLLs come from `python -m deadlock.dlls_load --ok`, run after
  one `redo-ifchange` over every `load` document. A failing `--ok` stops the
  build under `set -e`, since its output is captured with `$(...)`, not
  `< <(...)`.

## Open Questions

- [ ] `document.py` says `module` "is the DLL's basename as listed in
      `data/dlls.list`", but `facets` lowercases it (`Qt5Core.dll` →
      `qt5core.dll`; 000's open question). For now `concommands.tsv` shows
      the lowercase form and `file`/`load.tsv` the listed one. One of the
      two should change upstream, and then the case-insensitive assert here
      can become `==`.

## Final report
