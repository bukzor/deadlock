---
managed-by: Skill(llm-subtask)
status: open
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

## Decisions

## Open Questions

## Final report
