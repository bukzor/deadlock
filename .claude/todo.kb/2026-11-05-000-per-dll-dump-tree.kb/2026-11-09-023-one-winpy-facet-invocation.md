---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-011-dll-load-and-concommands-atoms.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-020-convars-atom-aggregate-check.md
  - ~/.claude/must-read.kb/before/writing-bash-scripts.md
  - bin/winpy
---

# One invocation of `bin/winpy dllscan <facet>` for every Windows atom

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the step "One
helper for the `bin/winpy dllscan <facet>` invocation")

## Problem Statement

The same block is copied into three `.do` files:
`data/dlls/{load,concommands,convars}/default.json.do`. It builds the
`bin/winpy dllscan <facet>` argv: the `wslpath -w` DLL path and the two bin
dirs from `deadlock.paths bin_dirs`. Then it declares the dependencies
(`bin/winpy`, `src/dllscan/*.py` minus tests). The same goes for the
lookup-and-guard lines. A fourth facet would make a fourth copy.

Write it once, and make each `.do` the facet-specific part only. The shape
is yours: a sourced bash file, a small `bin/` script, or a shared default
`.do`. Weigh it against the house limits (bash ≤50 lines, only for
fs/process work or `python -m` shims) and redo's dependency rules. Every
atom must still declare exactly the dependencies it uses: an excluded DLL's
`load` atom must not depend on the scanner (011's Decisions).

**Acceptance (6860):**
- `redo` at the repo root rebuilds the atoms, since their `.do` files
  changed, and exits 0;
- every document is byte-identical to a snapshot taken before the change,
  and `git diff data/` is empty;
- a second `redo` runs nothing;
- `redo-sources` for one atom of each facet lists the same dependencies as
  before. Show the before/after.

**Scope:** `data/dlls/{load,concommands,convars}/default.json.do`, the shared
helper, and `bin/` if that's where it goes. A sibling (022) renames
`docs/dev/convar-dump.kb/` concurrently. If a comment in your files cites
that path, write the new path, `cvar-dump.kb`.

## Steps

- [x] Baseline: `redo -j8` brought up to date (66 s, byte-identical to the prior tree); snapshot
      `trash/023/data.base.sha256`, deps `trash/023/deps.base` (query: `trash/023/deps.sh`)
- [x] `bin/winpy-facet.bash` + the three `.do`s; `shellcheck` (via `uvx --from shellcheck-py`) clean
- [x] Acceptance run, logs `trash/023/redo1.log`; guard smoke (excluded, failed, unlisted)

## Decisions

- **A sourced bash file** (`lookup`, `require_loaded`, `dllscan`), not a `bin/` script: the
  lookup sets `dll` and must run *before* load's exclusion step, so the shared part brackets
  facet-specific code. A script can wrap only one end. Each step declares its own deps, so an
  excluded `load` atom still never depends on the scanner. It does depend on the helper, as it
  depended on its `.do` (which held the scan block) before.
- **In `bin/`, not `data/dlls/`:** `/data/dlls/*` is gitignored except `*.do`/`*.tsv`, and
  `redo clean` (`git clean -fdX data/dlls`) would delete it. Not executable; it carries
  `# shellcheck shell=bash`.
- **Paths are root-based** (`BASH_SOURCE`): the helper doesn't assume the caller's cwd.
- **`redo-sources` takes no arguments** in this redo, so I read per-target deps from
  `.redo/db.sqlite3`.

## Open Questions

- [ ] `data/dlls/file/default.json.do` (out of scope) repeats the `lookup` lines with its own
      module list (`dll_file` instead of `dll_load`). Folding it in would need `lookup` to take
      the guard's modules.

## Final report

Files: new `bin/winpy-facet.bash` (42 lines, sourced); rewritten
`data/dlls/{load,concommands,convars}/default.json.do` (19/16/16 lines; −72 +26).

API (`bin/winpy-facet.bash`, sourced after `redo-ifchange` on it; sets `root`, `py`):
- `lookup NAME`: the dlls.list guard. Sets `dll` to the path; declares `dlls.list`,
  `deadlock/{dlls_list,paths,dll_load,types}.py`, `dllscan/document.py`.
- `require_loaded NAME`: `data/dlls/load/NAME.json` must say `ok` (deps: that document).
- `dllscan FACET DLL`: prints `bin/winpy dllscan FACET` on the Windows paths of DLL and the bin
  dirs (deps: DLL, `bin/winpy`, `src/dllscan/*.py` minus tests).
A new load-time facet's `.do` is `lookup "$2"; require_loaded "$2"; dllscan FACET "$dll" >"$3"`.

Acceptance (6860):
- `redo -j8` at the root: exit 0, 84 s; rebuilt 97 load, 91 concommands, 91 convars atoms.
- Every file under `data/` except `*.do` is byte-identical to the baseline (sha256, 606 files),
  and `git status data/` shows only `.do` sources.
- A second `redo` runs only `all`, `(data/gamedata.list)`, `data/date.txt` (always-run).
- Deps (`load/helpsystem` excluded, `load/client`, `concommands/client`, `convars/client`):
  before == after except for one added line each, `m bin/winpy-facet.bash`. The excluded
  atom still has no `bin/winpy` and no `src/dllscan/` beyond `document.py`.
- Guards: `concommands/helpsystem` → `('load outcome', 'excluded')`, `convars/phonon4` →
  `('load outcome', 'failed')`, `load/nope.dll` → `not exactly once in dlls.list`. Each exits
  1 with no target.

Checks: no Python touched, so no pytest/pyright needed. Deviation: the dep lists gain the helper
itself, which correctness requires.
