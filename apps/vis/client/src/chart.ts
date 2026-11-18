/**
 * The damage timeline: one bar per hit on the left axis, and the cumulative
 * damage as a step line on the right axis (docs/dev/decisions.kb/vis-app.md,
 * "Client view").
 */
import * as Plot from "@observablehq/plot";

import type { AbilityKind, HitLine } from "./protocol";

/** Bars: one hit's size. Line: damage so far. A Tableau 10 blue/orange pair. */
const BAR = "#4e79a7";
const LINE = "#f28e2b";

/**
 * Axis and label text colors, per color scheme: the bar and line colors, darkened
 * on a light page and lightened on a dark one until the 12 px text reads (both
 * are at least 4.5:1 against white and against #242424).
 */
export const TEXT = {
  light: { bar: "#2f5d8a", line: "#a85400" },
  dark: { bar: "#8fb4dc", line: "#f5a65b" },
} as const;

/** Chart text size in px: the page's 0.85rem labels are 13.6 px; Plot's own is 10. */
const FONT_PX = 12;

/**
 * Each hit as a bar from x1 = trigger to x2 = land, damage tall, plus a rule at
 * land so a hit with zero width stays visible and adjacent bars stay apart.
 *
 * Every hit has the same color: a label names one hit ("shot 12"), so coloring
 * by it gives a gun a color per bullet.
 */
export function hitMarks(hits: readonly HitLine[]): Plot.Markish[] {
  return [
    Plot.rect(hits, { x1: "trigger", x2: "land", y1: 0, y2: "damage", fill: BAR, fillOpacity: 0.45 }),
    Plot.ruleX(hits, { x: "land", y1: 0, y2: "damage", stroke: BAR, strokeWidth: 2 }),
  ];
}

/** A hit's tooltip: its label, then trigger, land, width and damage, one per line. */
export function hitTitle(hit: HitLine): string {
  return [
    hit.label,
    `trigger ${num(hit.trigger)} s`,
    `land ${num(hit.land)} s`,
    `width ${num(hit.land - hit.trigger)} s`,
    `damage ${num(hit.damage)}`,
  ].join("\n");
}

/** One point of the cumulative-damage step line. */
export interface Step {
  t: number;
  total: number;
}

/**
 * Damage dealt by each time: a point at 0, one at each distinct land, and one
 * at `end`, to draw with `curve: "step-after"`. Hits landing together make one
 * step; a hit at t=0 steps up at once.
 */
export function cumulative(hits: readonly HitLine[], end: number): Step[] {
  const steps: Step[] = [{ t: 0, total: 0 }];
  for (const h of [...hits].sort((a, b) => a.land - b.land)) {
    const last = steps[steps.length - 1]!;
    if (last.t === h.land) last.total += h.damage;
    else steps.push({ t: h.land, total: last.total + h.damage });
  }
  const last = steps[steps.length - 1]!;
  if (end > last.t) steps.push({ t: end, total: last.total });
  return steps;
}

/** Round ticks from 0 that cover `max`, 6 to 11 of them. */
export function niceTicks(max: number): number[] {
  if (!(max > 0)) return [0, 1];
  const raw = max / 10;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * mag).find((s) => s >= raw) ?? 10 * mag;
  const n = Math.ceil(max / step - 1e-9);
  return Array.from({ length: n + 1 }, (_, i) => Number((i * step).toPrecision(12)));
}

/** What a bar's width means, for each kind of source. */
export function widthCaption(kind: AbilityKind): string {
  const width = {
    gun: "bullet travel time to the target (distance ÷ bullet speed)",
    melee: "the assumed wind-up (the game data has none)",
    cast: "the cast delay before an impact; for a damage-over-time tick, the time since the previous tick",
  }[kind];
  return `Bar width: ${width}. Bar height: one hit's damage. The line is the damage dealt so far; its slope is the DPS.`;
}

/** From 0 to the horizon, or to the last land if a bar ends past it. */
export function xDomain(hits: readonly HitLine[], horizon: number): [number, number] {
  return [0, Math.max(horizon, ...hits.map((h) => h.land))];
}

/**
 * The whole chart, ready to mount. Both axes share the plot's one y scale: the
 * cumulative series is scaled into the bars' range, and the right axis labels
 * it back in damage dealt.
 */
export function hitChart(
  hits: readonly HitLine[],
  options: { width?: number; horizon?: number; hp?: number; kind?: AbilityKind; dark?: boolean } = {},
): ReturnType<typeof Plot.plot> {
  const { hp } = options;
  const text = TEXT[options.dark === true ? "dark" : "light"];
  const [, end] = xDomain(hits, options.horizon ?? 0);
  const steps = cumulative(hits, end);
  const barTicks = niceTicks(Math.max(0, ...hits.map((h) => h.damage)));
  const lineTicks = niceTicks(Math.max(steps[steps.length - 1]!.total, 1.1 * (hp ?? 0))); // headroom for the hp label
  const k = barTicks[barTicks.length - 1]! / lineTicks[lineTicks.length - 1]!;
  return Plot.plot({
    ...(options.width === undefined ? {} : { width: options.width }),
    ...(options.kind === undefined ? {} : { caption: widthCaption(options.kind) }),
    style: { fontSize: `${FONT_PX}px` },
    marginRight: 64,
    x: { label: "time (s)", domain: [0, end], insetLeft: 4 }, // the inset keeps a hit at t=0 off the frame
    y: { domain: [0, barTicks[barTicks.length - 1]!] },
    marks: [
      Plot.gridY(lineTicks.map((v) => v * k)),
      Plot.axisY(barTicks, { anchor: "left", label: "↑ damage per hit", color: text.bar }),
      Plot.axisY(
        lineTicks.map((v) => v * k),
        { anchor: "right", label: "cumulative damage ↑", color: text.line, tickFormat: (v: number) => num(v / k) },
      ),
      ...hitMarks(hits),
      Plot.line(steps, { x: "t", y: (s: Step) => s.total * k, curve: "step-after", stroke: LINE, strokeWidth: 2 }),
      ...(hp === undefined
        ? []
        : [
            Plot.ruleY([hp * k], { stroke: LINE, strokeDasharray: "4 3" }),
            Plot.text([hp * k], {
              y: (v: number) => v,
              frameAnchor: "right",
              textAnchor: "end",
              dx: -4,
              dy: -7,
              text: () => `target hp ${num(hp)}`,
              fill: text.line,
            }),
          ]),
      Plot.ruleY([0]),
      Plot.tip(hits, Plot.pointerX({ x1: "trigger", x2: "land", y: "damage", title: hitTitle })),
    ],
  });
}

/** A number for display: at most 3 decimals, no trailing zeros. */
function num(x: number): string {
  return String(Number(x.toFixed(3)));
}
