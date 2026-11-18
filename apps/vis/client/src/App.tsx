/**
 * The damage timeline view: pick a hero, then an ability, then tune the params
 * that ability's kind reads; the chart, measures and notes follow. The
 * selection lives in the URL (docs/dev/decisions.kb/vis-app.md, "Client view").
 */
import { useEffect, useRef, useState } from "react";

import { abilities, heroes, timeline } from "./api";
import { hitChart } from "./chart";
import type { AbilityKind, CycleLine, HitLine, MeasureLine, NoteLine, TimelineLine } from "./protocol";
import { fromSearch, knobsFor, timelineParams, toSearch, type Knob, type Selection } from "./selection";
import { unreachableKillNote, windowFields, windowFromText, zoomToKill, type Window, type WindowField, type WindowUnit } from "./window";

/** Each knob's label, and its placeholder: the server's default, never a value. */
const KNOB_TEXT: Record<Knob, { label: string; placeholder: string }> = {
  level: { label: "hero level", placeholder: "default 0" },
  distance: { label: "distance (m)", placeholder: "default 0" },
  spirit: { label: "spirit power", placeholder: "default 0" },
  windup: { label: "wind-up (s)", placeholder: "default 0" },
};

const WINDOW_LABEL: Record<WindowUnit, string> = { seconds: "window (s)", cycles: "cycles shown" };

export function App() {
  const [initial] = useState(() => fromSearch(location.search));
  const [sel, setSel] = useState<Selection>(initial.sel);
  const [timeWindow, setTimeWindow] = useState<Window | null>(initial.window);
  const [hp, setHp] = useState(initial.hp);
  // Set by a change that may move the kill (hp, hero, ability, level), and
  // cleared by a window edit: the next answer may zoom the window out to it.
  const [zoomPending, setZoomPending] = useState(false);
  useEffect(() => {
    history.replaceState(null, "", toSearch({ sel, window: timeWindow, hp }) || location.pathname);
  }, [sel, timeWindow, hp]);

  const heroList = useLines(heroes, "heroes");
  const abilityList = useLines(sel.hero === "" ? null : () => abilities(sel.hero), sel.hero);
  // `undefined` until the abilities arrive: the knobs to send depend on it.
  const kind: AbilityKind | null | undefined = abilityList.loading
    ? undefined
    : abilityList.lines.find((a) => a.ability === sel.ability)?.kind;
  const params = kind === undefined ? null : timelineParams({ sel, window: timeWindow, hp }, kind);
  const key = JSON.stringify(params);
  const lines = useLines(params === null || sel.hero === "" || sel.ability === "" ? null : () => timeline(params), key);
  const { cycle, hits, measures, notes } = splitTimeline(lines.lines);
  // By name: the server orders and adds measures as it likes.
  const killTime = measures.find((m) => m.name === "time_to_kill")?.value;
  const answered = !lines.loading && lines.key === key;
  useEffect(() => {
    if (!zoomPending || !answered || cycle === undefined) return;
    setZoomPending(false);
    const zoomed = zoomToKill(cycle, killTime);
    if (zoomed !== null) setTimeWindow(zoomed);
  }, [zoomPending, answered, cycle, killTime]);
  const fields = windowFields(timeWindow, cycle);
  const reachNote = cycle === undefined ? null : unreachableKillNote(cycle, killTime);
  const hpValue = Number(params?.hp);

  return (
    <main>
      <h1>Damage timeline</h1>
      <form onSubmit={(e) => e.preventDefault()}>
        <label>
          hero
          <select
            value={sel.hero}
            onChange={(e) => {
              setSel({ ...sel, hero: e.target.value, ability: "" });
              setZoomPending(true);
            }}
          >
            <option value="">pick a hero</option>
            {heroList.lines.map((h) => (
              <option key={h.hero} value={h.hero} title={h.hero}>
                {h.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          ability
          <select
            value={sel.ability}
            onChange={(e) => {
              setSel({ ...sel, ability: e.target.value });
              setZoomPending(true);
            }}
          >
            <option value="">pick an ability</option>
            {abilityList.lines.map((a) => (
              <option key={a.ability} value={a.ability} title={a.ability} disabled={a.kind === null}>
                {a.name} {a.kind === null ? "(no damage model)" : `(${a.kind})`}
              </option>
            ))}
          </select>
        </label>
        {kind != null && (
          <>
            {(["seconds", "cycles"] as const).map((by) => (
              <DraftInput
                key={by}
                label={WINDOW_LABEL[by]}
                field={fields[by]}
                onEdit={(text) => {
                  setTimeWindow(windowFromText(by, text));
                  setZoomPending(false);
                }}
              />
            ))}
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
                    if (knob === "level") setZoomPending(true);
                  }}
                />
              </label>
            ))}
            <label>
              target hp
              <input
                inputMode="decimal"
                placeholder="optional"
                value={hp}
                onChange={(e) => {
                  setHp(e.target.value);
                  setZoomPending(true);
                }}
              />
            </label>
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
        <Chart
          hits={hits}
          kind={kind}
          horizon={cycle?.horizon ?? 10}
          {...(Number.isFinite(hpValue) ? { hp: hpValue } : {})}
          {...(killTime === undefined ? {} : { killTime })}
        />
      )}
      {hits.length === 0 && measures.length > 0 && (
        <p className="chart">No damage lands within the window: the notes say what the model leaves out.</p>
      )}
      {measures.length > 0 && <Measures measures={measures} />}
      {(notes.length > 0 || reachNote !== null) && (
        <ul>
          {reachNote !== null && <li>{reachNote}</li>}
          {notes.map((n, i) => (
            <li key={i}>{n.text}</li>
          ))}
        </ul>
      )}
    </main>
  );
}

