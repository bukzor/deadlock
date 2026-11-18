---
status: proposed
date: "2026-11-18"
---

# `apps/vis`: a browser visualizer over `data/`, client and server talking JSONL

A general-purpose app for looking at the game data in a browser. The first view
answers "what damage does this hero's ability deal over time?", as a chart and
as DPS numbers a player can check in-game.

## Shape

- **`apps/vis/server/`**: Python, **its own uv workspace** (`[tool.uv.workspace]
  members = []`) on 3.14, basedpyright `all`. It is not a member of the root
  workspace because the root pins 3.12 for the extract tooling. It depends on the
  root `deadlock` package as an editable path dependency and reuses it rather
  than re-reading the data its own way. That includes
  `deadlock.ability_profiles.profiles`, which already derives gun DPS. Runtime
  dependencies are Starlette and uvicorn.
- **`apps/vis/client/`**: Vite + React + TypeScript (strict), a pnpm workspace
  whose root is `apps/vis/client/`. Charts use Observable Plot, tests use vitest.
  The user allowed Vue/Nuxt; React was kept because nothing here needs SSR or
  routing, and Plot is framework-agnostic.
- The dev server proxies `/api` to the Python server (port 8787). For a single
  process, the server can also serve `client/dist`.

## Protocol: JSONL that `jq` reads

- `GET /api/{query}?k=v…` answers `application/jsonl`: one compact JSON object
  per line, keys sorted (`deadlock.jsonl.dumps`).
- `vis-server query {query} k=v …` prints the same lines, so `vis-server query
  timeline hero=… | jq` works without a browser. `vis-server serve` runs HTTP.
- `GET /api` lists the queries, one line each: `{"query", "params": {name:
  description}}`.
- The server builds the whole response before sending it, so an error can
  still set the status. A `BadRequest` (unknown hero, unparseable number)
  becomes a 400 with one `{"error": message}` line. Anything else is a bug and
  fails loudly (500).

The query registry `queries.QUERIES` maps a name to a `Query`. A `Query`
carries its `params` as `{name: description}` and a `run(params: Params) ->
Sequence[JsonObj]`. The HTTP app and the CLI both read the registry and write
`run`'s lines unchanged, so they cannot drift apart.

Queries:

| query | params | lines |
|---|---|---|
| `heroes` | | `{"hero": key, "name": display}` |
| `abilities` | `hero` | `{"ability": key, "name", "kind": "gun"\|"melee"\|"cast"\|null}` |
| `timeline` | `hero`, `ability`, `horizon` (default: 2 periods of the cycle, at least 10 s), `distance`=0 (m), `spirit`=0, `windup`=0 (s), `hp` (optional) | lines tagged `kind`, below |

`timeline` lines:

- `{"kind": "hit", "trigger", "land", "damage", "label", "cycle"}`: one damage
  instance (`timeline.Hit`). `kind` is `hit` and nothing else.
- `{"kind": "measure", "name", "label", "value", "unit", "check"}`: `name` is a
  stable identifier for `jq`, and `label` is the player-facing wording. `check` says how to
  verify the value in-game.
- `{"kind": "note", "text"}`: a caveat on the model, such as "wind-up is not in
  the data", "charges not modeled" or "unverified heuristic".

Melee appears in `abilities` as two pseudo-abilities, `melee_light` and
`melee_heavy`, so no separate `attack` parameter is needed.

## Model: every damage source is a repeating `Cycle`

`server/src/vis_server/timeline.py` defines `Hit` and `Cycle`, and `repeat`
unrolls a cycle up to the horizon. Only hits that land within the horizon are
sent, so the chart draws exactly what the totals count. A hit's **trigger** is the input (trigger
pull, swing, cast) and its **land** is when the damage applies. The gap between
them is the wind-up, which is the bar's width in the chart.
- For a discrete hit, the trigger is the player's input.
- For a damage-over-time tick, the trigger is when that tick's damage starts
  building: the cast for the first tick, the previous tick for the rest. The
  bars tile the duration.

