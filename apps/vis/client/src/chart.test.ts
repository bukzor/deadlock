// @vitest-environment jsdom
import * as Plot from "@observablehq/plot";
import { describe, expect, it } from "vitest";

import { TEXT, axisMargin, cumulative, hitChart, hitMarks, hitTitle, niceTicks, widthCaption, xDomain } from "./chart";
import type { HitLine } from "./protocol";

function hit(trigger: number, land: number, damage: number, label = "bullet"): HitLine {
  return { kind: "hit", trigger, land, damage, label, cycle: 0 };
}

/** Render with 100 px per second and 2 px per damage, y up from 200. */
function render(hits: HitLine[]): Element {
  return Plot.plot({
    marks: hitMarks(hits),
    x: { domain: [0, 10] },
    y: { domain: [0, 100] },
    width: 1000,
    height: 200,
    margin: 0,
  });
}

function colors(svg: Element, selector: string, name: string): Set<string | null> {
  return new Set([...svg.querySelectorAll(selector)].map((el) => el.getAttribute(name)));
}

function attrs(svg: Element, selector: string, names: string[]): number[][] {
  return [...svg.querySelectorAll(selector)].map((el) =>
    names.map((name) => Number(el.getAttribute(name))),
  );
}

describe("hitMarks", () => {
  it("draws a bar from trigger to land, as tall as the damage", () => {
    const svg = render([hit(1, 1.5, 50), hit(4, 6, 100)]);
    expect(attrs(svg, `[aria-label="rect"] rect`, ["x", "width", "y", "height"])).toEqual([
      [100, 50, 100, 100],
      [400, 200, 0, 200],
    ]);
  });

  it("draws a rule at each land, from zero up to the damage", () => {
    const svg = render([hit(1, 1.5, 50), hit(3, 3, 100)]);
    expect(attrs(svg, `[aria-label="rule"] line`, ["x1", "x2", "y1", "y2"])).toEqual([
      [150, 150, 200, 100],
      [300, 300, 200, 0],
    ]);
  });

  it("draws every hit in one color, however many labels there are", () => {
    const svg = render([hit(0, 1, 50, "shot 1"), hit(0, 2, 50, "shot 2"), hit(0, 3, 50, "DPS tick 1")]);
    expect(colors(svg, `[aria-label="rect"] rect`, "fill")).toHaveLength(1);
    expect(colors(svg, `[aria-label="rule"] line`, "stroke")).toHaveLength(1);
  });

  it("fills each bar enough to read on its own", () => {
    const svg = render([hit(0, 1, 50)]);
    const opacity = svg.querySelector(`[aria-label="rect"]`)?.getAttribute("fill-opacity");
    expect(Number(opacity ?? 1)).toBeGreaterThanOrEqual(0.4);
  });
});

describe("hitTitle", () => {
  it("names the hit, its times, its width and its damage, one per line", () => {
    expect(hitTitle(hit(0.48, 0.86, 8.74, "DPS tick 2"))).toBe(
      "DPS tick 2\ntrigger 0.48 s\nland 0.86 s\nwidth 0.38 s\ndamage 8.74",
    );
  });
});

describe("xDomain", () => {
  it("spans the horizon when every bar ends inside it", () => {
    expect(xDomain([hit(0, 1, 5)], 10)).toEqual([0, 10]);
  });

  it("stretches to the last land when a bar ends past the horizon", () => {
    expect(xDomain([hit(30, 30.48, 5), hit(30.48, 35.04, 5)], 30)).toEqual([0, 35.04]);
  });
});

describe("cumulative", () => {
  it("starts at zero and steps up by each hit's damage at its land", () => {
    expect(cumulative([hit(0, 1, 5), hit(1, 2, 7)], 3)).toEqual([
      { t: 0, total: 0 },
      { t: 1, total: 5 },
      { t: 2, total: 12 },
      { t: 3, total: 12 },
    ]);
  });

  it("orders by land, whatever order the hits come in", () => {
    expect(cumulative([hit(0, 2, 7), hit(0, 1, 5)], 3).map((p) => p.total)).toEqual([0, 5, 12, 12]);
  });

  it("makes one step of the hits that land together", () => {
    expect(cumulative([hit(0, 1, 5), hit(0, 1, 5)], 1)).toEqual([
      { t: 0, total: 0 },
      { t: 1, total: 10 },
    ]);
  });

  it("has a hit at t=0 step up at once", () => {
    expect(cumulative([hit(0, 0, 5)], 1)).toEqual([
      { t: 0, total: 5 },
      { t: 1, total: 5 },
    ]);
  });
});

