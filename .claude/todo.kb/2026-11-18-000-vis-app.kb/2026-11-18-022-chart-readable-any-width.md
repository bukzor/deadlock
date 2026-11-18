---
managed-by: Skill(llm-subtask)
status: open
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
