/**
 * The view's selection: what the user picked and typed, kept in the URL so a
 * page can be reloaded or shared (docs/dev/decisions.kb/vis-app.md, "Client
 * view"). Values stay as typed; the server parses them and answers 400.
 */
import type { Params } from "./api";
import type { AbilityKind } from "./protocol";
import { windowParams, type Window, type WindowUnit } from "./window";

/** A parameter that only some kinds of ability use. */
export type Knob = "level" | "distance" | "spirit" | "windup";

/** Text as typed, `undefined` or blank meaning "server default". */
export interface Selection {
  hero: string;
  ability: string;
  level?: string;
  distance?: string;
  spirit?: string;
  windup?: string;
}

/** Everything the URL holds. The window and the target's `hp` (`""` for none) are values of their own. */
export interface Page {
  sel: Selection;
  window: Window | null;
  hp: string;
}

type Key = keyof Selection | WindowUnit | "hp";
const KEYS: readonly Key[] = ["hero", "ability", "level", "seconds", "cycles", "distance", "spirit", "windup", "hp"];
const UNITS: readonly WindowUnit[] = ["seconds", "cycles"];

/** Parse `location.search`; unknown keys are ignored, and `seconds` wins over `cycles`. */
export function fromSearch(search: string): Page {
  const query = new URLSearchParams(search);
  const sel: Selection = { hero: query.get("hero") ?? "", ability: query.get("ability") ?? "" };
  for (const knob of ["level", "distance", "spirit", "windup"] as const) {
    const value = query.get(knob);
    if (value !== null) sel[knob] = value;
  }
  const by = UNITS.find((unit) => query.get(unit) !== null);
  return { sel, window: by === undefined ? null : { by, value: query.get(by)! }, hp: query.get("hp") ?? "" };
}

/** `?k=v&…` in a fixed key order, blanks left out; `""` when nothing is set. */
export function toSearch(page: Page): string {
  const values: Partial<Record<Key, string | undefined>> = { ...page.sel, ...windowParams(page.window), hp: page.hp };
  const query = new URLSearchParams();
  for (const key of KEYS) {
    const value = values[key]?.trim();
    if (value) query.append(key, value);
  }
  return query.size === 0 ? "" : `?${query}`;
}

/** The knobs each kind of ability reads; the window and `hp` apply to every kind. */
const KNOBS: Record<AbilityKind, readonly Knob[]> = {
  gun: ["level", "distance"],
  melee: ["level", "windup"],
  cast: ["level", "spirit"],
};

export function knobsFor(kind: AbilityKind | null): readonly Knob[] {
  return kind === null ? [] : KNOBS[kind];
}

/** The `timeline` request: only the knobs `kind` reads, then the window and `hp` as typed. */
export function timelineParams(page: Page, kind: AbilityKind | null): Params {
  const params: Params = { hero: page.sel.hero, ability: page.sel.ability };
  for (const knob of knobsFor(kind)) {
    const value = page.sel[knob]?.trim();
    if (value) params[knob] = value;
  }
  const hp = page.hp.trim();
  return { ...params, ...windowParams(page.window), ...(hp ? { hp } : {}) };
}
