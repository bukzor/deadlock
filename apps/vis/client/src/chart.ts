/**
 * The damage-over-time chart: one bar per hit (docs/dev/decisions.kb/vis-app.md,
 * "Client view").
 */
import * as Plot from "@observablehq/plot";

import type { HitLine } from "./protocol";

const COLOR = "steelblue";

/**
 * Each hit as a bar from x1 = trigger to x2 = land, damage tall, plus a rule at
 * land so a hit with no wind-up (zero width) stays visible and adjacent bars
 * stay apart. Hovering a rule shows the hit's `hitTitle`.
 *
 * Every hit has the same color: a label names one hit ("shot 12"), so coloring
 * by it gives a gun a color per bullet.
 */
export function hitMarks(hits: readonly HitLine[]): Plot.Markish[] {
  return [
    Plot.rect(hits, {
      x1: "trigger",
      x2: "land",
      y1: 0,
      y2: "damage",
      fill: COLOR,
      fillOpacity: 0.45,
    }),
    Plot.ruleX(hits, {
      x: "land",
      y1: 0,
      y2: "damage",
      stroke: COLOR,
      strokeWidth: 2,
      title: hitTitle,
      tip: true,
    }),
  ];
}

/** A hit's tooltip: its label, then trigger, land, wind-up and damage, one per line. */
export function hitTitle(hit: HitLine): string {
  const num = (x: number): string => String(Number(x.toFixed(3)));
  return [
    hit.label,
    `trigger ${num(hit.trigger)} s`,
    `land ${num(hit.land)} s`,
    `wind-up ${num(hit.land - hit.trigger)} s`,
    `damage ${num(hit.damage)}`,
  ].join("\n");
}

/** From 0 to the horizon, or to the last land if a bar ends past it. */
export function xDomain(hits: readonly HitLine[], horizon: number): [number, number] {
  return [0, Math.max(horizon, ...hits.map((h) => h.land))];
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
      ...(options.horizon === undefined ? {} : { domain: xDomain(hits, options.horizon) }),
    },
    y: { label: "damage", grid: true, nice: true },
    marks: [...hitMarks(hits), Plot.ruleY([0])],
  });
}
