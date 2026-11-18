/**
 * The chart's window: how much time it shows, as one value in the unit the
 * user last typed it in (docs/dev/decisions.kb/vis-app.md, "Client view").
 */
import type { Params } from "./api";
import type { CycleLine } from "./protocol";

export type WindowUnit = "seconds" | "cycles";

/** The text typed, unparsed: the server answers 400 on a bad number. */
export interface Window {
  by: WindowUnit;
  value: string;
}

/** The window after typing `text` in the `by` field; a blank is the server's default (`null`). */
export function windowFromText(by: WindowUnit, text: string): Window | null {
  const value = text.trim();
  return value === "" ? null : { by, value };
}

/** The `timeline` params that ask for `window`. */
export function windowParams(window: Window | null): Params {
  return window === null ? {} : { [window.by]: window.value };
}

export interface WindowField {
  value: string;
  placeholder: string;
  disabled: boolean;
}

/**
 * What each window field shows when the user is not typing in it: the window
 * `cycle` (the latest answer's) resolved to, in seconds and in cycles. Before
 * any answer, only the field the window was typed in has a value.
 */
export function windowFields(window: Window | null, cycle: CycleLine | undefined): Record<WindowUnit, WindowField> {
  const field = (value: string, placeholder = "", disabled = false): WindowField => ({ value, placeholder, disabled });
  if (cycle === undefined) {
    const typed = (by: WindowUnit) => field(window?.by === by ? window.value : "", window === null ? "default" : "");
    return { seconds: typed("seconds"), cycles: typed("cycles") };
  }
  return {
    seconds: field(num(cycle.horizon)),
    cycles: cycle.period === null ? field("", "one-shot", true) : field(num(cycle.horizon / cycle.period)),
  };
}

/** The most whole cycles the server will show (its hit guard), or `null` when it states no limit. */
function maxCycles(cycle: CycleLine): number | null {
  return cycle.period === null || cycle.max_horizon == null ? null : Math.round(cycle.max_horizon / cycle.period);
}

/**
 * The window that shows the kill at `killTime`: `null` (keep the window) when
 * there is none, it lands inside `cycle.horizon`, or the largest window the
 * server allows is no bigger; else the fewest whole cycles whose half-open
 * window holds it (whole seconds for a one-shot), at most that largest
 * window. It only ever zooms out.
 */
export function zoomToKill(cycle: CycleLine, killTime: number | undefined): Window | null {
  if (killTime === undefined || killTime < cycle.horizon) return null;
  const unit = cycle.period ?? 1;
  let n = Math.floor(killTime / unit) + 1;
  while (n * unit <= killTime) n++; // float rounding: the server multiplies the same way
  const cap = maxCycles(cycle);
  if (cap !== null && n > cap) {
    if (cap * unit <= cycle.horizon) return null;
    n = cap;
  }
  return { by: cycle.period === null ? "seconds" : "cycles", value: String(n) };
}

/**
 * A note, in player words, when no window the server allows reaches the kill
 * at `killTime`; `null` otherwise. The time-to-kill row still gives the time.
 */
export function unreachableKillNote(cycle: CycleLine, killTime: number | undefined): string | null {
  const cap = maxCycles(cycle);
  if (killTime === undefined || cap === null || cycle.period === null || cycle.max_horizon == null) return null;
  if (killTime < cycle.max_horizon) return null;
  return `The chart can't reach the kill: it shows at most ${cap.toLocaleString("en-US")} cycles (${num(cycle.max_horizon)} s), and the time to kill is below.`;
}

/** A number for display: at most 3 decimals, no trailing zeros. */
function num(x: number): string {
  return String(Number(x.toFixed(3)));
}
