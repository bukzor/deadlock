---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-10-001-cvarlist-oracle-check.md
  - docs/dev/game-runtime.kb/cvarlist-capture.md
---

# `cvarlist-capture.md` and `clean.do` catch up with the oracle check

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the `cvarlist` oracle)

## Problem Statement

001's Open Questions name two stale spots:

- `docs/dev/game-runtime.kb/cvarlist-capture.md` calls `differences` a
  name/value table. It prints five columns: name, value, default, flags
  (full words), help. Its Procedure should lead with
  `redo data/dlls.check/cvarlist`, the built way to capture and check, and
  keep `bin/cvarlist-capture` as the manual capture.
- `clean.do` doesn't remove `data/cvarlist/`. Add it to the `git clean`
  pathspecs there, keeping the `.do` files. Confirm with `git clean -ndX --
  data/cvarlist` that only captures would go.

**Check:** `~/.claude/skills/llm-kb/bin/llm.kb-validate-links` over
`docs/dev/` reports no broken links.

**Scope:** `docs/dev/game-runtime.kb/cvarlist-capture.md`, `clean.do`.

## Steps

- [x] Read the brief, 001's report, the doc, `clean.do`, 6860's captures in `data/cvarlist/`
- [x] `cvarlist-capture.md`: Procedure leads with `redo data/dlls.check/cvarlist`;
      `bin/cvarlist-capture server|client DIR` as the manual capture
- [x] `cvarlist-capture.md`: `differences` as the five-column table; closing line
      names what `deadlock.cvarlist_check` does
- [x] `clean.do`: `data/cvarlist` in the `git clean` pathspecs and its comment
- [x] Checks: `git clean -ndX -- data/cvarlist`, `bash -n clean.do`, link validator

## Decisions

- **Manual capture writes to `DIR`, not `trash/cvarlist`.** `docs/dev/CLAUDE.md`
  forbids citing `trash/`; the redo target is now the durable home.
- **"about 70" became 58**, the count `cvarlist.parse` gives on 6860's client capture
  (and the check's summary, `differences 58`).
- **The closing "So an oracle ..." line now states the check's rule** (apply
  `gameinfo.gi`; a `differences` name against its `default` column) instead of
  "skip the client's `differences` names", which the check no longer does.

## Open Questions

## Final report

Files: `docs/dev/game-runtime.kb/cvarlist-capture.md`, `clean.do`.

Checks: `git clean -ndX -- data/cvarlist` lists only `client.log` and `server.log`
(`default.log.do` is kept by `.gitignore`'s `!/data/cvarlist/*.do`). `bash -n clean.do`
clean. `llm.kb-validate-links docs/dev`: 53 links in 46 files, 0 broken. Not run:
`redo clean` itself (it would wipe every output). Deviations: none beyond the
Decisions above (`trash/` citation dropped, count corrected).
