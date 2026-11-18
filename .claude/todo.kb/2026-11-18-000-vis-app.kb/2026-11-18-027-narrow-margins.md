---
managed-by: Skill(llm-subtask)
status: open
blocked-by: []
required-reading:
  - ./CLAUDE.md
  - ../../../apps/vis/client/src/index.css
  - ../../../apps/vis/client/src/chart.ts
  - ../../../apps/vis/client/src/App.tsx
  - ../../../apps/vis/bin/serve
  - ../../../trash/024/gun-hp200-460.png   # the narrow layout today
---

# Client: margins that shrink on narrow screens; machine names on hover; `bin/serve` ≤50 lines

**Parent:** <https:../2026-11-18-000-vis-app.md> (review round 4: the user's manual review)

## Problem Statement

- The user: "left and right margin seems excessive, at narrow aspect ratio (on
  the graph mainly, on the text to a lesser extent)… can we do something like
  max(%,px)?" **Decided:** the page's side padding is `min(<px>, <vw>)`
  (equivalently `clamp`), so it caps on wide screens and shrinks on narrow
  ones. For the chart, Plot's margins should be as wide as the tick labels
  need, not fixed. Look for other inherited spacing too (body margin, figure
  padding). At 460 px wide, the plot area should take nearly the full width.
- The user, on ability names (unit 026 makes the server send display names):
  "Setting the machine-name as alt-text or data- or something might be a good
  idea?" **Decided:** each hero and ability `<option>` carries its machine key
  as `title`, so it shows on hover, and the URL keeps the key as now.
- `apps/vis/bin/serve` is 54 lines; the repo limit for bash is 50. Bring it
  under without losing behaviour.

**Proof:** screenshots in `trash/027/` at 460 and 1280 px, dark scheme. Run
your own `PORT=5197 API_PORT=8797 apps/vis/bin/serve` and kill only the pids
you started.

**Scope:** `apps/vis/client/src/*`, `apps/vis/client/index.html`,
`apps/vis/bin/serve`. Every save leaves the live app working.
