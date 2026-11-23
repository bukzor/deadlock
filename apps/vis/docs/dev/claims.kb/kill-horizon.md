---
label: KILL_HORIZON
standing: agent
verdict: superseded
why:
- horizon-default.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# With hp, the horizon zooms out by whole periods past the kill, to 120 s

When `hp` is given, the horizon is the asked-for one (or the 2-period
default) zoomed out, never in: the fewest whole periods (whole seconds for
a one-shot) whose half-open window holds the land of the hit that reaches
`hp`, never less than the asked-for or default horizon, and at most 120 s.
When `hp` is not reached by 120 s, the horizon is 120 s (or the asked-for
or default horizon, if longer), so the note says "not reached within
120 s". When it zooms out a horizon the user asked for, a note says so,
because the client's inputs still show the horizon the user typed.

The owner asked for it ("i'd like setting the hp to 'zoom' (zoom out, if
necessary? or zoom unconditionally?) to include the TTK", quoted in unit
026's brief), and the brief settled zoom out only. Declined: the kill's
land itself, which the half-open window would leave out; a margin such as
+20 %, which breaks "cycles shown" into a fraction; zooming in, which would
discard a horizon the user chose; and keeping the horizon when `hp` is out
of reach, which would answer "not within 4 s" to a question 120 s could
still settle. Overturned if the owner wants the chart to end at the kill.
Built in `packages/bukzor-deadlock-damage/src/bukzor_deadlock_damage/measures.py` (`horizon_used`).

Out of force: the owner ruled that the window and the target hp are two
separate values, and that a change to hp moves the window only when the
time to kill would not be visible. The server no longer zooms and has no
time cap: it measures `time_to_kill` wherever the kill falls, and the
client zooms out to the fewest whole cycles that show it. Design:
[`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md), *Client
view* and *Measures*; built by unit 030
(brief (`git show c940883:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-030-window-and-target.md`)).
The limit on a window is now `window-limits.md`.

Provenance (the handoff files are retired): `git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-020-ux-review-2.md`; `git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-023-player-words-server.md`; `git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-026-names-and-hp-zoom.md`.