describe("niceTicks", () => {
  it("covers the max with round steps", () => {
    expect(niceTicks(297)).toEqual([0, 50, 100, 150, 200, 250, 300]);
  });

  it("gives a zero max one tick", () => {
    expect(niceTicks(0)).toEqual([0, 1]);
  });
});

describe("widthCaption", () => {
  it("says what a bar's width means for each kind", () => {
    expect(widthCaption("gun")).toMatch(/bullet travel/);
    expect(widthCaption("melee")).toMatch(/assumed wind-up/);
    expect(widthCaption("cast")).toMatch(/since the previous tick/);
  });
});

describe("hitChart", () => {
  const hits = [hit(0, 1, 50), hit(1, 2, 100)];
  const labels = (svg: Element) => [...svg.querySelectorAll("text")].map((t) => t.textContent);

  it("labels the left axis per hit and the right axis cumulative", () => {
    const labelled = labels(hitChart(hits, { horizon: 3 }));
    expect(labelled.some((t) => t?.includes("damage per hit"))).toBe(true);
    expect(labelled.some((t) => t?.includes("cumulative damage"))).toBe(true);
  });

  it("draws the cumulative step line", () => {
    const svg = hitChart(hits, { horizon: 3 });
    expect(svg.querySelectorAll(`[aria-label="line"] path`)).toHaveLength(1);
  });

  it("draws a dashed hp rule only when hp is set", () => {
    const dashed = (svg: Element) => svg.querySelectorAll(`[aria-label="rule"][stroke-dasharray]`).length;
    expect(dashed(hitChart(hits, { horizon: 3 }))).toBe(0);
    expect(dashed(hitChart(hits, { horizon: 3, hp: 120 }))).toBe(1);
  });

  it("keeps the bars to the lower half, so the line reads as its own layer", () => {
    const svg = hitChart(hits, { horizon: 3 }) as unknown as Element & { scale(n: "y"): Plot.Scale };
    const y = svg.scale("y");
    const [bottom, top] = y.range as [number, number];
    expect(y.apply(100)).toBeCloseTo((bottom + top) / 2);
  });

  it("marks where the line reaches hp with a rule and its time", () => {
    const texts = (svg: Element) => labels(svg).filter((t) => t === "1 s");
    const rules = (svg: Element) => svg.querySelectorAll(`[aria-label="rule"] line`).length;
    expect(texts(hitChart(hits, { horizon: 3, hp: 40 }))).toEqual([]);
    expect(texts(hitChart(hits, { horizon: 3, hp: 40, killTime: 1 }))).toEqual(["1 s"]);
    expect(rules(hitChart(hits, { horizon: 3, hp: 40, killTime: 1 }))).toBe(rules(hitChart(hits, { horizon: 3, hp: 40 })) + 1);
  });

  it("follows the pointer with a tip", () => {
    expect(hitChart(hits, { horizon: 3 }).querySelector(`[aria-label="tip"]`)).not.toBeNull();
  });
});

describe("hitChart text", () => {
  const hits = [hit(0, 1, 50), hit(1, 2, 100)];

  it("is 12 px, not Plot's 10", () => {
    expect(hitChart(hits, { horizon: 3 }).style.fontSize).toBe("12px");
  });

  it("colors the axis labels per color scheme", () => {
    const fills = (dark: boolean) =>
      new Set([...hitChart(hits, { horizon: 3, dark }).querySelectorAll("[fill]")].map((t) => t.getAttribute("fill")));
    expect(fills(true).has(TEXT.dark.bar)).toBe(true);
    expect(fills(false).has(TEXT.light.bar)).toBe(true);
    expect(fills(false).has(TEXT.dark.bar)).toBe(false);
  });
});

describe("axisMargin", () => {
  it("fits the widest label, so narrow labels leave more plot", () => {
    expect(axisMargin(["0", "5"])).toBeLessThan(axisMargin(["0", "250", "300"]));
    expect(axisMargin(["0", "250", "300"])).toBe(Math.ceil(9 + 0.62 * 12 * 3));
  });
});
