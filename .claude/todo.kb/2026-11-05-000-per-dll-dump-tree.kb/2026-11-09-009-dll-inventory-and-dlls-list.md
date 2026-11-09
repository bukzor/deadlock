---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - docs/dev/convar-dump.kb/output-views.md
  - docs/dev/CLAUDE.md
  - data/gamedata.list.do
  - src/deadlock/paths.py
---

# `deadlock.dll_inventory`, `paths.bin_dirs`, `data/dlls.list.do`

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (Wave 6, the WSL
side; rows `paths` and `dll_inventory`, and the tree's `data/dlls.list`)

## Problem Statement

The store's root: membership only. Sibling units (010–012) are building
against this contract right now, so keep it exactly:

- `data/dlls.list`: one line per `*.dll` under `game/`, each a path relative to
  `game/` (e.g. `citadel/bin/win64/server.dll`), byte-sorted, `\n`-terminated.
  Basenames are unique: assert it, and fail loudly naming the duplicates.
  On 6860 there are 97 DLLs, including `bin/win64/qt5_plugins/` and
  `subtools/`.
- No size, hash or other patch-varying data goes in it. Every atom depends on
  it, so its content changes only when a DLL is added, removed or renamed.
  Use `redo-stamp` (as `gamedata.list.do` does) so a rebuild with unchanged
  content doesn't re-run the atoms.
- `deadlock.paths.bin_dirs`: `game/bin/win64` and `game/citadel/bin/win64`
  as WSL paths. The atoms convert them with `wslpath -w` for `bin/winpy`
  (invocation in 008's Final report). Follow `paths.py`'s existing resolver
  and CLI style, and add a CLI entry for `bin_dirs` if `paths` has one per
  resolver.
- `python -m deadlock.dll_inventory` prints `dlls.list`.
- What `dlls.list.do` depends on is yours to choose (mirror
  `gamedata.list.do`). It must notice a patch that adds a DLL, e.g. by
  depending on `data/deadlock-version.json`. Justify the choice.

**Tests** beside each module (Describe/it), over a fake `game/` tree in
`tmp_path`: sorting, a duplicate basename, nested dirs, non-DLL files
ignored, case (`.DLL`?). Check what the real install has before deciding
how case is handled. Then run `redo data/dlls.list` for real and report its
line count and first and last lines.

**Scope:** `src/deadlock/paths.py` (+ test), `src/deadlock/dll_inventory.py`
(+ test), `data/dlls.list.do`. Not `.gitignore` or `all.do`: wiring is a
later unit.

## Steps

- [x] Survey 6860: 97 DLLs, all suffixed `.dll`; mixed-case basenames (`Qt5Core`,
      `SDL3`, …); none duplicate; one symlinked dir (`citadel/replays`)
- [x] `paths.bin_dirs` + CLI entry (red: missing name, then wrong value)
- [x] `dll_inventory` (red at a stub; each guard then mutated and killed)
- [x] `data/dlls.list.do`; real `redo data/dlls.list`; `pytest`, `pyright`

## Decisions

- **Case:** the suffix matches in any case (`.DLL` is a DLL to Windows; none on
  6860), names kept as found. Basename uniqueness ignores case, as the Windows
  loader does; `dllscan`'s `module` is the lowercased basename, so this keeps
  `module` unique too.
- **Symlinks:** `os.walk` default, not followed: no double listing, no loops.
- **Duplicates** fail with `assert not dups, dups`: `{lowercased basename:
  [paths]}`, so the message names every colliding path.
- **`bin_dirs` CLI:** prints one path per line (engine's, then game's);
  `RESOLVERS` values may now return `tuple[Path, ...]`. Bash: `mapfile -t bins
  < <("$py" -m deadlock.paths bin_dirs)`.
- **`dlls.list.do` deps:** `dll_inventory.py`, `paths.py`,
  `data/deadlock-version.json`, + `redo-stamp`. Only a patch adds/removes/renames
  a DLL, and a patch bumps the stamp. Rejected: `redo-always` (the walk is
  ~4 s over `/mnt/c`, paid on every build); depending on the DLL files (re-runs
  on content changes yet still misses an added DLL).

## Open Questions

- None. (A DLL added without a version bump waits for the next bump.)

## Final report

Files: `src/deadlock/paths.py` (+`paths_test.py`), new
`src/deadlock/dll_inventory.py` (51 lines) + `dll_inventory_test.py`, new
`data/dlls.list.do`.

API:
- `deadlock.paths.bin_dirs(environ: dict[str, str] | None = None) ->
  tuple[Path, Path]`: `(game/bin/win64, game/citadel/bin/win64)`;
  `python -m deadlock.paths bin_dirs` prints them one per line.
- `deadlock.dll_inventory.dlls(game: Path) -> list[str]`: relative POSIX paths,
  byte-sorted; `AssertionError` naming duplicates.
- `deadlock.dll_inventory.basename_duplicates(relpaths: Iterable[str]) ->
  Mapping[str, list[str]]`.
- `python -m deadlock.dll_inventory` prints `dlls.list` (no args).
- No basename → path lookup here: 010 owns it (it may add it to this module).

Real run (6860): `redo data/dlls.list` 5.0 s, 97 lines, first
`bin/win64/Qt5Concurrent.dll`, last `citadel/bin/win64/server.dll`;
byte-identical to `find … -iname '*.dll' | LC_ALL=C sort`. A following
`redo-ifchange data/dlls.list` runs nothing. Side effect: the dep rebuilt
`data/deadlock-version.json` 6857 → 6860 (committed file, already modified in
the tree; the `gamedata.tsv` views are still 6857-built until `redo` all).

Note for 012: basenames are mixed case (`Qt5Core.dll`) but `dllscan`'s
`module` is lowercased (`qt5core.dll`); a join on the two must lowercase.

Checks: `pytest` on the four files 22 passed; `pyright` 0 errors. Every new
assertion observed failing (stubs, then 11 mutants, all killed). Deviations: none.
