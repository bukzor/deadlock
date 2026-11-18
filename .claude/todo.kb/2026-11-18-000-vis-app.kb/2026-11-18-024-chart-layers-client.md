---
managed-by: Skill(llm-subtask)
status: done
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../docs/dev/decisions.kb/vis-app.md   # "Client view"
  - ./2026-11-18-020-ux-review-2.md   # Final report: findings 4 (the chart half), 5 (margin), 6 (`× period`), 7
  - ./2026-11-18-022-chart-readable-any-width.md   # the resize redraw this unit repairs
  - ../../../apps/vis/client/src/
---

# Client: no resize loop, separate layers, a time-to-kill mark, "cycles shown"

**Parent:** <https:../2026-11-18-000-vis-app.md> (review round 3)

## Problem Statement

- **Defect from 022:** the browser logs "ResizeObserver loop completed with
  undelivered notifications" over and over, once every second or two, in the user's
  running page. A redraw probably changes the page height, which toggles the
  scrollbar, which changes the width again. Find the real cause in the browser
  and fix it so a redraw cannot trigger another. For example, redraw only when
  the rounded width changes, from the next animation frame, and reserve the
  scrollbar gutter. Prove it: no such error while resizing in headless Chrome.
- **Layers** (finding 7): the bars use a y domain of about 2× the largest hit,
  so they keep to the lower half. The gridlines follow one axis only.
- **Time to kill** (finding 4, the chart half): where the cumulative line
  crosses `hp`, draw a vertical mark with a label (its time). The server
  computes `time_to_kill`; read it from the measure line.
- **Margin** (finding 5): `figure { margin: 0 }` if 022 left the browser's
  default.
- **Wording** (finding 6): the `× period` input is labelled "cycles shown".

Unit 023 is changing the server's measures and labels in parallel. Read
measures by `name`, never by position.

**Proof:** screenshots in `trash/024/`, at 460 and 1280 px, dark scheme, one
with an `hp` that is reached. Run your own `PORT=5194 API_PORT=8794
apps/vis/bin/serve`, and kill only the pids you started. A `pkill -f` pattern
kills the user's serve on 5173/8788.

**Scope:** `apps/vis/client/src/*`, `apps/vis/client/index.html`.

## Steps

- [x] Reproduce the loop in headless Chrome (`trash/024/loop.mjs`): 2 errors at load, 38 over 39 resize steps
- [x] `chart.ts`: bars in the lower half, kill-time rule and label (tests red first, then green)
- [x] `App.tsx`: draw on the next frame, only on a whole-pixel width change; `killTime` from the `time_to_kill` measure, read by name; "cycles shown"
- [x] `index.css`: `figure { margin: 0 }`, `scrollbar-gutter: stable`
- [x] Screenshots, after which the loop count was 0 at load and 0 over resizing

## Decisions

- **Cause of the loop.** `draw()` ran inside the ResizeObserver callback, and the new SVG changed the observed element's height. That is a new notification during delivery, so every redraw logged the error; it was not a true oscillation. The fix: the callback only schedules `requestAnimationFrame(draw)`, and only when `Math.round(contentRect.width)` changed. `scrollbar-gutter: stable` also keeps a scrollbar that comes and goes from changing the width.
- **Gridlines** stay on the right (cumulative) axis, the main read. The bars' ticks span the lower half only.
- **Kill mark:** a rule from 0 up to the crossing, a dot, and a bold label with the time. The label goes where the line is not: left of the rule and above hp when t is in the right half, else right of the rule and below hp. The "target hp" label moves to the opposite end, so the two never meet (checked at 460 px for both branches).

## Final report

- `tsc --noEmit` clean; vitest 54 passed (2 new tests, each observed red). `pnpm` is absent, so I used `apps/vis/client/node_modules/.bin/{tsc,vitest}`.
- Proof, in `trash/024/`, all dark: `gun-hp200-{460,1280}.png` (hp reached, label left of the rule), `gun-hp60-{460,1280}.png` (the other label branch), `cast-leech-hp100-{460,1280}.png`, and `gun-hp600-*` (not reached). Every page logged 0 errors. Drivers: `loop.mjs` and `shots.mjs`. I ran my own serve on 5194/8794 and Chrome on CDP 9224, and stopped them by pid and over CDP; the user's 8788 was untouched.
- Each save left the app compiling: `killTime` is optional, and every file went in as one write.
