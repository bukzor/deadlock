---
managed-by: Skill(llm-subtask)
status: done
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../docs/dev/decisions.kb/vis-app.md   # "Model" and "Measures": both amended for this unit
  - ../../../apps/vis/docs/dev/claims.md
  - ./2026-11-18-012-end-to-end.md   # how it drove Windows Chrome headless (playwright-core), and serve
---

# Damage over time tiles; `uptime_dps` generalized via a `Cycle`'s downtime

**Parent:** <https:../2026-11-18-000-vis-app.md> (review round 1)

## Problem Statement

The user ran the app on Nurse Harrow's `ability_nurse_leech_therapy` (horizon
30) and gave this feedback, verbatim:

> I have to say I don't understand the result though. What's with the shading?
>
> - "for a gun" seems unwarranted. This can be easily generalized to
>   abilities, no?
> - "steady_dps" seems like it should be lower than "uptime_dps" in the case
>   at hand, yes?

What went wrong:
- **The shading.** Every tick triggered at the cast, so the bars overlapped
  from t=0, and their faint fills stacked into a staircase.
- **`uptime_dps`.** It is computed as per-cycle damage ÷ (period − `reload`).
  A cast has no `reload`, so its uptime collapsed into its steady value: both
  read 3.79.

The design's "Model" and "Measures" sections now state the fix. Implement it:

1. **Ticks tile.** In `casts.py`, a tick's trigger is the previous tick's land
   (the first tick's trigger is the cast).
2. **`reload` → `downtime`.** Rename the `Cycle` field everywhere it appears.
   Set it per source as the design states:
   - **gun:** the reload, unchanged, so the UI-DPS tests still hold;
   - **cast:** the cooldown left after the last land. If the damage outlasts
     the cooldown, decide what happens, and record the decision;
   - **melee:** 0.

   `uptime_dps` divides by `period − downtime`. Rewrite its `check` to cover
   every source, with no "for a gun" special case.
3. **Chart.** Make the client fit the tiled bars:
   - restore a readable fill (the faint fill was there for the overlap);
   - make the tooltip plain: label, trigger, land, wind-up and damage, where
     it now shows "damage 0–8.74" and "time (s): bar spans trigger → land";
   - the x domain covers every bar the server sends, so the second cast's
     bars at t=30 aren't clipped to a sliver.
4. **Ledger.** In `apps/vis/docs/dev/claims.kb/model.kb/`:
   - mark `dot-trigger.md`'s claim superseded with a `verdict:`;
   - file the tiling claim as `standing: agent`, citing the user's feedback
     above;
   - the `uptime_dps` generalization is the user's own suggestion, so file it
     citing their words. Find them in session
     `14fac9c8-bc5e-42f7-956c-f88e2a8e613c` (the message with "for a gun"
     seems unwarranted).

   Validate the ledger as unit 011 did.
5. **Proof.** Screenshot Nurse Harrow `ability_nurse_leech_therapy` at
   horizon 30 and one gun, taken the way unit 012 drove Chrome. Put them in
   `trash/013/` and name them in the Final report. Expected numbers: the
   leech's `uptime_dps` is well above its `steady_dps` (3.79). For guns,
   `uptime_dps` and `steady_dps` are unchanged.

All checks must be clean: pytest, basedpyright `all`, `tsc --noEmit` and
vitest.

**Scope:** `apps/vis/server/src/vis_server/*`, `apps/vis/client/src/*`, and
`apps/vis/docs/dev/claims.kb/model.kb/*`

## Steps

- [x] 1: ticks tile (`casts._ticks`)
- [x] 2: `Cycle.reload` → `downtime`; cast downtime; one `uptime_dps` check
- [x] 3: chart: fill 0.45, plain `title` tooltip, `xDomain`
- [x] 4: ledger: `DOT_TRIGGER` superseded; `DOT_TILING`, `UPTIME_ANY_SOURCE`, `CAST_DOWNTIME`
- [x] 5: screenshots
- [x] checks, commit

## Decisions

- **Damage outlasting the cooldown:** downtime 0, plus a note that casts on
  cooldown overlap; the period is then all uptime. Filed as `CAST_DOWNTIME`
  (`model.kb/cast-downtime.md`), which also covers the per-source table.
- **One `uptime_dps` check:** "deal one cycle (a clip, a swing, a cast) to the
  training dummy; divide its damage by the stopwatch time from the first
  trigger until its downtime starts." The stat-panel hint is gone from the
  check; the docstring and tests keep the gun/UI equivalence.
- **Tooltip** is Plot's `title` channel from a pure `hitTitle`, so it is
  unit-tested and shows exactly label/trigger/land/wind-up/damage.
- **`Gun.reload`** stays: it is the gun's stat; only `Cycle`'s field renamed.
- **`L1273`** added to `claims.md`'s `non-claim-tokens:` beside `L5`/`L1002`
  (outside the brief's scope, one line), so the mentions scan stays clean.
- The user's words are `14fac9c8#L1273`; `UPTIME_ANY_SOURCE` quotes both
  bullets, `DOT_TILING` quotes "What's with the shading?".

## Open Questions

- **Impact-only casts:** `uptime_dps` = damage ÷ cast delay, so a 100-damage
  impact at 0.25 s reads 400/s, and one at delay 0 has no `uptime_dps` at
  all (all downtime). Correct by the definition, but a player may find it odd.
- **The second cast at the horizon:** `repeat` keeps a hit by its trigger, so
  with tiled ticks only the first tick of a cast at t=horizon is sent (one
  bar to 30.48, not 13 to 35.04). Nothing is clipped; it is just less shown.

## Final report

Checks: pytest 144 passed; basedpyright `all` 0 errors; `tsc --noEmit`
clean; vitest 19/19. New tests were each seen red (the downtime-divisor one
by mutating `measures.py`). Ledger: `llm.kb-validate` 22 files 0 errors;
links 30/0 broken; mentions 0; graph 27 nodes, 1 component, acyclic;
grounding shows `DOT_TRIGGER` struck, the new claims grounded on 2 users.

Numbers: leech (horizon 30) `uptime_dps` 22.54, `steady_dps` 3.79. Guns
unchanged: the real-data oracle test still matches `ability_profiles`
dps/sdps for every live gun; Infernus 52.38 / 29.2.

Screenshots (`trash/013/`): `hero_nurse.ability_nurse_leech_therapy.horizon-30.png`,
`hero_nurse.ability_nurse_leech_therapy.tip.png`,
`hero_inferno.citadel_weapon_inferno_set.png`,
`hero_inferno.citadel_weapon_inferno_set.tip.png`. Driven by
`trash/012/driver/drive.mjs` against my own server on :8788 and a
throwaway headless Chrome profile, both stopped after.

Deviations: the `claims.md` token line (Decisions). Results:
`apps/vis/server/src/vis_server/{timeline,casts,measures}.py` and tests,
`apps/vis/client/src/chart{,.test}.ts`, `apps/vis/docs/dev/claims.kb/model.kb/`.
