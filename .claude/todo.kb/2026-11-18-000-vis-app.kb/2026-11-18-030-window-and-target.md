---
managed-by: Skill(llm-subtask)
status: open
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../docs/dev/decisions.kb/vis-app.md   # "Protocol" (timeline params), "Measures" (time_to_kill), "Client view" (the window and the target)
  - ../../../apps/vis/server/src/vis_server/queries.py
  - ../../../apps/vis/client/src/App.tsx
  - ../../../apps/vis/client/src/selection.ts
---

# The window and the target hp: two separate values, and zoom out only to show the kill

**Parent:** <https:../2026-11-18-000-vis-app.md> (review round 5: the user's review)

## Problem Statement

The user: "the interaction among the three x-axis controls needs fully
revised". They object to the 120 s cap, and to fields that don't show what the
chart shows. The design doc's "Client view" section now holds the decided
behaviour, and its "Protocol" and "Measures" sections the server's side. Build
it:

- **Server:**
  - The window is at most one of `seconds` or `cycles`; the old `horizon`
    param goes. `hp` no longer touches the window: remove the zoom, its note
    and the 120 s cap.
  - `time_to_kill` is computed from the cycle wherever the kill falls. It
    needs no unrolled hits beyond the window.
  - Guard against absurd windows by the number of hits (a 400 with a clear
    message), not by seconds.
- **Client:**
  - State is the window (`{by: "seconds" | "cycles", value}`) and `hp`,
    separately, both in the URL.
  - Both window fields show the resolved window. The field being typed in
    keeps the user's text until they leave it, so the cursor never jumps.
  - Zoom out to the kill as the design says: on a change to `hp`, hero,
    ability or level, never on a window edit. Use the fewest whole cycles that
    show the kill.
  - In React terms: one `useState` per value, derived displays, and a local
    draft per input. No effect may write the window in response to the
    window.
- **Tests:**
  - Pure functions for the zoom rule and the conversions, in
    `selection.ts` or a new module, with vitest. 028 found `App.tsx`
    untested; don't add untested logic there.
  - Each new assertion is seen red.

Update `apps/vis/docs/dev/claims.kb/` where a claim no longer holds
(`kill-horizon.md`, `horizon-default.md`): supersede it, citing the design
doc.

**Proof:** in headless Chrome, take screenshots in `trash/030/`:
- hp typed with the kill inside the window (no zoom);
- hp typed with the kill outside (zoom to whole cycles);
- a hero switch that pushes the kill out;
- seconds typed below the kill (the window stays, and the time-to-kill row says
  where the kill is).

Use your own `PORT=5230 API_PORT=8830 apps/vis/bin/serve`, and clean up as
CLAUDE.md says.

**Scope:** `apps/vis/server/src/vis_server/*`, `apps/vis/client/src/*`,
`apps/vis/docs/dev/claims.kb/**`, `apps/vis/README.md` if it names `horizon`.
Every save leaves the live app working.
