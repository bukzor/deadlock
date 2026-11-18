---
managed-by: Skill(llm-subtask)
status: open
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

## Decisions

## Open Questions

## Final report
