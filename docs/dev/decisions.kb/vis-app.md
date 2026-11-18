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

Queries:

| query | params | lines |
|---|---|---|
| `heroes` | | `{"hero": key, "name": display}` |
| `abilities` | `hero` | `{"ability": key, "name", "kind": "gun"\|"melee"\|"cast"\|null}` |
| `timeline` | `hero`, `ability`, `horizon`=10, `distance`=0 (m), `spirit`=0, `windup`=0 (s), `hp` (optional) | lines tagged `kind`, below |

`timeline` lines:

- `{"kind": "hit", "trigger", "land", "damage", "label", "cycle"}`: one damage
  instance (`timeline.Hit`). `kind` is `hit` and nothing else.
- `{"kind": "measure", "name", "value", "unit", "check"}`: `check` says how to
  verify the value in-game.
- `{"kind": "note", "text"}`: a caveat on the model, such as "wind-up is not in
  the data", "charges not modeled" or "unverified heuristic".

Melee appears in `abilities` as two pseudo-abilities, `melee_light` and
`melee_heavy`, so no separate `attack` parameter is needed.

## Model: every damage source is a repeating `Cycle`

`server/src/vis_server/timeline.py` defines `Hit` and `Cycle`, and `repeat`
unrolls a cycle up to the horizon. A hit's **trigger** is the input (trigger
pull, swing, cast) and its **land** is when the damage applies. The gap between
them is the wind-up, which is the bar's width in the chart.

Each source module turns one hero's ability into `(Cycle, notes)`, or `None`
when the ability is not its kind:

- **Gun** (`guns.py`): one clip fired at the gun's rate, then its reload. The
  formulas are in `docs/dev/mechanics.kb/gun-*.md`. Travel time is `distance /
  bullet speed`; the speed is read from `m_BulletSpeedCurve` and is known for
  only a few guns, so the others get travel 0 and a note.
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

- **`uptime_dps`**: damage per cycle ÷ (period − reload). It equals the in-game
  UI's DPS for guns.
- **`steady_dps`**: damage per cycle ÷ period. It equals the sustained DPS
  (`sdps`).
- Over the horizon: total damage, average DPS, and first land.
- **`time_to_kill`**, when `hp` is given: the land time of the hit that brings
  cumulative damage to `hp` or more. It can be checked against a training-dummy
  health bar.

## Client view

The view has a hero picker, then an ability picker, then a params form. The
chart has one bar per hit, drawn as a Plot `rect` from x1 = trigger to x2 =
land, with height y = damage. A `ruleX` at land keeps zero-width hits visible.
Below the chart are a measures table that shows each `check` and the notes
list.

## What would change this

- Real in-game measurements that disagree with a model. Those are recorded in
  `docs/dev/mechanics.kb/`, and the model is fixed to match.
- A second view that needs server push or interactive state. Then reconsider
  streaming or a websocket instead of request/response JSONL.
