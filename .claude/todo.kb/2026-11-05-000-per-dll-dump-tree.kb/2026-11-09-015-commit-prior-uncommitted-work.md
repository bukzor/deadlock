---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.md
  - docs/dev/CLAUDE.md
  - docs/dev/decisions.kb/commit-diffable-data-let-git-diff.md
---

# Commit the tree's prior uncommitted work

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (prerequisite for
the wiring step: it edits `.gitignore`, `all.do` and `README.md`, which this
work also changed)

## Problem Statement

Before this session, the tree already held finished but uncommitted work.
All of it is ticked `[x]` in `.claude/todo.md`:
- redo tracks VRF releases (`data/tools/vrf-release.json{,.do}`,
  `data/date.txt.do`, `bin/fetch-vrf`, `Source2Viewer-CLI.d.do`);
- the sparse/dense gamedata views (`src/deadlock/sparse{,_test}.py`,
  `data/gamedata.dense.tsv/`, `*.defaults.tsv`,
  `decisions.kb/sparse-views-with-defaults-sidecar.md`);
- `weapons` renamed to `ability_profiles`;
- `docs/dev/mechanics.kb/`;
- edits to `.gitignore`, `all.do`, `clean.do`, `README.md`, `docs/dev/`, and
  `src/deadlock/{abilities,ability_upgrades}*`.

`git status` shows all of it. **The per-DLL work is not yours:**
`src/dllscan/`, `bin/winpy`, `src/deadlock/{dll_*,dlls_*}`,
`data/dlls*`, and this `.kb/`.

**`scratchpad/` is where work in progress sits until it graduates; `trash/` is a
recoverable `rm` (`mv -t trash/`).** Replace the tracked `scratchpad/README.md`
("Just some scratch notes.") with a short `scratchpad/CLAUDE.md`:
- what belongs: notes, prototypes, captures that are in progress;
- every item graduates, to `docs/` (knowledge; evidence into
  `docs/dev/probes/`), to `src/` (code), or to `trash/` (superseded, or
  already distilled);
- nothing outside cites it.

`docs/dev/CLAUDE.md`'s citation rule names both `trash/` and `scratchpad/`:
neither will keep existing.
Then graduate the current untracked contents. Content a KB still needs is distilled into that KB, or archived
into `docs/dev/probes/` if it's evidence. A prototype since replaced by
committed code, and anything already distilled, goes to `trash/`. Nothing
else does: `client2.log`/`server2.log` are console captures (check them
against `game-runtime.kb/`), `geist.kb/value.md` is a hero note (check it
against `mechanics.kb/`), and `__pycache__/` is trash. Report where each
went and why.

Use **`Skill(commit)`** to commit it. That skill overrides this
directory's `CLAUDE.md` rule against committing, for this unit only. Split
it into logical commits as the skill guides. Before committing:
- **Review the diff** for anything unfinished or inconsistent. Fix only
  what is plainly mechanical; report anything else instead of committing it.
- **Regenerate on the current build.** `data/deadlock-version.json` says
  6860, but the gamedata TSVs were built on 6857. `redo` the gamedata
  targets (not `data/dlls/`: the store isn't wired into `all.do` yet), so
  the committed views match the committed stamp.
- **Run** `pytest` and `pyright` over the whole repo and get both clean.
  Sibling agents are editing `src/dllscan/` and
  `src/deadlock/dlls_concommands*` concurrently: if one of those files fails
  mid-edit, rerun rather than fixing it.

`.claude/todo.md` also carries one per-DLL line: its status was changed from
`active` to `open`. Commit that with the rest.

**Scope:** the files above, the gamedata outputs `redo` writes, and `trash/`.

## Steps

- [x] Review the diff; fix the mechanical: README's `abilities.tsv` row (said
  "four signature abilities") and "provisions the pinned" VRF line
- [x] `redo all` on the current install (6860): views rebuilt byte-identical,
  so the committed views match the stamp; `deadlock.sparse` re-split cmp-clean
- [x] `pytest` (all pass) and `pyright` (0 errors), whole repo
- [x] Graduate `scratchpad/` contents; `scratchpad/CLAUDE.md` replaces README
- [x] Four commits, mixed files (`.gitignore`, `all.do`, `README.md`,
  `docs/dev/CLAUDE.md`) staged hunk-wise per commit

## Decisions

- One commit for abilities widening + `ability_profiles` + sparse views + data:
  the TSVs, `all.do` and `default.tsv.do` entangle all three, and an
  intermediate commit would not build.
- Console logs to `trash/`, not `probes/`: `game-runtime.kb`'s build-6745 files
  (local-bot-match, server-config-files, sv-cheats) already quote their lines;
  `probes/` holds scripts, and the logs carry a steam id and lobby payload.
- `geist.kb/value.md` to `trash/`: its souls→AP pairs are `levels.tsv`'s
  curve; the rest is a Lady Geist build plan, no formula for `mechanics.kb`.

## Open Questions

## Final report

Commits: `42fcb53` VRF follows latest release (+ `gamedata.list.do`
`-type f` fix, todo.md); `ce765f4` mechanics.kb; `4a0ab4f` every bound
ability, `ability_profiles`, sparse views, data regenerated on 6860;
`539d9e2` `scratchpad/CLAUDE.md`. Scratchpad items now in
`trash/scratchpad-retired/` (`client2.log`, `server2.log`, `geist.kb/`,
`__pycache__/`). Untouched: per-DLL files, this `.kb/`, and a sibling's
`docs/dev/convar-dump.kb/capture-approach.kb/queue-shape-scan.md`.
Deviation: `bin/shell` needed the documented `env -u DIRENV_*` prefix.
