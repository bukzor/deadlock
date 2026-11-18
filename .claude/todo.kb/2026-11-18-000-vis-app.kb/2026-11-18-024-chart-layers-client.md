---
managed-by: Skill(llm-subtask)
status: open
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
