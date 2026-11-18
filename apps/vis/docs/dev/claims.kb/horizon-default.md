---
label: HORIZON_DEFAULT
standing: agent
why:
- original-request.md
- judge-on-own-authority.md
- ../../../../../.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-015-ux-review.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# The horizon defaults to two periods of the cycle

When neither `seconds` nor `cycles` is given, the server uses exactly 2
periods of the cycle, and 10 s for a cycle that happens once; `hp` never
changes it. The server sends a `cycle` line with the period and the horizon
used, so the client shows the window in seconds and in cycles shown. The owner amended finding 3 (unit 016's brief records
their words): two mutually-updating inputs, so that by default the page shows
two full cycles. Declined: a fixed 10 s (a cast shows one burst, then nothing,
while `steady_dps` describes a cooldown never drawn), and a 10 s floor. Built
by unit 016 (server) and 017 (client).

The owner asked for the review that produced this call ("a sub-agent to
ponder the intelligibility and overall UX of this UI", quoted in unit 015's
brief); the finding is in
[unit 015's report](../../../../../.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-015-ux-review.md). Design:
[`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md).
