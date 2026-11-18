/**
 * The JSONL lines the server answers, one type per line shape.
 *
 * Mirrors the "Protocol" section of docs/dev/decisions.kb/vis-app.md; change
 * both together. Times are seconds, distances metres.
 */

/** `GET /api`: one line per query the server offers. */
export interface QueryLine {
  query: string;
  /** Parameter name to a description of it. */
  params: Record<string, string>;
}

/** `GET /api/heroes`. */
export interface HeroLine {
  hero: string;
  name: string;
}

export type AbilityKind = "gun" | "melee" | "cast";

/** `GET /api/abilities?hero=…`. Melee appears as `melee_light`/`melee_heavy`. */
export interface AbilityLine {
  ability: string;
  name: string;
  /** `null` when no damage model covers the ability. */
  kind: AbilityKind | null;
}

/** One damage instance: input at `trigger`, damage applied at `land`. */
export interface HitLine {
  kind: "hit";
  trigger: number;
  land: number;
  damage: number;
  label: string;
  /** Which repetition of the ability's cycle this hit belongs to, from 0. */
  cycle: number;
}

/** A derived number, with how to verify it in-game. */
export interface MeasureLine {
  kind: "measure";
  name: string;
  value: number;
  unit: string;
  check: string;
}

/** A caveat on the model behind the timeline. */
export interface NoteLine {
  kind: "note";
  text: string;
}

/** `GET /api/timeline?…`: lines are tagged by `kind`. */
export type TimelineLine = HitLine | MeasureLine | NoteLine;

/** The single line of a 400 answer. */
export interface ErrorLine {
  error: string;
}

/** `timeline`'s parameters; the server applies the defaults shown. */
export interface TimelineParams {
  hero: string;
  ability: string;
  /** Seconds to unroll the cycle over. Default 10. */
  horizon?: number;
  /** Metres to the target, for bullet travel time. Default 0. */
  distance?: number;
  /** Spirit power, for spirit-scaled damage. Default 0. */
  spirit?: number;
  /** Seconds of assumed melee wind-up. Default 0. */
  windup?: number;
  /** Target health, for `time_to_kill`. */
  hp?: number;
}
