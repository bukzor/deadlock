import { describe, expect, it } from "vitest";

import type { CycleLine } from "./protocol";
import { windowFields, windowFromText, windowParams, zoomToKill } from "./window";

function cycle(period: number | null, horizon: number): CycleLine {
  return { kind: "cycle", period, downtime: 0, horizon };
}

describe("windowFromText", () => {
  it("keeps the text, trimmed, in the unit typed", () => {
    expect(windowFromText("cycles", " 3 ")).toEqual({ by: "cycles", value: "3" });
    expect(windowFromText("seconds", "x")).toEqual({ by: "seconds", value: "x" });
  });

  it("is the server's default on a blank", () => {
    expect(windowFromText("seconds", "  ")).toBeNull();
  });
});

describe("windowParams", () => {
  it("sends the window under its unit's name", () => {
    expect(windowParams({ by: "cycles", value: "3" })).toEqual({ cycles: "3" });
    expect(windowParams({ by: "seconds", value: "12" })).toEqual({ seconds: "12" });
  });

  it("sends nothing for the default", () => {
    expect(windowParams(null)).toEqual({});
  });
});

describe("windowFields", () => {
  it("shows the resolved window in both units, whichever was typed", () => {
    const shown = { seconds: { value: "7.5", placeholder: "", disabled: false }, cycles: { value: "3", placeholder: "", disabled: false } };
    expect(windowFields(null, cycle(2.5, 7.5))).toEqual(shown);
    expect(windowFields({ by: "seconds", value: "7.5" }, cycle(2.5, 7.5))).toEqual(shown);
  });

  it("rounds a float product back to the whole cycles typed", () => {
    expect(windowFields({ by: "cycles", value: "3" }, cycle(5.085, 3 * 5.085)).cycles.value).toBe("3");
  });

  it("disables cycles for a one-shot", () => {
    expect(windowFields(null, cycle(null, 10)).cycles).toEqual({ value: "", placeholder: "one-shot", disabled: true });
  });

  it("shows the text typed, and no number it cannot know, before an answer", () => {
    expect(windowFields({ by: "cycles", value: "3" }, undefined)).toEqual({
      seconds: { value: "", placeholder: "", disabled: false },
      cycles: { value: "3", placeholder: "", disabled: false },
    });
    expect(windowFields(null, undefined).seconds).toEqual({ value: "", placeholder: "default", disabled: false });
  });
});

describe("zoomToKill", () => {
  it("keeps a window the kill lands inside", () => {
    expect(zoomToKill(cycle(2, 6), 5.9)).toBeNull();
  });

  it("keeps the window when there is no kill", () => {
    expect(zoomToKill(cycle(2, 6), undefined)).toBeNull();
  });

  it("zooms out to the fewest whole cycles that show the kill", () => {
    expect(zoomToKill(cycle(2, 6), 9.5)).toEqual({ by: "cycles", value: "5" });
  });

  it("zooms out past a kill on the window's edge, which is open", () => {
    expect(zoomToKill(cycle(2, 6), 6)).toEqual({ by: "cycles", value: "4" });
    expect(zoomToKill(cycle(0.7, 1.4), 3 * 0.7)).toEqual({ by: "cycles", value: "4" });
  });

  it("zooms a one-shot out by whole seconds", () => {
    expect(zoomToKill(cycle(null, 10), 12.4)).toEqual({ by: "seconds", value: "13" });
  });
});
