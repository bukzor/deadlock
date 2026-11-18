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

/** The cycle behind the timeline: always the first line. */
export interface CycleLine {
  kind: "cycle";
  /** Seconds between repetitions; `null` for a one-shot. */
  period: number | null;
  /** Seconds of each period spent dealing no damage (reload, cooldown). */
  downtime: number;
  /** The window the server resolved, in seconds (its default when none was sent). */
  horizon: number;
}

/** A derived number, with how to verify it in-game. */
export interface MeasureLine {
  kind: "measure";
  /** A stable identifier, for `jq`. */
  name: string;
  /** The player-facing wording. Older servers omit it: fall back to `name`. */
  label?: string;
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
export type TimelineLine = CycleLine | HitLine | MeasureLine | NoteLine;

/** The single line of a 400 answer. */
export interface ErrorLine {
  error: string;
}

/** `timeline`'s parameters; the server applies the defaults shown. */
export interface TimelineParams {
  hero: string;
  ability: string;
  /** The window in seconds; give this or `cycles`. Default 2 cycles, or 10 s for a one-shot. */
  seconds?: number;
  /** The window in periods of the cycle; give this or `seconds`. A one-shot ignores it. */
  cycles?: number;
  /** Hero level, a whole number from 0 to the data's last: one boon per level. Default 0. */
  level?: number;
  /** Metres to the target, for bullet travel time. Default 0. */
  distance?: number;
  /** Spirit power on top of the level's, for spirit-scaled damage. Default 0. */
  spirit?: number;
  /** Seconds of assumed melee wind-up. Default 0. */
  windup?: number;
  /** Target health, for `time_to_kill`, wherever the kill falls. Never changes the window. */
  hp?: number;
}
