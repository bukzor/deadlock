---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-008-dllscan-main-load-concommands-strides.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-011-dll-load-and-concommands-atoms.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-012-dlls-facet-aggregates.md
  - docs/dev/cvar-dump.kb/validation.md
  - docs/dev/decisions.kb/commit-diffable-data-let-git-diff.md
  - .gitignore
  - all.do
  - clean.do
  - README.md
---

# Wire the DLL store into the build, with the strides check

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (steps
"`data/dlls.check/strides.do`" and "Wire up")

## Problem Statement

The store builds by hand today (`redo data/dlls/<facet>.tsv`). Make `redo`
from the repo root build it, commit what should be committed, and check the
pinned layout on every build.

- **`.gitignore`:** commit the source and the views; keep the documents and
  `dlls.list` ignored. That means the `.do` files under `data/dlls/`, the
  `data/dlls.check/` `.do` files, and `data/dlls/{file,load,concommands}.tsv`.
  Follow the existing `gamedata*` exception pattern. Then
  `git status --ignored` should show exactly that split.
- **`all.do`:** the three TSVs join the `committed` list the way the
  gamedata views do (`redo-adopt`), plus the strides check as a dependency.
  Keep `all.do`'s style.
- **`data/dlls.check/strides.do`:** `bin/winpy dllscan strides` on
  `server.dll`, failing if the strides moved (008's `strides` already
  raises). `validation.md` also lists anchor and coverage checks that no
  target owns:
  - The anchors already label `strides`' output.
  - Coverage: `engine2`, `client` and `server` each yield a command queue,
    which `concommands.tsv` can show; convars come after the value decode.

  Own what is cheap now, and say in Open Questions what waits for
  `convars`. 008 notes that the anchors' flags are unchecked; check them
  here if it's cheap.
- **`clean.do`:** extend it if it should remove the store's outputs. Follow
  what it does for gamedata.
- **`README.md`:** add the three TSVs and the check to its views table, in
  its existing style.

**Acceptance (6860):**
- from clean (remove `data/dlls/*/*.json`, `data/dlls/*.tsv` and
  `data/dlls.list`), `redo` at the repo root exits 0;
- a second `redo` runs nothing in `data/dlls*`;
- `git status` then shows the three TSVs and the new `.do` files as the only
  new files. `concommands.tsv` has 1418 rows;
- report the wall time of the clean build.

**Scope:** `.gitignore`, `all.do`, `clean.do`, `README.md`,
`data/dlls.check/*.do`, and a small `deadlock` module (+ test) if a check
needs logic beyond shell. Don't commit; the coordinator does.

## Steps

- [x] `deadlock.dlls_check` + test: 18 red against a stub, then green;
      14 hand mutants (`trash/dlls-check-mutants/run.py`) killed
- [x] `data/dlls.check/{strides,concommands}.do`; `.gitignore`, `all.do`, `clean.do`, `README.md`
- [x] Clean build at the root (after 014 landed), logs `trash/016-{clean,second}-build.log`

## Decisions

- **Two check targets, named by what they read:** `strides` (server.dll) and
  `concommands` (the TSV, ms); `convars` gets its own. Logic: `deadlock.dlls_check`.
- **Anchor check added to `strides`:** `dllscan strides` passes with null
  labels; the check requires each `STRIDES` kind labelled exactly once, since
  the anchors decide which stride is which.
- **Anchor flags as `validation.md` states them, as a subset:**
  `citadel_bot_kick` ⊇ `developmentonly`; `bot_kick_all`, `find` none.
  Every copy of an anchor must have them (duplicates are kept).
- **Coverage's load half needs no check:** `concommands.tsv`'s `.do` enforces it.
- **`.gitignore` keeps `data/dlls/*.tsv`** (gamedata's pattern), not the
  three by name: a future facet's TSV is committed by default.
- **README:** own table (gamedata's sparse text doesn't apply); Setup: needs `python.exe`.
- **`clean.do` fix (pre-existing):** `find data/gamedata.tsv -name '*.tsv'`
  matched the directory itself, so `rm -vf` failed; now `-type f -maxdepth 1`.

## Open Questions

- [ ] Waits for `convars`: the convar anchor
      (`citadel_lane_swap_available_duration_prematch` ⊇ `replicated cheat`) and
      convar coverage (engine2/client/server each yield a convar queue).
      `strides` shows server's convar queue exists, not client's/engine2's.
- [ ] `data/dlls/{concommands.md,load.tree.txt}.do` appeared mid-task (a
      sibling's): `.gitignore` commits their `.do`, ignores their outputs
      ("local only", as they say); `all.do` doesn't build them.

## Final report

Files: `.gitignore`, `all.do`, `clean.do`, `README.md` (edited);
`data/dlls.check/{strides,concommands}.do`, `src/deadlock/dlls_check{,_test}.py` (new).

API, `deadlock.dlls_check`: `COMMAND_ANCHORS: Mapping[tuple[str, str], frozenset[str]]`;
`QUEUE_DLLS = ("client.dll", "engine2.dll", "server.dll")`;
`check_strides(learned: object) -> None`; `check_concommands(table: Table) -> Table`
(the anchor rows, `module name flags`). CLI `python -m deadlock.dlls_check
strides PATH` (silent) / `concommands PATH` (prints the anchor rows).
Targets: `data/dlls.check/strides` (the labelled strides JSON),
`data/dlls.check/concommands` (the anchor rows); both gitignored, both in `all.do`.

Acceptance (6860):
- From clean (`data/dlls/*/*.json`, `data/dlls/*.tsv`, `data/dlls.list`,
  `data/dlls.check/strides`), `redo` at the root: exit 0, **222.7 s wall** (serial).
- Second `redo`: 1.1 s; runs `all`, `data/date.txt`, nothing in `data/dlls*`.
- `git status`: new files `data/dlls/{file,load,concommands}.tsv`, the `.do`s
  (mine, 010-012's, and the sibling's two above), plus `src/` modules.
  `git status --ignored`: 285 documents, `dlls.list`, both check outputs ignored.
- `concommands.tsv` 1418 rows; `load.tsv` 91 ok / 2 failed / 4 excluded. `strides`: 160 convars 2008, 64 concommands 493. Anchors: `bot_kick_all`
  `cheat client_can_execute`, `citadel_bot_kick` `developmentonly defensive`,
  `tier0 find` `release`.

Checks: `pytest src` passes; `pyright` on `dlls_check*` 0 errors; 14 mutants killed.
Deviations: README's check is a paragraph, not a table row; the `clean.do` fix.