/**
 * An input showing `field`, except while focused: then it keeps the user's
 * own text, so an answer arriving mid-typing never moves the cursor.
 */
function DraftInput(props: { label: string; field: WindowField; onEdit: (text: string) => void }) {
  const { label, field, onEdit } = props;
  const [draft, setDraft] = useState<string | null>(null);
  return (
    <label>
      {label}
      <input
        inputMode="decimal"
        placeholder={field.placeholder}
        disabled={field.disabled}
        value={draft ?? field.value}
        onFocus={() => setDraft(field.value)}
        onChange={(e) => {
          setDraft(e.target.value);
          onEdit(e.target.value);
        }}
        onBlur={() => setDraft(null)}
      />
    </label>
  );
}

function Chart(props: { hits: readonly HitLine[]; kind: AbilityKind; horizon: number; hp?: number; killTime?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const { hits, kind, horizon, hp, killTime } = props;
  // Redrawn from `hits` at the container's own width whenever that changes, and
  // when the color scheme flips: a scaled SVG shrinks its text with it.
  //
  // A redraw changes the container's height. Drawn inside the observer's
  // callback, that is a new notification mid-delivery ("ResizeObserver loop
  // completed with undelivered notifications"), so the observer only schedules
  // a draw for the next frame, and only when the whole-pixel width changed.
  useEffect(() => {
    const el = ref.current;
    if (el === null) return;
    const scheme = matchMedia("(prefers-color-scheme: dark)");
    const draw = () => {
      const width = el.clientWidth || 640;
      const extra = { ...(hp === undefined ? {} : { hp }), ...(killTime === undefined ? {} : { killTime }) };
      el.replaceChildren(hitChart(hits, { width, kind, horizon, dark: scheme.matches, ...extra }));
    };
    let last = -1;
    let frame = 0;
    const observer = new ResizeObserver(([entry]) => {
      const width = Math.round(entry!.contentRect.width);
      if (width === last) return;
      last = width;
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(draw);
    });
    observer.observe(el);
    scheme.addEventListener("change", draw);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      scheme.removeEventListener("change", draw);
    };
  }, [hits, kind, horizon, hp, killTime]);
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
