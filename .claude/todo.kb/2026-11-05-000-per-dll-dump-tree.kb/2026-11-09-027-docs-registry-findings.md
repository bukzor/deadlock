---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-026-registry-readback-check.md
  - docs/dev/cvar-dump.kb/CLAUDE.md
---

# Docs: what the registry readback established

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the step "Docs: drop
each `[!TODO]` callout as it lands …")

## Problem Statement

026 built the registry readback (`data/dlls.check/registry`) and measured,
on 6860, things the KB states otherwise or leaves open. Its Decisions and
Open Questions list them. Bring `docs/dev/cvar-dump.kb/` to that truth:

- `capture-approach.kb/icvar-hook.md`: the "494 against the queue's 493"
  commands was the shared tier0 `<unknown>` record an invalid index returns;
  the registry holds exactly the queue's distinct names. The "unexplained"
  flag changes are the measured flag rule (per-DLL flag added; `reference`
  declarations lose `developmentonly defensive`; tier0 runtime flags on one
  convar per DLL). Resolve its `[!QUESTION]`s that 026 answered. Keep the
  open one (why that one convar carries the runtime flags) as a
  `[!QUESTION]`.
- Anywhere else in the KB that states one of these facts (grep for them:
  `registration-flow.md`'s per-DLL flag, `output-views.md`'s merged-view
  question).

- `capture-approach.kb/registry-walk.md`: its title says "after Connect",
  but the replay runs in `Init`; rename the title (and the file, if its
  name says the same, updating every reference). Its "Against" paragraph
  states DumpSource2's cross-DLL merge rule as fact, which contradicts
  `output-views.md` (the rule is to be taken from tier0, still a
  `[!QUESTION]`). Make it agree with `output-views.md`.

State each as fact with its build and point to the check, not to the
handoff. Don't change the design.

**Check:** `~/.claude/skills/llm-kb/bin/llm.kb-validate-links` over
`docs/dev/` and `.claude/todo.kb/` reports no broken links.

**Scope:** `docs/dev/cvar-dump.kb/**`. A sibling (028) runs builds
concurrently; it edits nothing under `docs/`.

## Steps

- [x] Re-measure 026's findings from its readback (`trash/026/run1/`) against `data/dlls/`
- [x] `icvar-hook.md`; then the other KB files that state them
- [x] `registry-walk.md`: title and "Against" (the brief's later item)
- [x] Link check

## Decisions

- **6854's flag sentence removed, not annotated.** Its "20 gain `developmentonly|defensive`"
  has the direction backwards on 6860 (the declaration carries them; the `reference`
  registration lacks them), and its "5 others" are the 4 convars that already declare `gamedll`
  plus the 1 with tier0's runtime bits. The 6860 rule replaces it as fact.
- **The "replays before `Init` stops" `[!QUESTION]` narrowed**, not dropped: answered for
  `server` and `client` only. Its tier0 half narrowed too: measured (026's readback against the
  committed `concommands.tsv`/`convars.tsv`) that none of tier0's 27 queue names is in either
  registry, so the cvar system's `Connect` doesn't register tier0's queue; whether tier0's `Init`
  does stays open.
- **`output-views.md`:** the flag changes at registration moved out of the `[!QUESTION]` as
  fact; the question keeps only the merge rule (the check compares once-declared names only).
- **`registry-walk.md`:** title and mechanism say "after `Init`" (the replay runs there,
  `registration-flow.md`); no rename, the filename doesn't say "Connect", so no references
  changed. "Against" now defers the merge rule to tier0, open in `output-views.md`; verdict
  unchanged. One sentence: the built readback check is this walk, one DLL per process.
- **`capture-approach.md`:** the readback check is no longer a "later use".

## Open Questions

- [ ] Why one convar per DLL carries `initial_setvalue performing_callbacks` (kept as a
      `[!QUESTION]` in `icvar-hook.md`).

## Final report

Files: `docs/dev/cvar-dump.kb/capture-approach.kb/{icvar-hook,registry-walk}.md`,
`docs/dev/cvar-dump.kb/{registration-flow,output-views,capture-approach}.md`.

- `icvar-hook.md`: 6854's "494 vs 493" and "5 unexplained" flags replaced by a 6860 section
  pointing at the check (`validation.md`, "Registry readback"): both DLLs replay whole queues;
  registry = queue's distinct names; walk ends (null / the 0xFFFF `<unknown>` record); the flag
  rule; the runtime-bit convars. New `[!QUESTION]` on those bits; replay/tier0 one narrowed.
- `registration-flow.md`: per-DLL flag skips `reference` declarations; their registry flags
  lack `developmentonly defensive`.
- `output-views.md`: flag changes as fact; `[!QUESTION]` is the merge rule only.
- `registry-walk.md`: "after `Init`" in title and mechanism; "Against" agrees with
  `output-views.md` (merge rule tier0's, open); points at the readback check.

Check: `llm.kb-validate-links docs/dev/ .claude/todo.kb/`: 50 links in 77 files, 0 broken.
(`llm.kb-validate` isn't installed in this repo's env; no frontmatter was added.)
Deviations: none from the brief's scope; design unchanged.