The first version triggered every tick at the cast. Its bars all overlapped
from t=0, and the user couldn't read the chart.

A `Cycle` carries its **downtime**: the seconds of each period spent dealing
no damage. For a gun that is the reload. For a cast it is the cooldown left
after the last tick lands. For melee it is 0.

Each source module exposes `cycle(heroes, abilities, hero, ability, …)`. The
trailing arguments are the parameters that source uses. It turns one hero's
ability into `(Cycle, notes)`, or returns `None` when the ability is not its
kind. Every timeline also gets a note that stats are level 0 with no items.

- **Gun** (`guns.py`): one clip fired at the gun's rate, then its reload. The
  formulas are in `docs/dev/mechanics.kb/gun-*.md`. Travel time is `distance /
  bullet speed`. Every live gun sets `m_flBulletSpeed`, in engine units (inches)
  per second. Six also carry a `m_BulletSpeedCurve`, and on five of those the
  two speeds disagree. Where a curve exists, the model uses it and notes the
  conflict as unverified; which speed the game actually uses can be checked
  in-game.
- **Melee** (`melee.py`): damage comes from hero
  `m_mapStartingStats.E{Light,Heavy}MeleeDamage`, and the period from
  `m_mapAttacks.EAttackType_{Light,Heavy}.m_flCooldownOnHit`. Wind-up is not
  in the data, so it is the `windup` parameter plus a note.
- **Cast** (`casts.py`): signature or ultimate abilities that have `Damage`
  and/or `DPS` properties. The impact lands at `AbilityCastDelay`. `DPS` ticks
  every `TickRate` across `AbilityDuration`, and the cycle repeats every
  `AbilityCooldown`. Spirit adds `m_flStatScale × spirit` for `ETechPower`
  scaling. Charges, upgrades and level scaling are not modeled; each of those
  gaps, and the heuristic as a whole, is stated in a note.

## Measures

`measures.py` computes the measures from a cycle and its unrolled hits:

- **`uptime_dps`**: damage per cycle ÷ (period − downtime), the DPS while the
  source is active. For a gun it equals the in-game UI's DPS. For a cast it is
  the damage over the ability's active time. Every source gets the same `check`
  wording, with no special case for guns.
- **`steady_dps`**: damage per cycle ÷ period. It equals the sustained DPS
  (`sdps`).
- Over the horizon: total damage, average DPS, and first land.
- **`time_to_kill`**, when `hp` is given: the land time of the hit that brings
  cumulative damage to `hp` or more. It can be checked against a training-dummy
  health bar.

## Client view

The view has a hero picker, then an ability picker, then only the parameters
that apply to the ability's `kind`. The selection lives in the URL, so a page
can be reloaded or shared.

The chart is titled "Damage timeline", because in Deadlock "damage over time"
means DoT.
- **Bars:** one per hit, a Plot `rect` from x1 = trigger to x2 = land, with
  height y = damage per hit (the user's spec). A caption per `kind` says what
  the width means: bullet travel, assumed wind-up, or time since the previous
  tick.
- **Cumulative damage:** a step line on a right-hand axis. Its slope is the DPS,
  and a dashed line at `hp` shows time-to-kill. This is the main read for
  comparing sources, because a bar's height is the size of one hit, not how
  much damage the source deals.
- **Hover:** the tooltip comes from the pointer anywhere on a bar, not only from
  the thin line at land.

Below the chart is the measures table: each measure's `label`, value and
`check`, with the DPS a player can compare to the card first. The notes list
follows, written for players and ordered by how much each caveat moves the
numbers.

## What would change this

- Real in-game measurements that disagree with a model. Those are recorded in
  `docs/dev/mechanics.kb/`, and the model is fixed to match.
- A second view that needs server push or interactive state. Then reconsider
  streaming or a websocket instead of request/response JSONL.
