---
managed-by: Skill(llm-subtask)
status: open
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../docs/dev/decisions.kb/vis-app.md   # "Protocol", "Measures"
  - ../../../src/deadlock/loc.py   # parses the game's localization
  - ../../../apps/vis/server/src/vis_server/queries.py
---

# Server: ability names players know, and target hp always zooms out to the kill

**Parent:** <https:../2026-11-18-000-vis-app.md> (review round 4: the user's manual review)

## Problem Statement

The user's review, verbatim where it matters:

- "can we get humanized names for `ability`? as we do for `hero`." The
  `abilities` query's `name` is the machine key today. Use the in-game name from
  the game's English localization (`deadlock.loc`). Fall back to the key when
  there is none, and give `melee_light` and `melee_heavy` plain names. Upgrade
  notes ("T2 dps 0.6") use localized names too, where they exist; this replaces
  the regex humanizing.
- "i'd like setting the hp to 'zoom' (zoom out, if necessary? or zoom
  unconditionally?) to include the TTK". **Decided:** zoom out only, never in.
  With `hp`, the horizon used is the larger of the asked-for (or default)
  horizon and the time-to-kill land, still capped at 120 s. Today the stretch
  only happens when `horizon` is absent. When it stretches the horizon, emit a
  note in player words saying so, because the client's inputs show the horizon
  the user typed.

Update the design doc's `horizon` param row and the `time_to_kill` bullet to
match, and say so in your report. The coordinator has granted that edit to this
unit.

**Scope:** `apps/vis/server/src/vis_server/*`, `apps/vis/docs/dev/claims.kb/**`,
and the two named spots in `docs/dev/decisions.kb/vis-app.md`. Every save leaves
the live app working.
