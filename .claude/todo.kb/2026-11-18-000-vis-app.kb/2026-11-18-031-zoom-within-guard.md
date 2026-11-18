---
managed-by: Skill(llm-subtask)
status: done
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

## Steps

- [x] server: `max_horizon` on the `cycle` line; the 400 names the largest window (`queries.py`)
- [x] client: `zoomToKill` stops at it; `unreachableKillNote`; wired in `App.tsx` last
- [x] test hang: `within(seconds)` in `conftest.py` (SIGALRM), used on the zero-damage test
- [x] docs: `window-limits.md`, line kinds in `vis-app.md`

## Decisions

- Chose the `cycle` line (not the 400 body) to carry the guard: the client knows it before any error. Field `max_horizon`, seconds, whole cycles; `null` for a one-shot; optional in the TS type for older servers.
- Timeout via a SIGALRM context manager, not a new dependency (no pytest-timeout).
- Note for an unreachable kill is client-derived and shown first in the notes list.

## Open Questions

- A cycle with more than 10,000 hits itself (no whole cycle fits) has `max_horizon` of 0 and no window passes; not seen in real data.
- No headless-Chrome screenshot taken (not asked for in the brief); logic is covered by vitest and by a real-data API check (hp 1e9 answers; seconds 1e9 gives the 400 naming 10607.3 s).

## Final report

- Checks: server pytest all pass, basedpyright 0/0/0; client tsc clean, vitest 67 pass.
- Red seen: zero-damage guard mutant now fails in 5 s with TimeoutError (was a hang); one-shot `max_horizon` mutant, cap mutants (`n = cap + 1`, dropped already-largest check, off-by-one note) all red. The `+ 1` mutant of the server's largest-window count loops long in the `nextafter` correction rather than failing quickly (red by hang; not bounded).
- Deviations: none.
