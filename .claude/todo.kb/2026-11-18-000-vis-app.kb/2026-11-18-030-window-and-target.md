---
managed-by: Skill(llm-subtask)
status: done
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

## Steps

- [x] server: `kill_time` from the cycle, any distance out (`measures.py`)
- [x] server: `seconds`/`cycles` window, no `horizon`, no zoom, hit-count guard (`queries.py`)
- [x] client: pure window/zoom functions (`window.ts`), chart draws the kill only inside the window
- [x] client: `App.tsx` wired to window + hp state, drafts per input
- [x] claims, README
- [x] headless-Chrome proof in `trash/030/`
- [x] checks, commit

## Decisions

- `kill_time` binary-searches, per hit of the cycle, the first repeat whose
  land has reached hp, comparing times exactly as `repeat` computes them.
  Exact over interleaving lands and float period boundaries; agrees with a
  brute-force unroll on 924 real (hero, ability, hp) cases.
- Hit guard: 10,000 hits (cycles started in the window x hits per cycle).
  Claim: `apps/vis/docs/dev/claims.kb/window-limits.md`.
- `cycles` on a one-shot gives its 10 s default and a note, not a 400, so
  switching from a gun shown in cycles to a one-shot doesn't break the page.
- `hp` that is never reached (no damage, or a one-shot that falls short)
  gets the note "never reached"; the old "not reached within N s" is gone.
- Client: no zoom on page load: a shared URL shows the window it names.
- Client: zoom is a `zoomPending` flag set by the hp/hero/ability/level
  handlers, cleared by a window edit, and consumed by the first answer to
  the current params. Knob and hp inputs need no draft: their state is the
  typed text. Window field labels: "window (s)", "cycles shown".
- `horizon-default.md` still holds (2 cycles), so it is restated, not
  superseded; `model.kb/horizon-counting.md` restated likewise (time to
  kill no longer counted by the horizon). `kill-horizon.md` superseded.

## Open Questions

- Zoom vs the hit guard: hp=1e9 zooms to a window the server refuses (400),
  and since zoom never zooms in, lowering hp keeps the error until the user
  edits the window. Should a zoom stop at the guard instead?
- Design doc still says "horizon" in *Model*; the protocol key stays
  `horizon` in the `cycle` line. Not edited (outside scope).

## Final report

- Checks: server `pytest` all pass; basedpyright `all` 0/0/0 (whole
  server); client `tsc --noEmit` clean, vitest 61 pass. Each new
  assertion seen red, by natural red or a mutant (an equivalent mutant of
  `_landed_by`'s estimate survives, as it should; the zero-damage guard's
  mutant hangs rather than fails).
- Proof (`trash/030/`, script `shots.mjs`, CDP 9230, Chrome and serve
  stopped, none left): `1-hp-kill-inside.png` (hp 200, window stays 2
  cycles, ttk 6.03); `2-hp-kill-outside.png` (hp 3000 zooms to 21 cycles =
  106.785 s, ttk 102.23); `3a-atlas-kill-inside.png` then
  `3b-haze-kill-pushed-out.png` (hero switch zooms to 4 cycles, ttk 15.03);
  `4-seconds-below-kill.png` (seconds 2 kept, cycles 0.393, ttk row 6.03,
  no kill mark).
- Deviations: `horizon-default.md` restated, not superseded (it still
  holds). `chart.ts` now hides the kill mark past the chart's end.
- Tools: `node_modules/.bin/{tsc,vitest}` (no pnpm); playwright-core from
  `trash/012/driver`.
