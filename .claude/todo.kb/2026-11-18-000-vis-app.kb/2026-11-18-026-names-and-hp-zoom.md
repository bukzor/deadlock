---
managed-by: Skill(llm-subtask)
status: done
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

## Steps

- [x] `names.py`: localized ability names and property labels (new module, tested)
- [x] `casts.py`: upgrade and extra-damage notes use localized labels
- [x] `queries.py`: `abilities` names; load the tokens
- [x] `measures.py` + `queries.py`: with `hp`, the asked-for horizon zooms out to the kill; note it
- [x] design doc rows, claims, checks, commit

## Decisions

- Names live in a new module, `names.py`, not `queries.py`: `queries_test.py`
  would have passed 300 lines, and `casts.py` needs the property labels too.
- Tokens come from the install's `citadel_heroes` and `citadel_attributes`
  English files (ability names in the first; `{prop}_label` in both), read
  once in `load_data`. No conflicting duplicates between them today; a
  conflict asserts.
- Melee: "Light Melee" / "Heavy Melee", the game's own stat labels.
- A property's token follows its `m_strLocTokenOverride` (150 properties
  carry one), as tooltips do. The "Extra damage not included" note uses the
  same labels as the upgrade note.
- Where the game has no label (127 of 1038 upgrade properties), notes keep
  `_humanize`'s lower-case words, not the raw key, so no engine name reaches
  player text. Filed as `claims.kb/ability-names.md`.
- `default_horizon` is renamed `horizon_used(cycle, hp, asked)`. With `hp`
  out of reach, an asked-for horizon zooms out to 120 s too, matching the
  existing default behaviour (`kill-horizon.md`).
- The zoom note goes after the source's notes and before the "not reached"
  note: "The horizon is zoomed out from 2 s to 15 s, to look for the time to
  kill 1000 HP."

## Open Questions

- The client's horizon inputs still show the typed value while the chart
  spans the zoomed horizon (the `cycle` line carries it). Whether the inputs
  should follow is a client unit's call.
- The design doc's `abilities` row says only `"name"`; it now holds the
  in-game name. Not edited (outside the granted spots).
- Upgrade notes mix casing: game labels are Title Case ("T2 Lifesteal 20"),
  fallbacks lower-case.

## Final report

- Checks: `uv run pytest` (whole server, real data present) and
  `uv run basedpyright src/vis_server/` both clean. Every new assertion was seen
  red, by stub or by mutant (`python -B`, `.pyc` removed, module restored).
  Client untouched, so its checks were not run.
- Live: `/api/abilities?hero=hero_inferno` answers "Incendiary Remarks",
  "Light Melee", "Napalm", and so on; `timeline ... hp=1000&horizon=2` answers
  horizon 15 with the zoom note.
- Design doc: the `horizon` param row and the `time_to_kill` bullet in
  `docs/dev/decisions.kb/vis-app.md` now say the horizon zooms out with `hp`.
- Claims: `kill-horizon.md` rewritten for zoom-out-only; `horizon-default.md`
  reworded; `ability-names.md` added.
- Code: `apps/vis/server/src/vis_server/{names,names_test}.py` (new);
  `casts`, `queries`, `measures`, `conftest` and their tests.
