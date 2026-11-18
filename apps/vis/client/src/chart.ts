/**
 * The damage-over-time chart: one bar per hit (docs/dev/decisions.kb/vis-app.md,
 * "Client view").
 */
import * as Plot from "@observablehq/plot";

import type { HitLine } from "./protocol";

const COLOR = "steelblue";

/**
 * Each hit as a bar from x1 = trigger to x2 = land, damage tall, plus a rule at
 * land so a hit with no wind-up (zero width) stays visible. Hovering a rule
 * shows the hit's fields, `label` among them.
 *
 * Every hit has the same color: a label names one hit ("shot 12"), so coloring
 * by it gives a gun a color per bullet. The bars are faint, so where they
 * overlap they darken: damage-over-time ticks, which all trigger at the cast,
 * read as a staircase whose steps are the ticks' lands.
 */
export function hitMarks(hits: readonly HitLine[]): Plot.Markish[] {
  return [
    Plot.rect(hits, {
      x1: "trigger",
      x2: "land",
      y1: 0,
      y2: "damage",
      fill: COLOR,
      fillOpacity: 0.12,
    }),
    Plot.ruleX(hits, {
      x: "land",
      y1: 0,
      y2: "damage",
      stroke: COLOR,
      strokeWidth: 2,
      channels: { label: "label", trigger: "trigger", cycle: "cycle" },
      tip: true,
    }),
  ];
}

/** The whole chart, ready to mount. */
export function hitChart(
  hits: readonly HitLine[],
  options: { width?: number; horizon?: number } = {},
): ReturnType<typeof Plot.plot> {
  return Plot.plot({
    ...(options.width === undefined ? {} : { width: options.width }),
    x: {
      label: "time (s): bar spans trigger → land",
      insetLeft: 4, // keeps a hit at t=0 off the frame's edge
      ...(options.horizon === undefined ? {} : { domain: [0, options.horizon] }),
    },
    y: { label: "damage", grid: true, nice: true },
    marks: [...hitMarks(hits), Plot.ruleY([0])],
  });
}
