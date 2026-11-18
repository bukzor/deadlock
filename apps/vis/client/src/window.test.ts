import { describe, expect, it } from "vitest";

import type { CycleLine } from "./protocol";
import { unreachableKillNote, windowFields, windowFromText, windowParams, zoomToKill } from "./window";

function cycle(period: number | null, horizon: number, max_horizon: number | null = null): CycleLine {
  return { kind: "cycle", period, downtime: 0, horizon, max_horizon };
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

describe("zoomToKill under the server's largest window", () => {
  const capped = cycle(2, 6, 20); // at most 10 cycles

  it("zooms out as far as the kill when that fits", () => {
    expect(zoomToKill(capped, 15)).toEqual({ by: "cycles", value: "8" });
  });

  it("stops at the largest whole-cycle window when the kill is beyond it", () => {
    expect(zoomToKill(capped, 1e9)).toEqual({ by: "cycles", value: "10" });
    expect(zoomToKill(capped, 20)).toEqual({ by: "cycles", value: "10" });
  });

  it("keeps the window when it is already the largest", () => {
    expect(zoomToKill(cycle(2, 20, 20), 1e9)).toBeNull();
  });

  it("does not cap a one-shot", () => {
    expect(zoomToKill(cycle(null, 10), 1e9)).toEqual({ by: "seconds", value: "1000000001" });
  });
});

describe("unreachableKillNote", () => {
  const capped = cycle(2, 6, 20);

  it("says the chart can't reach a kill beyond the largest window", () => {
    expect(unreachableKillNote(capped, 25)).toMatch(/can't reach the kill.*10 cycles \(20 s\)/);
  });

  it("is silent when the largest window shows the kill, or there is no kill or no limit", () => {
    expect(unreachableKillNote(capped, 19.9)).toBeNull();
    expect(unreachableKillNote(capped, undefined)).toBeNull();
    expect(unreachableKillNote(cycle(null, 10), 1e9)).toBeNull();
  });
});
