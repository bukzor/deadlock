---
label: BAR_WIDTH_CAPTION
standing: agent
why:
- original-request.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# A caption per kind says what a bar's width means

Each bar carries a caption naming its width: bullet travel for a gun, assumed
wind-up for melee, time since the previous tick for a damage-over-time tick.
Damage-over-time ticks keep their width, so the ticks tile their duration
(`DOT_TILING`). Declined: one caption for all (it promises a wind-up that only
cast delays deliver), and dropping the width of ticks (finding 4). The owner
can overrule whether ticks should carry width at all. Built by unit 017.

The owner asked for the review that produced this call ("a sub-agent to
ponder the intelligibility and overall UX of this UI", quoted in unit 015's
brief); the finding is in
unit 015's report (`git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-015-ux-review.md`). Design:
[`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md). Revisit if the owner drops tick width.

Provenance (the handoff files are retired): `git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-015-ux-review.md`.
