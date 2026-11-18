/**
 * The damage timeline view: pick a hero, then an ability, then tune the params
 * that ability's kind reads; the chart, measures and notes follow. The
 * selection lives in the URL (docs/dev/decisions.kb/vis-app.md, "Client view").
 */
import { useEffect, useRef, useState } from "react";

import { abilities, heroes, timeline } from "./api";
import { hitChart } from "./chart";
import type { AbilityKind, CycleLine, HitLine, MeasureLine, NoteLine, TimelineLine } from "./protocol";
import {
  fromSearch,
  horizonInputs,
  knobsFor,
  timelineParams,
  toSearch,
  withHorizon,
  type Knob,
  type Selection,
} from "./selection";

/** Each knob's label, and its placeholder: the server's default, never a value. */
const KNOB_TEXT: Record<Knob, { label: string; placeholder: string }> = {
  distance: { label: "distance (m)", placeholder: "default 0" },
  spirit: { label: "spirit power", placeholder: "default 0" },
  windup: { label: "wind-up (s)", placeholder: "default 0" },
  hp: { label: "target hp", placeholder: "optional" },
};

export function App() {
  const [sel, setSel] = useState<Selection>(() => fromSearch(location.search));
  useEffect(() => {
    history.replaceState(null, "", toSearch(sel) || location.pathname);
  }, [sel]);
  // Each cycle's period, by the request minus its horizon: `periods` needs it.
  const [periods, setPeriods] = useState<Record<string, number | null>>({});

  const heroList = useLines(heroes, "heroes");
  const abilityList = useLines(sel.hero === "" ? null : () => abilities(sel.hero), sel.hero);
  // `undefined` until the abilities arrive: the knobs to send depend on it.
  const kind: AbilityKind | null | undefined = abilityList.loading
    ? undefined
    : abilityList.lines.find((a) => a.ability === sel.ability)?.kind;
  const base = kind === undefined ? "" : JSON.stringify(timelineParams(withHorizon(sel, "horizon", ""), kind, undefined));
  const params = kind === undefined ? null : timelineParams(sel, kind, periods[base]);
  const lines = useLines(
    params === null || sel.hero === "" || sel.ability === "" ? null : () => timeline(params),
    JSON.stringify(params),
  );
  const { cycle, hits, measures, notes } = splitTimeline(lines.lines);
  const current = cycle !== undefined && lines.key !== null && baseOf(lines.key) === base ? cycle : undefined;
  useEffect(() => {
    if (cycle !== undefined && lines.key !== null) setPeriods((m) => ({ ...m, [baseOf(lines.key!)]: cycle.period }));
  }, [cycle, lines.key]);
  const horizon = horizonInputs(sel, current);
  const hp = Number(params?.hp);

  return (
    <main>
      <h1>Damage timeline</h1>
      <form onSubmit={(e) => e.preventDefault()}>
        <label>
          hero
          <select value={sel.hero} onChange={(e) => setSel({ ...sel, hero: e.target.value, ability: "" })}>
            <option value="">pick a hero</option>
            {heroList.lines.map((h) => (
              <option key={h.hero} value={h.hero}>
                {h.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          ability
          <select value={sel.ability} onChange={(e) => setSel({ ...sel, ability: e.target.value })}>
            <option value="">pick an ability</option>
            {abilityList.lines.map((a) => (
              <option key={a.ability} value={a.ability} disabled={a.kind === null}>
                {a.name} {a.kind === null ? "(no damage model)" : `(${a.kind})`}
              </option>
            ))}
          </select>
        </label>
        {kind != null && (
          <>
            <label>
              horizon (s)
              <input
                inputMode="decimal"
                placeholder={horizon.seconds.placeholder}
                value={horizon.seconds.value}
                onChange={(e) => setSel(withHorizon(sel, "horizon", e.target.value))}
              />
            </label>
            <label>
              × period
              <input
                inputMode="decimal"
                placeholder={horizon.periods.placeholder}
                value={horizon.periods.value}
                disabled={horizon.periods.disabled}
                onChange={(e) => setSel(withHorizon(sel, "periods", e.target.value))}
              />
            </label>
            {knobsFor(kind).map((knob) => (
              <label key={knob}>
                {KNOB_TEXT[knob].label}
                <input
                  inputMode="decimal"
                  placeholder={KNOB_TEXT[knob].placeholder}
                  value={sel[knob] ?? ""}
                  onChange={(e) => {
                    const { [knob]: _, ...rest } = sel;
                    setSel(e.target.value.trim() === "" ? rest : { ...rest, [knob]: e.target.value });
                  }}
                />
              </label>
            ))}
          </>
        )}
      </form>

      {[heroList, abilityList, lines].map(
        (l, i) =>
          l.error !== null && (
            <p key={i} className="error">
              {l.error}
            </p>
          ),
      )}
      {lines.loading && <p>loading…</p>}
      {hits.length > 0 && kind != null && (
        <Chart hits={hits} kind={kind} horizon={cycle?.horizon ?? 10} {...(Number.isFinite(hp) ? { hp } : {})} />
      )}
      {hits.length === 0 && measures.length > 0 && (
        <p className="chart">No damage lands within the horizon: the notes say what the model leaves out.</p>
      )}
      {measures.length > 0 && <Measures measures={measures} />}
      {notes.length > 0 && (
        <ul>
          {notes.map((n, i) => (
            <li key={i}>{n.text}</li>
          ))}
        </ul>
      )}
    </main>
  );
}

/** A timeline request's key, minus its horizon: the key the period is known by. */
function baseOf(key: string): string {
  const { horizon: _, ...rest } = JSON.parse(key) as Record<string, unknown>;
  return JSON.stringify(rest);
}

function Chart(props: { hits: readonly HitLine[]; kind: AbilityKind; horizon: number; hp?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const { hits, kind, horizon, hp } = props;
  useEffect(() => {
    const el = ref.current;
    if (el === null) return;
    const width = el.clientWidth || 640;
    el.replaceChildren(hitChart(hits, { width, kind, horizon, ...(hp === undefined ? {} : { hp }) }));
  }, [hits, kind, horizon, hp]);
  return <div ref={ref} className="chart" />;
}

function Measures({ measures }: { measures: readonly MeasureLine[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>measure</th>
          <th>value</th>
          <th>unit</th>
          <th className="check">how to check in-game</th>
        </tr>
      </thead>
      <tbody>
        {measures.map((m) => (
          <tr key={m.name}>
            <td title={m.name}>{m.label ?? m.name}</td>
            <td className="value">{m.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
            <td>{m.unit}</td>
            <td className="check">{m.check}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function splitTimeline(lines: readonly TimelineLine[]) {
  let cycle: CycleLine | undefined;
  const hits: HitLine[] = [];
  const measures: MeasureLine[] = [];
  const notes: NoteLine[] = [];
  for (const line of lines) {
    if (line.kind === "cycle") cycle = line;
    else if (line.kind === "hit") hits.push(line);
    else if (line.kind === "measure") measures.push(line);
    else notes.push(line);
  }
  return { cycle, hits, measures, notes };
}

interface Loaded<T> {
  lines: readonly T[];
  error: string | null;
  loading: boolean;
  /** The key `lines` were loaded for; `null` when cleared. */
  key: string | null;
}

/**
 * Run `load` whenever `key` changes and collect its lines; `null` clears them.
 * An answer that arrives after `key` has moved on is dropped.
 */
function useLines<T>(load: (() => AsyncIterable<T>) | null, key: string): Loaded<T> {
  const [state, setState] = useState<Loaded<T>>({ lines: [], error: null, loading: false, key: null });
  useEffect(() => {
    if (load === null) {
      setState({ lines: [], error: null, loading: false, key: null });
      return;
    }
    let stale = false;
    setState((s) => ({ ...s, loading: true }));
    void (async () => {
      const lines: T[] = [];
      try {
        for await (const line of load()) lines.push(line);
        if (!stale) setState({ lines, error: null, loading: false, key });
      } catch (e) {
        if (!stale) setState({ lines: [], error: e instanceof Error ? e.message : String(e), loading: false, key });
      }
    })();
    return () => {
      stale = true;
    };
    // `key` stands for everything `load` closes over.
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  return state;
}
