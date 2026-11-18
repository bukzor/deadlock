---
label: CUMULATIVE_LINE
standing: agent
why:
- original-request.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# A cumulative-damage line is the main read; the bars stay

The chart's main read is a cumulative-damage step line on a right-hand axis,
whose slope is the DPS and whose dashed `hp` line gives time to kill. The bars
stay, one per hit and as tall as the hit's damage, as the request specified
(`VIS_REQUEST`). Declined: dropping the bars, or letting bar height or area
stand for damage output, which the eye reads as such but which is only one
hit's size (finding 2). The owner can overrule this, since the bars are their
spec. Built by unit 017.

The owner asked for the review that produced this call ("a sub-agent to
ponder the intelligibility and overall UX of this UI", quoted in unit 015's
brief); the finding is in
unit 015's report (`git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-015-ux-review.md`). Design:
[`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md). Revisit if the owner would rather the bars carry the main read.

Provenance (the handoff files are retired): `git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-015-ux-review.md`.
