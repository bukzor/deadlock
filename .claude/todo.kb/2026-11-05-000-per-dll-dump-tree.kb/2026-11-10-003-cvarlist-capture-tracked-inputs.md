---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-10-001-cvarlist-oracle-check.md
  - docs/dev/game-runtime.kb/cvarlist-capture.md
  - data/cvarlist/default.log.do
  - data/dlls.check/cvarlist.do
---

# The `cvarlist` captures depend on their inputs, not `redo-always`

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the `cvarlist` oracle)

## Problem Statement

`data/cvarlist/<side>.log` is `redo-always`, so every run of the check
relaunches the game. A capture has three inputs, and each one can be
tracked:

- **The install:** the DLLs it loads and `gameinfo.gi`. Depend on
  `data/dlls/file.tsv`, which holds every listed DLL's sha256, and on
  `gameinfo.gi`.
- **The user's saved settings:** the client capture's 58 user values
  (`differences`, 6860). The user believes they are all in `.cfg` files in
  the game tree. Measure it first: find which files hold each of the 58
  names and values, whether in the game tree, a `.vcfg`, or Steam's
  `userdata/<id>/1422450/`. If any value has no file, stop and report.
  Also find which settings files the server side reads, if any.
- **The Steam session:** leave it untracked. State that as an assumption in
  `cvarlist-capture.md`.

**A launch may rewrite its own inputs** (archived settings are typically
written at quit). Measure it: take each input file's mtime and sha256
before and after a client launch. Then make the capture depend on
contents, not mtimes. One way: a `redo-always` target that hashes the
input files and `redo-stamp`s the result, with the capture
`redo-ifchange`-ing that target. A rewrite with the same content must
not trigger a relaunch.

**Acceptance (6860):**
- `redo data/dlls.check/cvarlist` launches both sides and passes.
- A second run launches nothing and passes.
- Changing one input relaunches only the sides that depend on it. Do this
  with a harmless edit made and reverted inside a copy, or by `touch` plus
  `redo-stamp`, not by editing the user's settings.
- A plain `redo` still launches nothing, and `git diff data/` is empty.

**Scope:** `data/cvarlist/*.do` (plus a new stamp target if you take that
route), `docs/dev/game-runtime.kb/cvarlist-capture.md`. Never modify the
user's settings or install files. Read and hash them only.

## Steps

- [x] Locate the 58 `differences` values (`trash/003/where.{py,tsv}`): every one has a file
- [x] Find what the server reads: nothing (its logs, server.cfg values unapplied)
- [x] Hash every candidate before/after a client and a server launch (`trash/003/snap.sh`, `{before,after}-*.tsv`)
- [x] `data/cvarlist/default.inputs.do`; `default.log.do` depends on it, `file.tsv`, the script
- [x] Acceptance runs (`trash/003/redo-*.log`); `cvarlist-capture.md`

## Decisions

- **The user's belief was wrong:** 57 of 58 values live in Steam's `userdata/37093539/1422450/`
  `.vcfg` files (36 `local/cfg/machine_convars.vcfg`, 21 `remote/user_convars.vcfg` + its
  local copies). Only `citadel_bot_match_host_locally` is in the game tree (`cfg/autoexec.cfg`).
  The game tree's `machine_convars.vcfg`/`user_convars_0_slot0.vcfg`/`video.txt` are stale
  (Sep 29): 24 of the 58 differ there, 9 absent. Not inputs.
- **Server reads no settings file:** `server.cfg`'s `sv_cheats 1` lists `false`; `rate` is
  gameinfo's, not `machine_convars.vcfg`'s; no `USRLOCAL`. Its stamp hashes gameinfo.gi only.
- **Client inputs:** gameinfo.gi, `cfg/autoexec.cfg`, `local/cfg/{machine_convars.vcfg,
  user_convars_0_slot0.vcfg,video.txt}`, `remote/user_convars.vcfg`. `video.txt` is logged
  loaded and holds 2 listed names. The local slot copy is hashed too (cheap: rewritten
  byte-identical), in case the cloud copy isn't what loads.
- **Launch rewrites:** client 13 files (12 byte-identical, Steam's `remotecache.vdf` differs,
  not an input), server `boot.vcfg` (identical). So the stamp hashes content.
- **`<side>.inputs`:** `redo-always` + `redo-stamp` of `sha256sum` lines. Gameinfo goes in
  the stamp too, not a direct mtime dep. The Steam root is the install's `../../..`; exactly
  one `userdata/*/1422450` or it fails.

## Open Questions

- [ ] Out of scope, stale: `data/dlls.check/cvarlist.do`'s comment says each log is "a fresh
      launch of the game". Plain `redo` needs the `env -u DIRENV_*` prefix (`redo-adopt` is in `.venv/bin`).

## Final report

Files: new `data/cvarlist/default.inputs.do`; edited `data/cvarlist/default.log.do`
(`redo-always` → `redo-ifchange ../../bin/cvarlist-capture ../dlls/file.tsv "$2.inputs"`),
`docs/dev/game-runtime.kb/cvarlist-capture.md` (Procedure; new "What a capture reads" with the
measurements and the untracked assumptions: Steam session, files autoexec.cfg execs, Steam root
layout). Targets: `data/cvarlist/{server,client}.inputs` (gitignored).

Acceptance (6860): run 1 `redo data/dlls.check/cvarlist` launched both, exit 0, 14 s, counts
1765/2513. Run 2: no launch, exit 0, 1.8 s (check reran only because `redo` forces its target).
`touch autoexec.cfg` + `redo-ifchange`: no launch, check not rerun. A temporary client-only line
in the stamp (and its revert): client relaunched each time, server.log untouched. Plain `redo`:
`all`, `(gamedata.list)`, `date.txt`, no launch. `git diff data/` shows only the two `.do`
edits, no generated file. No user settings or install file written by me except one `touch`.
