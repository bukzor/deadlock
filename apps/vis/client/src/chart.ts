/**
 * The damage-over-time chart: one bar per hit (docs/dev/decisions.kb/vis-app.md,
 * "Client view").
 */
import * as Plot from "@observablehq/plot";

import type { HitLine } from "./protocol";

/**
 * Each hit as a bar from x1 = trigger to x2 = land, damage tall, plus a rule at
 * land so a hit with no wind-up (zero width) stays visible. Hits are colored by
 * `label`; hovering a rule shows the hit's fields.
 */
export function hitMarks(hits: readonly HitLine[]): Plot.Markish[] {
  return [
    Plot.rect(hits, {
      x1: "trigger",
      x2: "land",
      y1: 0,
      y2: "damage",
      fill: "label",
      fillOpacity: 0.4,
    }),
    Plot.ruleX(hits, {
      x: "land",
      y1: 0,
      y2: "damage",
      stroke: "label",
      strokeWidth: 2,
      channels: { trigger: "trigger", cycle: "cycle" },
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
      ...(options.horizon === undefined ? {} : { domain: [0, options.horizon] }),
    },
    y: { label: "damage", grid: true },
    color: { legend: true },
    marks: [...hitMarks(hits), Plot.ruleY([0])],
  });
}
