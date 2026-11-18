// @vitest-environment jsdom
import * as Plot from "@observablehq/plot";
import { describe, expect, it } from "vitest";

import { hitMarks } from "./chart";
import type { HitLine } from "./protocol";

function hit(trigger: number, land: number, damage: number): HitLine {
  return { kind: "hit", trigger, land, damage, label: "bullet", cycle: 0 };
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
});
