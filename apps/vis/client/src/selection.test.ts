import { describe, expect, it } from "vitest";

import type { CycleLine } from "./protocol";
import {
  fromSearch,
  horizonInputs,
  knobsFor,
  timelineParams,
  toSearch,
  withHorizon,
  type Selection,
} from "./selection";

function cycle(period: number | null, horizon: number): CycleLine {
  return { kind: "cycle", period, downtime: 0, horizon };
}

const base: Selection = { hero: "hero_inferno", ability: "citadel_weapon_inferno_set" };

describe("toSearch / fromSearch", () => {
  it("round-trips a full selection", () => {
    const sel: Selection = { ...base, level: "10", periods: "3", distance: "30", hp: "500" };
    expect(fromSearch(toSearch(sel))).toEqual(sel);
  });

  it("writes keys in a fixed order and leaves out blanks", () => {
    expect(toSearch({ hp: "500", level: "3", ability: "a", hero: "h b", horizon: "" })).toBe("?hero=h+b&ability=a&level=3&hp=500");
  });

  it("is empty for an empty selection", () => {
    expect(toSearch({ hero: "", ability: "" })).toBe("");
  });

  it("ignores keys it does not know", () => {
    expect(fromSearch("?hero=h&junk=1")).toEqual({ hero: "h", ability: "" });
  });
});

describe("knobsFor", () => {
  it("gives a gun level, distance and hp", () => {
    expect(knobsFor("gun")).toEqual(["level", "distance", "hp"]);
  });

  it("gives melee level, wind-up and hp", () => {
    expect(knobsFor("melee")).toEqual(["level", "windup", "hp"]);
  });

  it("gives a cast level, spirit and hp", () => {
    expect(knobsFor("cast")).toEqual(["level", "spirit", "hp"]);
  });

  it("gives an unmodeled ability nothing", () => {
    expect(knobsFor(null)).toEqual([]);
  });
});

describe("timelineParams", () => {
  it("sends only the knobs that apply to the kind", () => {
    const sel: Selection = { ...base, level: "5", distance: "30", spirit: "100", windup: "0.4", hp: "500" };
    expect(timelineParams(sel, "gun", undefined)).toEqual({ ...base, level: "5", distance: "30", hp: "500" });
  });

  it("sends the seconds as typed", () => {
    expect(timelineParams({ ...base, horizon: "12" }, "gun", 4)).toEqual({ ...base, horizon: "12" });
  });

  it("turns periods into seconds once the period is known", () => {
    expect(timelineParams({ ...base, periods: "3" }, "gun", 2.5)).toEqual({ ...base, horizon: "7.5" });
  });

  it("leaves the horizon to the server while the period is unknown or absent", () => {
    expect(timelineParams({ ...base, periods: "3" }, "gun", undefined)).toEqual(base);
    expect(timelineParams({ ...base, periods: "3" }, "cast", null)).toEqual(base);
  });

  it("passes unparseable periods through, so the server says what is wrong", () => {
    expect(timelineParams({ ...base, periods: "x" }, "gun", 2)).toEqual({ ...base, horizon: "x" });
  });
});

describe("withHorizon", () => {
  it("keeps only the input last edited", () => {
    const sel = withHorizon({ ...base, horizon: "12" }, "periods", "3");
    expect(sel).toEqual({ ...base, periods: "3" });
    expect(withHorizon(sel, "horizon", "9")).toEqual({ ...base, horizon: "9" });
  });

  it("clears both on a blank", () => {
    expect(withHorizon({ ...base, periods: "3" }, "periods", " ")).toEqual(base);
  });
});

describe("horizonInputs", () => {
  it("shows the server's defaults as placeholders, never as values", () => {
    expect(horizonInputs(base, cycle(3.3, 6.6))).toEqual({
      seconds: { value: "", placeholder: "default 6.6" },
      periods: { value: "", placeholder: "default 2", disabled: false },
    });
  });

  it("derives periods from typed seconds", () => {
    expect(horizonInputs({ ...base, horizon: "10" }, cycle(4, 10)).periods.value).toBe("2.5");
  });

  it("derives seconds from typed periods", () => {
    expect(horizonInputs({ ...base, periods: "3" }, cycle(1.5, 4.5)).seconds.value).toBe("4.5");
  });

  it("disables periods for a one-shot", () => {
    expect(horizonInputs({ ...base, horizon: "10" }, cycle(null, 10)).periods).toEqual({
      value: "",
      placeholder: "one-shot",
      disabled: true,
    });
  });

  it("has no numbers before the first answer", () => {
    expect(horizonInputs(base, undefined)).toEqual({
      seconds: { value: "", placeholder: "default" },
      periods: { value: "", placeholder: "default 2", disabled: true },
    });
  });
});
