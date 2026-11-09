---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - docs/dev/CLAUDE.md
  - docs/dev/cvar-dump.kb/CLAUDE.md
---

# Rename `docs/dev/convar-dump.kb/` to `cvar-dump.kb/`

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (naming)

## Problem Statement

The KB designs the dump of both convars and concommands. The engine's own
word for the class covering both is "cvar": the `ICvar` registry holds both,
`cvarlist` lists both, and the `FCVAR_*` flags apply to both. "convar" is
the variable kind only. Rename the directory to `docs/dev/cvar-dump.kb/`
with `git mv`, so history follows.

- **Update every reference to the old path,** tracked or in this `.kb/`:
  `docs/dev/CLAUDE.md`'s index, the KB's own `CLAUDE.md` and its title,
  the parent plan, these handoff files, docstrings and comments under
  `src/`, `README.md`, and the repo `CLAUDE.md`. Find them with `git grep`
  plus a `grep -r` over `.claude/`.
- **Also align prose that says "convar" where it means both kinds:** the
  KB's `CLAUDE.md` opening, and its title line. Leave "convar" wherever it
  really means the variable kind, and leave Valve's identifiers alone.
- **Check:** `~/.claude/skills/llm-kb/bin/llm.kb-validate-links` over
  `docs/dev/` and `.claude/todo.kb/` reports no new broken links. Fix the ones
  the rename caused; leave ones that were already broken, and list them.

**Scope:** the rename and the reference updates only; no content changes
beyond the wording above. A sibling (023) edits `bin/` and
`data/dlls/*/default.json.do` concurrently. If one of its files names the
KB path, coordinate by leaving it to 023 and listing it in your report.

## Steps

- [x] Baseline `llm.kb-validate-links` (strict and `--lax`) over both trees.
- [x] `git mv docs/dev/convar-dump.kb docs/dev/cvar-dump.kb` (15 renames staged).
- [x] `sed s/convar-dump\.kb/cvar-dump.kb/` over every `git grep` / `grep -r .claude/`
  hit; then restored the two mentions that name the rename's source (this
  brief's title, 023's Scope line).
- [x] KB `CLAUDE.md`: title follows the sed; opening says "every cvar, convar
  and concommand alike"; "registers convars" -> "registers cvars".
- [x] Re-ran the link checks and diffed against baseline; checked every cited
  `docs/dev/cvar-dump.kb/...` path exists.

## Decisions

- `git mv` despite the "never touch the index" rule: the brief names it, and it
  stages only the 15 renames. Content edits are unstaged.
- `data/dlls/file/default.json.do` edited here: 023's own Scope is
  `data/dlls/{load,concommands,convars}/default.json.do` + `bin/`, none of which
  cite the path, so nothing was left to 023.
- `docs/dev/CLAUDE.md`'s index already says "convar/concommand dumper" and
  "registers cvars": accurate for both kinds, left as is.
- `README.md` and the repo `CLAUDE.md` never cited the path: nothing to change.

## Open Questions

- `registration-flow.md`'s title, "How a convar gets registered", covers both
  kinds (its step 1 is `ConVar`/`ConCommand`). Out of this brief's wording scope.

## Final report

**Files touched.** Renamed: `docs/dev/convar-dump.kb/**` -> `docs/dev/cvar-dump.kb/**`.
Path updated in: `docs/dev/CLAUDE.md`, `docs/dev/cvar-dump.kb/{CLAUDE.md,capture-approach.kb/CLAUDE.md}`,
`docs/dev/probes/convar_probe.py`, `src/deadlock/{dlls_check,dlls_concommands}.py`,
`src/dllscan/{convar_h,document,entries,facets,reglist,values}.py`,
`data/dlls.check/{concommands,convars,strides}.do`, `data/dlls/file/default.json.do`,
`.claude/todo.md`, the parent plan, this dir's `CLAUDE.md`, handoffs 000-002,
004-013, 015, 016, 018-021, and this brief's `required-reading`.

**Checks.** `llm.kb-validate-links` strict: unchanged from baseline, the only
broken links predate the rename (`bin/shell` in
`docs/dev/environment.kb/toolchain.md` and in handoff 001). `--lax`: identical
modulo the rename (its many hits are repo-root-relative paths, which it resolves
against the citing file; pre-existing). All nine distinct cited new paths exist.
`pytest` (touched src modules): 3 passed; `pyright` on them: 0 errors.
`llm.kb-validate` is not installed in this venv; not run.

**Deviations.** 023's brief edited (one line: its Scope's old-path mention,
rewritten by the sweep then restored). No net change to its text.
