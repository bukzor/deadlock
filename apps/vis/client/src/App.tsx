/**
 * The damage-over-time view: pick a hero, then an ability, then tune the
 * params; the chart, measures and notes follow (docs/dev/decisions.kb/vis-app.md,
 * "Client view").
 */
import { useEffect, useRef, useState } from "react";

import { abilities, heroes, timeline } from "./api";
import { hitChart } from "./chart";
import type { HitLine, MeasureLine, NoteLine, TimelineLine, TimelineParams } from "./protocol";

type Knob = Exclude<keyof TimelineParams, "hero" | "ability">;

/** The params form, in the order shown. Blank sends nothing: the server default applies. */
const KNOBS: readonly { knob: Knob; label: string; placeholder: string }[] = [
  { knob: "horizon", label: "horizon (s)", placeholder: "10" },
  { knob: "distance", label: "distance (m)", placeholder: "0" },
  { knob: "spirit", label: "spirit power", placeholder: "0" },
  { knob: "windup", label: "melee wind-up (s)", placeholder: "0" },
  { knob: "hp", label: "target hp", placeholder: "none" },
];

export function App() {
  const [hero, setHero] = useState("");
  const [ability, setAbility] = useState("");
  const [knobs, setKnobs] = useState<Partial<Record<Knob, string>>>({});

  const heroList = useLines(heroes, "heroes");
  const abilityList = useLines(hero === "" ? null : () => abilities(hero), hero);
  const params = { hero, ability, ...knobs };
  const lines = useLines(
    hero === "" || ability === "" ? null : () => timeline(params),
    JSON.stringify(params),
  );
  const { hits, measures, notes } = splitTimeline(lines.lines);

  return (
    <main>
      <h1>Damage over time</h1>
      <form onSubmit={(e) => e.preventDefault()}>
        <label>
          hero
          <select
            value={hero}
            onChange={(e) => {
              setHero(e.target.value);
              setAbility("");
            }}
          >
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
          <select value={ability} onChange={(e) => setAbility(e.target.value)}>
            <option value="">pick an ability</option>
            {abilityList.lines.map((a) => (
              <option key={a.ability} value={a.ability} disabled={a.kind === null}>
                {a.name} {a.kind === null ? "(no damage model)" : `(${a.kind})`}
              </option>
            ))}
          </select>
        </label>
        {KNOBS.map(({ knob, label, placeholder }) => (
          <label key={knob}>
            {label}
            <input
              inputMode="decimal"
              placeholder={placeholder}
              value={knobs[knob] ?? ""}
              onChange={(e) => {
                const { [knob]: _, ...rest } = knobs;
                const value = e.target.value.trim();
                setKnobs(value === "" ? rest : { ...rest, [knob]: value });
              }}
            />
          </label>
        ))}
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
      {hits.length > 0 && <Chart hits={hits} horizon={Number(knobs.horizon ?? 10)} />}
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

function Chart({ hits, horizon }: { hits: readonly HitLine[]; horizon: number }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (el === null) return;
    const width = el.clientWidth || 640;
    el.replaceChildren(hitChart(hits, Number.isFinite(horizon) ? { width, horizon } : { width }));
  }, [hits, horizon]);
  return <div ref={ref} />;
}

function Measures({ measures }: { measures: readonly MeasureLine[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>measure</th>
          <th>value</th>
          <th>unit</th>
          <th>check in-game</th>
        </tr>
      </thead>
      <tbody>
        {measures.map((m) => (
          <tr key={m.name}>
            <td>{m.name}</td>
            <td className="value">{m.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
            <td>{m.unit}</td>
            <td>{m.check}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function splitTimeline(lines: readonly TimelineLine[]) {
  const hits: HitLine[] = [];
  const measures: MeasureLine[] = [];
  const notes: NoteLine[] = [];
  for (const line of lines) {
    if (line.kind === "hit") hits.push(line);
    else if (line.kind === "measure") measures.push(line);
    else notes.push(line);
  }
  return { hits, measures, notes };
}

interface Loaded<T> {
  lines: readonly T[];
  error: string | null;
  loading: boolean;
}

/**
 * Run `load` whenever `key` changes and collect its lines; `null` clears them.
 * An answer that arrives after `key` has moved on is dropped.
 */
function useLines<T>(load: (() => AsyncIterable<T>) | null, key: string): Loaded<T> {
  const [state, setState] = useState<Loaded<T>>({ lines: [], error: null, loading: false });
  useEffect(() => {
    if (load === null) {
      setState({ lines: [], error: null, loading: false });
      return;
    }
    let stale = false;
    setState((s) => ({ ...s, loading: true }));
    void (async () => {
      const lines: T[] = [];
      try {
        for await (const line of load()) lines.push(line);
        if (!stale) setState({ lines, error: null, loading: false });
      } catch (e) {
        if (!stale) setState({ lines: [], error: String(e), loading: false });
      }
    })();
    return () => {
      stale = true;
    };
    // `key` stands for everything `load` closes over.
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  return state;
}
