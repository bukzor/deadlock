---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-10-000-cvarlist-capture.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-10-000-cvarlist-capture.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-026-registry-readback-check.md
  - docs/dev/game-runtime.kb/cvarlist-capture.md
  - docs/dev/cvar-dump.kb/validation.md
  - docs/dev/probes/cvarlist_vs_store.py
  - bin/cvarlist-capture
---

# The `cvarlist` oracle check: the store against the engine's own listing

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the step "On-demand
check: the `cvarlist` oracle")

## Problem Statement

The capture works (`bin/cvarlist-capture`, 2026-11-10-000), and
`cvarlist_vs_store.py` ran the comparison as a probe. Promote it to a
built, on-demand check, as `data/dlls.check/registry` is:

- **The captures as targets:** `data/cvarlist/{server,client}.log`
  (gitignored: Valve data), each made by `bin/cvarlist-capture`. A capture
  reads user state (the client's own values) as well as the install, so it
  is not a function of tracked inputs. Decide how redo should treat it, and
  report the decision.
- **`deadlock.cvarlist`:** parses a capture into typed records (name, value,
  flags, help), with tests on excerpts from the real format.
- **`deadlock.cvarlist_check`:** the listing against `convars.tsv` and
  `concommands.tsv`. Write each of the capture's findings as one rule with
  its source, not a list of names:
  - Every listed name is in the store.
  - Every store declaration of a DLL that side loaded is listed, unless it
    is `developmentonly`, `hidden`, or a `-` command. Take the set of loaded
    DLLs from evidence in the capture, not from a hand list.
  - Flags agree through the listing's abbreviations, and the flags it never
    prints are excluded.
  - Help agrees through the listing's print rule.
  - Values: the listing prints current values, not defaults. A value equals
    the store default unless the name's override has a source: `gameinfo.gi`'s
    `ConVars` block (read it from the install, with an existing parser if one
    fits) or the capture's own `differences` output.
  - Print a summary of counts per side. Any mismatch fails with the names.
- **`data/dlls.check/cvarlist.do`:** on demand, not in `all.do`.
- **Docs:** `validation.md`'s Oracle `[!TODO]` becomes fact, pointing at the
  target. `cvarlist_vs_store.py` stays (probes are archived evidence).

**Acceptance (6860):** `redo data/dlls.check/cvarlist` launches both sides,
exits 0 and prints counts matching the capture's report (server 1765, client
2513). A mutant in a rule makes it fail (`-B`, delete the `.pyc`). `pytest
src` and `pyright` are clean. A plain `redo` launches no game, and `git diff
data/` is empty.

**Scope:** new `src/deadlock/{cvarlist,cvarlist_check}{,_test}.py`, new
`data/cvarlist/*.do` and `data/dlls.check/cvarlist.do`, `.gitignore` if
needed, `docs/dev/cvar-dump.kb/validation.md`.

## Steps

- [x] Read the brief, its inputs, and 6860's captures in `trash/cvarlist/`
- [x] Measure each rule on the real captures (`trash/001/measure.py`)
- [x] `deadlock.cvarlist` + tests; 17 hand mutants, 1 equivalent survivor (`trash/001/cvarlist.mutants`)
- [x] `deadlock.cvarlist_check` + tests; 43 hand mutants all killed (`trash/001/check{,2}.mutants`)
- [x] `data/cvarlist/default.log.do`, `data/dlls.check/cvarlist.do`, `.gitignore`
- [x] Acceptance run; mutants through redo; plain `redo`; `git diff data/` (logs `trash/001/redo-*.log`)
- [x] `validation.md`

## Decisions

- **Captures are `redo-always`.** A capture reads what no tracked input records
  (install, Steam session, the user's settings), so redo can never know it's current.
  Each check run launches both sides afresh (16 s). `all.do` never reaches them.
- **`gameinfo.gi` via `vdf`** (ValvePython, `vpk`'s sibling; `uv add vdf`, stub
  `typings/vdf/`). `keyvalues3` reads KV3 only. Last duplicate key wins.
- **Loaded DLLs:** those that alone listably declare some listed name. A listed name
  that no proven-loaded DLL declares is explained by all its listable declarations
  (server `r_fullscreen_gamma`: `rendersystem{dx11,empty,vulkan}`, none provable).
- **`sv`/`cl` are `gamedll`/`clientdll`'s words.** A declaration's own per-DLL flag
  prints too (`voice_threshold`, engine2.dll, `clientdll`: prints `cl`).
- **Help:** the explaining declarations' one non-empty help (`bot_mimic`: client.dll's
  null, server.dll's text). Two different helps fail.
- **Floats print as shortest repr minus `.0`** (`1e-05`, `1000000`), not `%g`.
- **`differences` has 5 columns** (name value default flags help), so a user-changed
  name's default is checked too, through the table's `default` column.
- **No listed `reference` declaration** on 6860: asserted, not given a rule.

## Open Questions

- [ ] Out of scope, stale: `cvarlist-capture.md` calls `differences` a `name value` table
      (it also prints default, flags as full words, help); its Procedure could name
      `redo data/dlls.check/cvarlist`. `clean.do` skips `data/cvarlist/`.

## Final report

Files: new `src/deadlock/{cvarlist,cvarlist_check}{,_test}.py`, `data/cvarlist/default.log.do`,
`data/dlls.check/cvarlist.do`, `typings/vdf/__init__.pyi`; edited `.gitignore`,
`pyproject.toml` + `uv.lock` (`vdf`), `docs/dev/cvar-dump.kb/validation.md` (Oracle as fact).

API: `cvarlist.parse(text) -> Capture(entries, total, differences)`, `Entry(name, value, flags:
tuple[str, ...], help)`, `Difference(name, value, default, flags, help)`.
`cvarlist_check.check(label, capture, store, gameinfo) -> list[str]`; `declarations(convars_tsv,
concommands_tsv) -> list[Declaration(dll, name, flags, help, type, default)]` (`type` None: a
command); `overrides(gameinfo_text) -> dict[str, str]`; `listable`, `loaded_dlls`, `explaining`,
`printed_words`, `printed_help`, `render`, `parse_override`, `expected_value`; `UNLISTED`,
`NEVER_PRINTED`, `WORDS`. CLI `python -m deadlock.cvarlist_check SIDE.log GAMEINFO.gi CONVARS.tsv CONCOMMANDS.tsv`.

Acceptance (6860): `redo data/dlls.check/cvarlist` exit 0, 16 s, both sides launched. Server:
listed 1765 = total; 13 DLLs loaded, all 4329 of their listable declarations listed; values from
command 526, gameinfo.gi 23, store 1216. Client: 2513; 18 DLLs, 7270; command 724, differences 58,
gameinfo.gi 26, store 1705 (`data/dlls.check/cvarlist` has the full summary).
Mutants through redo (pyc deleted, `PYTHONDONTWRITEBYTECODE`): `WORDS` archive→`arch` fails
('flags', [...]); floats as `%g` fails ('value', ['r_particle_max_draw_distance']); restored passes.
Plain `redo`: only `all`, `gamedata.list`, `date.txt`, no launch; all 624 data files byte-identical;
`git diff data/` empty. `pytest src`, `pyright` clean. Deviation: the `vdf` dependency and its stub.
