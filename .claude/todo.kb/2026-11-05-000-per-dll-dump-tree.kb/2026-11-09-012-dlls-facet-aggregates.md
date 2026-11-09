---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-000-dllscan-document-types.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-006-dllscan-entries-names-help-flags.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - docs/dev/cvar-dump.kb/output-views.md
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

- [x] Modules + tests, red first; 48 mutants killed (`trash/dlls-aggregates-mutants/`)
- [x] `data/dlls/default.tsv.do`; real run (Final report)

## Decisions

Lossless is tested by reading back: each view's test parses its own table,
rebuilds the documents, and compares. Departures from gamedata (which has no
escaping, renders absent as an empty cell, and joins lists by `,` or space):

- **Cells in PostgreSQL `COPY` text format:** `\` `\t` `\n` `\r` are
  escaped. 6860 helps hold raw ones (168 commands `\n`, 129 `\t`), and
  `cstr_in` admits no other controls.
  `null` is `\N` and `""` is an empty cell: unlike in gamedata, empty is a
  real value here, and `\N` is the standard marker (a literal `\N` help
  renders `\\N`). A null↔`""` flip shows as one changed cell.
- **Lists are space-joined** (as `cooldown` is), with items asserted to need
  no escaping. Under `--word-diff`, an added flag or module is one word.
- **`load.tsv`: `dll outcome detail`** (the modules, the error or the
  reason). Long form would need a filler row for a DLL that added none.
- **Keys:** `file`/`load`: the `dlls.list` basename; `concommands.module`:
  the document's own, asserted equal to it once both are lowercased.
- **`.do`:** 010's shape. The `concommands` DLLs come from `dlls_load --ok`,
  run after one `redo-ifchange` over every `load` document, and captured with
  `$(...)`, so a failure stops the build.

## Open Questions

- [ ] `document.py` says `module` is the `dlls.list` basename, but `facets`
      lowercases it. Settle that upstream; then the assert becomes `==`.
- [ ] `/data/*` in `.gitignore` also hides every `data/dlls/**/*.do`. The
      wiring unit must re-include them, along with the committed TSVs.

## Final report

Files (new): `src/deadlock/dlls_{tsv,file,load,concommands}{,_test}.py`,
`data/dlls/default.tsv.do`.

API:
- `dlls_tsv`: `NULL = "\\N"`; `cell(str | None) -> str`; `uncell(str) -> str | None`;
  `list_cell(Sequence[str]) -> str`; `unlist_cell(str) -> list[str]`;
  `load_documents(paths, is_document) -> Mapping[basename, D]`; `is_str_sequence`.
- `dlls_<facet>`: `is_<facet>_document(object) -> TypeGuard[…]`,
  `table(Mapping[basename, Doc]) -> sparse.Table`, `main()`; CLI
  `python -m deadlock.dlls_<facet> DOC.json… > <facet>.tsv`. Columns:
  `dll size sha256`; `dll outcome detail`; `module name flags help`.
- `dlls_load.ok(docs) -> list[str]`; `python -m deadlock.dlls_load --ok DOC…`.

Real run, 6860: `file.tsv` and `load.tsv` have 97 rows each; `concommands.tsv`
has 1411 (= 011's total). Its read-back equals all 29 non-empty documents,
helps 24 null / 53 `""` / 1334 text (= 006's census). A forced rebuild is
byte-identical and a second `redo-ifchange` is a no-op; `convars.tsv` fails
loudly. First rows:

    Qt5Concurrent.dll	131432	d4a01961…6db29f
    phonon4.dll	failed	LoadLibraryExW: 126
    client.dll	camerazoomin	developmentonly defensive	\N

Checks: pytest 78 passed (`src` 461); pyright 0 errors. Deviations: none.
