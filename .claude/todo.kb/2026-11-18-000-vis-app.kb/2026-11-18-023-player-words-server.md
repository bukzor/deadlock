---
managed-by: Skill(llm-subtask)
status: open
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../docs/dev/decisions.kb/vis-app.md   # "Measures" (rewritten for this unit), "Protocol"
  - ./2026-11-18-020-ux-review-2.md   # Final report: findings 3, 4, 6, 8 are this unit's
  - ../../../apps/vis/server/src/vis_server/
---

# Server: measures and labels in the player's words, hp answered first, a clean hero list

**Parent:** <https:../2026-11-18-000-vis-app.md> (review round 3)

## Problem Statement

UX review round 2's findings 3, 4, 6 and 8 are server work. The design doc's
"Measures" section now states the decided outcome. Make the code match it:

- `time_to_kill` comes first when `hp` is given. With `hp` and no `horizon`,
  the default horizon stretches to the time-to-kill land, up to 120 s, but never
  below 2 periods. When the hp is still not reached, the note says so, as now.
- `uptime_dps` is omitted where it equals `steady_dps` (downtime 0) as well as
  for a single hit.
- `card_dps`: for a cast whose ability has a card DPS (its `DPS` property), the
  value at the given spirit and level. Label it so a player recognises the
  card's number.
- `average_dps` is gone.
- Labels and `check` text by kind: no label or check names another kind ("≈
  stat panel for guns", "(a clip, a swing, a cast)"). Keep each check short,
  one sentence a player can follow in the sandbox.
- `heroes`: sorted by display name, without `in_development` heroes
  (`heroes.tsv`) or the training dummy.

File each judgement call you make as an agent claim in
`apps/vis/docs/dev/claims.kb/` (see its CLAUDE.md).

**Scope:** `apps/vis/server/src/vis_server/*` and `apps/vis/docs/dev/claims.kb/**`.
`apps/vis/client/src/protocol.ts` too, only if a line's shape changes; a
new measure `name` needs no client change.

**Servers:** use your own ports for any proof run, and kill only the pids you
started. A `pkill -f` pattern kills the user's serve on 5173/8788.
