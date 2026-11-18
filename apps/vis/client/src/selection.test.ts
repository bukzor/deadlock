import { describe, expect, it } from "vitest";

import { fromSearch, knobsFor, timelineParams, toSearch, type Page, type Selection } from "./selection";

const base: Selection = { hero: "hero_inferno", ability: "citadel_weapon_inferno_set" };
const page = (over: Partial<Page> = {}): Page => ({ sel: base, window: null, hp: "", ...over });

describe("toSearch / fromSearch", () => {
  it("round-trips a full page", () => {
    const full = page({ sel: { ...base, level: "10", distance: "30" }, window: { by: "cycles", value: "3" }, hp: "500" });
    expect(fromSearch(toSearch(full))).toEqual(full);
  });

  it("writes keys in a fixed order and leaves out blanks", () => {
    const sel = { hero: "h b", ability: "a", level: "3", windup: "" };
    expect(toSearch({ sel, window: { by: "seconds", value: "12" }, hp: "500" })).toBe("?hero=h+b&ability=a&level=3&seconds=12&hp=500");
  });

  it("is empty for an empty page", () => {
    expect(toSearch({ sel: { hero: "", ability: "" }, window: null, hp: "" })).toBe("");
  });

  it("ignores keys it does not know", () => {
    expect(fromSearch("?hero=h&junk=1&horizon=5")).toEqual({ sel: { hero: "h", ability: "" }, window: null, hp: "" });
  });

  it("reads the window in either unit, seconds first", () => {
    expect(fromSearch("?cycles=4").window).toEqual({ by: "cycles", value: "4" });
    expect(fromSearch("?cycles=4&seconds=9").window).toEqual({ by: "seconds", value: "9" });
  });
});

describe("knobsFor", () => {
  it("gives a gun level and distance", () => {
    expect(knobsFor("gun")).toEqual(["level", "distance"]);
  });

  it("gives melee level and wind-up", () => {
    expect(knobsFor("melee")).toEqual(["level", "windup"]);
  });

  it("gives a cast level and spirit", () => {
    expect(knobsFor("cast")).toEqual(["level", "spirit"]);
  });

  it("gives an unmodeled ability nothing", () => {
    expect(knobsFor(null)).toEqual([]);
  });
});

describe("timelineParams", () => {
  it("sends only the knobs that apply to the kind", () => {
    const sel: Selection = { ...base, level: "5", distance: "30", spirit: "100", windup: "0.4" };
    expect(timelineParams(page({ sel }), "gun")).toEqual({ ...base, level: "5", distance: "30" });
  });

  it("sends the window in its unit, as typed", () => {
    expect(timelineParams(page({ window: { by: "cycles", value: "3" } }), "gun")).toEqual({ ...base, cycles: "3" });
    expect(timelineParams(page({ window: { by: "seconds", value: "x" } }), "gun")).toEqual({ ...base, seconds: "x" });
  });

  it("sends hp for every kind, and leaves a blank out", () => {
    expect(timelineParams(page({ hp: " 500 " }), "cast")).toEqual({ ...base, hp: "500" });
    expect(timelineParams(page({ hp: " " }), "cast")).toEqual(base);
  });
});
