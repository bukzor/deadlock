/**
 * The view's selection: what the user picked and typed, kept in the URL so a
 * page can be reloaded or shared (docs/dev/decisions.kb/vis-app.md, "Client
 * view"). Values stay as typed; the server parses them and answers 400.
 */
import type { Params } from "./api";
import type { AbilityKind, CycleLine } from "./protocol";

/** A parameter that only some kinds of ability use. */
export type Knob = "level" | "distance" | "spirit" | "windup" | "hp";

/**
 * Text as typed, `undefined` or blank meaning "server default". At most one
 * of `horizon` (seconds) and `periods` (multiples of the cycle's period) is
 * set: whichever the user edited last.
 */
export interface Selection {
  hero: string;
  ability: string;
  horizon?: string;
  periods?: string;
  level?: string;
  distance?: string;
  spirit?: string;
  windup?: string;
  hp?: string;
}

type Key = keyof Selection;
const KEYS: readonly Key[] = ["hero", "ability", "level", "horizon", "periods", "distance", "spirit", "windup", "hp"];

/** Parse `location.search`; unknown keys are ignored. */
export function fromSearch(search: string): Selection {
  const query = new URLSearchParams(search);
  const sel: Selection = { hero: query.get("hero") ?? "", ability: query.get("ability") ?? "" };
  for (const key of KEYS) {
    const value = query.get(key);
    if (value !== null) sel[key] = value;
  }
  return sel;
}

/** `?k=v&…` in a fixed key order, blanks left out; `""` when nothing is set. */
export function toSearch(sel: Selection): string {
  const query = new URLSearchParams();
  for (const key of KEYS) {
    const value = sel[key]?.trim();
    if (value) query.append(key, value);
  }
  return query.size === 0 ? "" : `?${query}`;
}

/** The knobs each kind of ability reads; `horizon` applies to every kind. */
const KNOBS: Record<AbilityKind, readonly Knob[]> = {
  gun: ["level", "distance", "hp"],
  melee: ["level", "windup", "hp"],
  cast: ["level", "spirit", "hp"],
};

export function knobsFor(kind: AbilityKind | null): readonly Knob[] {
  return kind === null ? [] : KNOBS[kind];
}

/**
 * The `timeline` request: only the knobs `kind` reads, and `periods` turned
 * into seconds by `period`. While the period is unknown (`undefined`, no
 * answer yet for these knobs) or absent (`null`, a one-shot), the horizon is
 * left to the server.
 */
export function timelineParams(sel: Selection, kind: AbilityKind | null, period: number | null | undefined): Params {
  const params: Params = { hero: sel.hero, ability: sel.ability };
  for (const knob of knobsFor(kind)) {
    const value = sel[knob]?.trim();
    if (value) params[knob] = value;
  }
  const horizon = sel.horizon?.trim();
  const periods = sel.periods?.trim();
  if (horizon) params.horizon = horizon;
  else if (periods && typeof period === "number") {
    const n = Number(periods);
    params.horizon = Number.isFinite(n) ? num(n * period) : periods;
  }
  return params;
}

/** The selection after typing `text` into one horizon input: the other is cleared. */
export function withHorizon(sel: Selection, by: "horizon" | "periods", text: string): Selection {
  const { horizon: _h, periods: _p, ...rest } = sel;
  return text.trim() === "" ? rest : { ...rest, [by]: text };
}

interface Input {
  value: string;
  placeholder: string;
}

/**
 * The two horizon inputs. The one the user typed in shows their text; the
 * other shows its equivalent through `cycle`'s period. With neither typed in,
 * both show the server's default as a placeholder. `cycle` is the latest
 * answer's cycle line, if any.
 */
export function horizonInputs(
  sel: Selection,
  cycle: CycleLine | undefined,
): { seconds: Input; periods: Input & { disabled: boolean } } {
  const period = cycle?.period ?? null;
  const convert = (text: string | undefined, f: (x: number, p: number) => number): string => {
    const x = Number(text);
    return text && period !== null && Number.isFinite(x) ? num(f(x, period)) : "";
  };
  return {
    seconds: {
      value: sel.horizon ?? convert(sel.periods, (n, p) => n * p),
      placeholder: cycle === undefined ? "default" : `default ${num(cycle.horizon)}`,
    },
    periods:
      cycle !== undefined && period === null
        ? { value: "", placeholder: "one-shot", disabled: true }
        : {
            value: sel.periods ?? convert(sel.horizon, (s, p) => s / p),
            placeholder: "default 2",
            disabled: cycle === undefined,
          },
  };
}

/** A number for display: at most 3 decimals, no trailing zeros. */
function num(x: number): string {
  return String(Number(x.toFixed(3)));
}
