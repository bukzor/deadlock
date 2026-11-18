---
label: WINDOW_LIMITS
standing: agent
why:
- judge-on-own-authority.md
- horizon-default.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# A window is limited by its hits, and a one-shot has no cycles

The server refuses a window whose cycles hold more than 10,000 hits,
with a 400 that says how many it holds; there is no limit in seconds,
so a slow cycle can be shown as far out as its kill. 10,000 bars is
about what the browser chart draws without stalling. Declined: a cap in
seconds, which the owner rejected; and no limit, which lets one typo
(`1e9`) hang the server and the tab.

The `cycle` line states the largest window (`max_horizon`, in seconds, whole
cycles; `null` for a one-shot), and the 400 names it, so the client never
holds the number. The zoom to the kill stops at that window; when the kill is
beyond it, a note says the chart can't reach it, and the time-to-kill row,
computed from the cycle, still gives the time. Declined: a zoom that
overrides the guard, which leaves the page on a 400 until the user edits the
window (`[!DRAFT]` agent call, 2026-11-18, brief 031).

A one-shot asked for in `cycles` gets its default 10 s window and a note
saying it has no cycles. Declined: a 400, which would break the page
whenever the user switches from a gun shown in cycles to a one-shot.

Overturned if the owner wants the zoom to override the hit limit, or a one-shot's cycles to mean something.

Provenance (the handoff files are retired): `git show c940883:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-030-window-and-target.md`; `git show c940883:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-031-zoom-within-guard.md`.
