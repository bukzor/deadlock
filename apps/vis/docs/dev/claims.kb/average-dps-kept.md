---
label: AVERAGE_DPS_KEPT
standing: agent
verdict: superseded
why:
- original-request.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# average_dps stays, labelled as DPS over the first N seconds

`average_dps` stays, with the label "DPS over the first {horizon} s". Finding
1 proposed dropping it, as it measures the chosen horizon and not the ability;
the call here keeps it because it reads burst, which neither `uptime_dps` nor
`steady_dps` does. The measures are labelled in player words and ordered with
`uptime_dps`, the one comparable to the card, first. Revisit if players read
it as the ability's DPS. Built by unit 016.

The owner asked for the review that produced this call ("a sub-agent to
ponder the intelligibility and overall UX of this UI", quoted in unit 015's
brief); the finding is in
unit 015's report (`git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-015-ux-review.md`). Design:
[`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md).

Out of force: the design's *Measures* section now has no average DPS,
because the horizon is whole cycles and the average would repeat
`steady_dps` (UX review round 2, finding 3; built by unit 023).

Provenance (the handoff files are retired): `git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-015-ux-review.md`.
