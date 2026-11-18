---
label: KILL_HORIZON
standing: agent
why:
- horizon-default.md
- judge-on-own-authority.md
- ../../../../../.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-020-ux-review-2.md
- ../../../../../.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-023-player-words-server.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# With hp, the default horizon grows by whole periods past the kill, to 120 s

When `hp` is given and `horizon` is not, the horizon is the fewest whole
periods (whole seconds for a one-shot) whose half-open window holds the
land of the hit that reaches `hp`, never fewer than the 2-period default,
and at most 120 s. When `hp` is not reached by 120 s, the horizon is 120 s
(or the default, if longer), so the note says "not reached within 120 s".

Declined: the kill's land itself, which the half-open window would leave
out; a margin such as +20 %, which breaks "cycles shown" into a fraction;
and keeping the default when `hp` is out of reach, which would answer
"not within 4 s" to a question 120 s could still settle. Overturned if
the owner wants the chart to end at the kill. Built in
`apps/vis/server/src/vis_server/measures.py` (`default_horizon`).
