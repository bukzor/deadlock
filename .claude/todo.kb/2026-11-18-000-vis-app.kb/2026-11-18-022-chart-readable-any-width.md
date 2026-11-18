---
managed-by: Skill(llm-subtask)
status: done
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../docs/dev/decisions.kb/vis-app.md   # "Client view"
  - ../../../apps/vis/client/src/chart.ts
  - ../../../apps/vis/client/src/App.tsx
  - ../../../apps/vis/client/src/index.css
  - ../../../trash/ux/user-narrow-chart.png   # the user's: drawn wide, then the window narrowed
  - ../../../trash/ux/user-narrow-chart-rerendered.png   # the user's: redrawn narrow; "still want it slightly more readable. The strokes on the font seems smaller than a pixel."
---

# The chart stays readable at any width, in the user's dark theme

**Parent:** <https:../2026-11-18-000-vis-app.md> (review round 2)

## Problem Statement

The user's words: "at narrow aspect ratio, nearly all the ui scales well
enough, but the graph scales poorly". `App.tsx` draws the chart once, at the
container's width at fetch time. After a resize, the browser scales the SVG,
text and all. When a later fetch redrew the chart at the narrow width, it
"improved it notably", but: "I'd still want it slightly more readable. The
strokes on the font seems smaller than a pixel."

**Decided:**

- Redraw the chart whenever its container's width changes. Use a
  `ResizeObserver`, not a window listener, and redraw from the data already
  fetched, never by refetching.
- Chart text (ticks, axis labels, the `target hp` label) is at least the
  page's body size less a step (about 12 px), not Plot's default 10 px. Its
  colour has enough contrast on the dark background the user's browser shows
  (`prefers-color-scheme: dark`), and in light mode too.
- At a narrow width, fewer ticks rather than crowded ones. Plot's defaults
  probably already do this once the chart is drawn at its true width; check.

**Proof:** in headless Windows Chrome (see `trash/017/driver/drive.mjs`), take
screenshots at about 460 and 1280 px wide, in dark and in light colour
schemes. Also take one after resizing from 1280 to 460 without reloading.
Save them in `trash/022/`. Run your own `PORT=5192 API_PORT=8792
apps/vis/bin/serve`. When you stop it, kill only the pids you started: a
`pkill -f` pattern also kills the user's serve on 5173/8788.

**Scope:** `apps/vis/client/src/{chart,App}.tsx?`, `index.css`, and their tests.

## Steps

- [x] ResizeObserver redraw in `App.tsx` `Chart` (from fetched hits, no refetch; also redraws on colour-scheme change)
- [x] `chart.ts`: 12 px text, per-scheme label colours (`TEXT`), `dark` option
- [x] Tests (`chart.test.ts`) and screenshots

## Decisions

- Label colours are passed by JS (`matchMedia` at draw time) because Plot writes colours as SVG attributes, where CSS variables do not apply. Bars and line keep their Tableau colours; only text colours change per scheme.
- Plot's default tick thinning already gives sensible ticks at the true width; no change.

## Final report

- `tsc --noEmit` and vitest (52) clean. `pnpm` absent; used `node_modules/.bin/{tsc,vitest}`.
- Proof in `trash/022/`: `{dark,light}-{460,1280}.png` and `dark-1280-to-460.png` (svg width 381 = container after resize, no reload). Driver `drive.mjs`, runner `run.sh`; own serve on 5192/8792 and Chrome stopped by pid, user's 5173/8788 untouched.
- Doubt: 12 px is Plot's `fontSize` on the svg; the user's "strokes under a pixel" is a rendering-weight impression, judged by screenshot only.
