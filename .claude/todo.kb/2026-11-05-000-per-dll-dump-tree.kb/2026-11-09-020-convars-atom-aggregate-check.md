---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-011-dll-load-and-concommands-atoms.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-012-dlls-facet-aggregates.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-016-wire-the-store-into-the-build.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-018-convar-value-layout-fit.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-019-dllscan-convar-decode.md
  - docs/dev/convar-dump.kb/output-views.md
  - docs/dev/convar-dump.kb/validation.md
---

# The `convars` atom, `convars.tsv`, and the convars check

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (steps
"`data/dlls/convars/default.json.do`" and the `convars` aggregate)

## Problem Statement

The WSL side of the `convars` facet, a copy of `concommands`' at each layer.
Sibling 019 builds the scanner side concurrently. The document is
`document.ConVar` as it is today, plus `version: int`, which 019 adds. Build
against that shape with fixtures, and run for real once 019's file says
`status: done`.

- **`data/dlls/convars/default.json.do`:** copy
  `concommands/default.json.do`, running `bin/winpy dllscan convars`.
- **`deadlock.dlls_convars` + its case in `data/dlls/default.tsv.do`.**
  Columns: `module, name, type, version, default, min, max, flags, help`.
  Rows are sorted by module, then in queue order (ordinal == list position,
  tested). Each cell reads back to its document value, by `dlls_tsv`'s
  conventions. Values are typed (`bool`, `int`, `float`, `str`, number
  lists) and the `type` column names the type, so a cell need only be
  unambiguous given that column. The read-back test proves it. Justify the
  encoding in Decisions.
- **`data/dlls.check/convars.do`** + `deadlock.dlls_check`: the convar
  anchor (`validation.md`; 016's Open Question names it), and convar-queue
  coverage (`engine2`, `client`, `server`), the way
  `data/dlls.check/concommands` does it for commands.
- **`all.do`:** `convars.tsv` joins `committed`, and the check joins the
  dependencies. Add a README row.

**Acceptance (6860), after 019 lands:**
- `redo` at the root exits 0;
- `convars.tsv` has 6223 rows, and reading it back gives every document;
- a second `redo` runs nothing in `data/dlls*`, and a forced rebuild is
  byte-identical;
- paste the first rows.

**Scope:** `data/dlls/convars/default.json.do`, `data/dlls/default.tsv.do`,
`data/dlls.check/convars.do`, `src/deadlock/{dlls_convars,dlls_check}{,_test}.py`,
`all.do`, `README.md`. Leave the untracked `data/dlls/{concommands.md,load.tree.txt}.do`
and `src/deadlock/dlls_{concommands_md,load_tree}*` alone: they're someone
else's.

## Steps

- [x] `dlls_convars`, `dlls_check.check_convars` + tests: red against stubs, then green
- [x] 42 hand mutants over both (`trash/020-mutants/run.py`): all killed
- [x] `.do` files, `all.do`, README
- [x] Real run (6860), logs `trash/020-{redo1,redo2,force}.log`, readback `trash/020-mutants/readback.py`

## Decisions

- **Value cells, read by `type` (`TYPES`: name → kind):** `\N` absent; `true`/`false`;
  numbers as `repr` (floats read back identical: `0.02`, `1.0`, `-0.0`); strings as any
  `dlls_tsv` cell; color/vectors space-joined (`255 0 16 255`), so `--word-diff` shows one
  component. Rejected: JSON cells (`[0.5, 0.0]`, `"text"`): quote every string, gain nothing
  once `type` is a column.
- **Kinds asserted** by the encoder and the document guard (`version` an int, not bool), so a
  bad document fails in `load_documents`, naming its path. `TYPES` is the view's own table,
  tested equal (names, order) to `dllscan.values.TYPES`.
- **One check helper,** `_check_queue(table, header, anchors)`, finds `flags` by name; both
  checks report `module name flags`. The `.do`s are copies, per the brief.

## Open Questions

- [ ] The winpy argv block is now in three `.do`s: 011's trigger for a helper has fired.
- [ ] 011's import-closure dependency gap applies to `convars` atoms too.

## Final report

Files: new `src/deadlock/dlls_convars{,_test}.py`, `data/dlls/convars/default.json.do`,
`data/dlls.check/convars.do`, `data/dlls/convars.tsv` (generated, to commit); edited
`src/deadlock/dlls_check{,_test}.py`, `data/dlls/default.tsv.do` (`concommands|convars)`),
`all.do`, `README.md`. `.gitignore`/`clean.do` already cover the new paths.

API:
- `dlls_convars`: `TYPES: Mapping[str, Kind]` (the 18 names in code order, = `values.TYPES`);
  `value_cell(type, ConVarValue | None) -> str`; `uncell_value(type, str) -> ConVarValue | None`;
  `is_convars_document(object) -> TypeGuard[ConVarsDocument]`; `table(Mapping[basename, Doc]) -> Table`;
  CLI `python -m deadlock.dlls_convars DOC.json… > convars.tsv`. Columns
  `module name type version default min max flags help`.
- `dlls_check`: `CONVAR_ANCHORS` (`server.dll` `citadel_lane_swap_available_duration_prematch`
  ⊇ `replicated cheat`); `check_convars(Table) -> Table` (anchor rows, `module name flags`);
  CLI `python -m deadlock.dlls_check convars PATH`. Target `data/dlls.check/convars`.

Acceptance (6860):
- `redo` at the root: exit 0, 230 s (rebuilt every DLL atom: 019 changed `src/dllscan/`).
- `convars.tsv`: 6223 rows; read back equals all 30 non-empty documents of 91 (JSON-text
  compare, so int/float kinds too). Documents byte-equal 019's `trash/convars019/run1/`.
- Second `redo`: 1 s, nothing in `data/dlls*`. Forced rebuild of the 91 atoms, TSV and check:
  22 s (`-j8`), all 385 `data/dlls*` outputs byte-identical (sha256).
- Check: `server.dll citadel_lane_swap_available_duration_prematch replicated cheat`.

First rows:

    module	name	type	version	default	min	max	flags	help
    animationsystem.dll	animgraph_debug_max_poseop_count	bool	0	\N	\N	\N	developmentonly reference defensive	\N
    client.dll	citadel_sat_volume_sat_color	color	0	255 255 255 255	\N	\N	developmentonly replicated	\N
    server.dll	sv_specspeed	float32	2	1200.0	\N	\N	archive notify replicated	

Checks: `pytest src` passes; pyright 0 errors on the 4 files; 42 hand mutants killed.
Deviations: none.
