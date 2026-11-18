---
managed-by: Skill(llm-subtask)
status: open
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../docs/dev/decisions.kb/vis-app.md   # "Client view": zoom out to the kill
  - ./2026-11-18-030-window-and-target.md   # Decisions and Open Questions
  - ../../../apps/vis/docs/dev/claims.kb/window-limits.md
---

# Zoom stops at the hit guard; a hang in a test becomes a failure

**Parent:** <https:../2026-11-18-000-vis-app.md> (review round 5)

## Problem Statement

030's open question: a huge `hp` (e.g. 1e9) zooms to a window the server
refuses (the 10,000-hit guard, a 400). Zoom never zooms in, so the page stays
broken until the user edits the window.

**Decided:** the zoom-out stops at the largest whole-cycle window within the
guard. The time-to-kill row still gives the exact kill time, because the server
computes it from the cycle. When the kill is beyond the largest window, a note
in player words says the chart can't reach it. A window the user types past
the guard is still a 400, with the message saying the largest allowed. Make the
client know the guard without duplicating the number: for example, the server
states the largest window in the `cycle` line, or in the 400 body. Pick one,
and document it where the line kinds are defined.

Also from 030: a mutant of the zero-damage guard hangs the test run instead of
failing it. Make that test fail on its own, with a bounded loop or a timeout,
and see it red.

**Scope:** `apps/vis/server/src/vis_server/*`, `apps/vis/client/src/*`,
`apps/vis/docs/dev/claims.kb/window-limits.md`, and the line-kinds list in
`docs/dev/decisions.kb/vis-app.md` if the `cycle` line gains a field. Every
save leaves the live app working.
